#!/usr/bin/env python3
"""
Flask server for Video Maker web interface
Handles file uploads and video generation
"""
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from pathlib import Path
import json
import subprocess
import tempfile
import shutil
import os
import time
import math

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

# Get project root
PROJECT_ROOT = Path(__file__).parent

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file(PROJECT_ROOT / 'webapp' / 'index.html')

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Handle video generation request"""
    try:
        # Extract files from request BEFORE entering the generator
        # This avoids "Working outside of request context" error
        transcript_file = request.files.get('transcript')
        audio_file = request.files.get('audio')
        image_files = request.files.getlist('images')
        
        # Get scene video files
        scene_videos = {}
        for field_name in request.files:
            if field_name.startswith('scene_video_'):
                scene_number = field_name.replace('scene_video_', '')
                video_file = request.files[field_name]
                if video_file and video_file.filename:
                    scene_videos[scene_number] = video_file
        
        # Use project directories
        input_dir = PROJECT_ROOT / 'input'
        output_dir = PROJECT_ROOT / 'output'
        
        # Clear and recreate directories
        if input_dir.exists():
            shutil.rmtree(input_dir)
        input_dir.mkdir(parents=True, exist_ok=True)
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images_dir = input_dir / 'images'
        videos_dir = input_dir / 'videos'
        images_dir.mkdir(parents=True, exist_ok=True)
        videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files immediately (while in request context)
        file_info = {'transcript': None, 'audio': None, 'image_count': 0, 'video_count': 0}
        
        # Save transcript
        if transcript_file:
            transcript_path = input_dir / 'transcript.txt'
            transcript_file.save(str(transcript_path))
            file_info['transcript'] = transcript_file.filename
        
        # Save audio
        if audio_file:
            audio_path = input_dir / 'audio.mp3'
            audio_file.save(str(audio_path))
            file_info['audio'] = audio_file.filename
        
        # Save images
        for i, img_file in enumerate(image_files):
            img_path = images_dir / img_file.filename
            img_file.save(str(img_path))
            file_info['image_count'] += 1
        
        # Save scene videos and create config
        scene_config = {'scenes': {}}
        for scene_number, video_file in scene_videos.items():
            video_path = videos_dir / video_file.filename
            video_file.save(str(video_path))
            
            scene_config['scenes'][scene_number] = {
                'type': 'video',
                'path': f'input/videos/{video_file.filename}'
            }
            file_info['video_count'] += 1
        
        # Save scene config if videos were uploaded
        if file_info['video_count'] > 0:
            config_path = input_dir / 'scene_config.json'
            with open(config_path, 'w') as f:
                json.dump(scene_config, f, indent=2)
        
        # Generator function for streaming logs
        def generate():
            try:
                yield f"data: {json.dumps({'type': 'log', 'message': 'Files saved successfully'})}\n\n"
                
                # Extract values to avoid backslash in f-string
                transcript_name = file_info['transcript']
                audio_name = file_info['audio']
                image_count = file_info['image_count']
                video_count = file_info['video_count']
                
                yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved transcript: {transcript_name}'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved audio: {audio_name}'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved {image_count} images'})}\n\n"
                
                if video_count > 0:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved {video_count} scene video(s)'})}\n\n"
                    yield f"data: {json.dumps({'type': 'log', 'message': '✓ Created scene configuration'})}\n\n"
                
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 10, 'message': 'Files uploaded, starting video generation...'})}\n\n"
                
                # Run the video creation script
                script_path = PROJECT_ROOT / 'scripts' / 'create_video.py'
                
                process = subprocess.Popen(
                    ['python3', str(script_path)],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**os.environ, 'PYTHONUNBUFFERED': '1'}
                )
                
                # Stream the output
                progress_map = {
                    'Step 1': 15,
                    'Step 2': 20,
                    'Step 3': 25,
                    'Step 4': 40,
                    'Step 5': 55,
                    'Step 6': 65,
                    'Step 7': 70,
                    'Step 8': 75,
                    'Step 9': 80
                }
                
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        # Determine progress percentage
                        percentage = 80
                        for step, pct in progress_map.items():
                            if step in line:
                                percentage = pct
                                break
                        
                        yield f"data: {json.dumps({'type': 'log', 'message': line})}\n\n"
                        
                        if any(step in line for step in progress_map.keys()):
                            yield f"data: {json.dumps({'type': 'progress', 'percentage': percentage, 'message': line})}\n\n"
                
                process.wait()
                
                if process.returncode != 0:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Video generation failed'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 95, 'message': 'Video created, preparing download...'})}\n\n"
                
                # Check if output file exists
                output_video = output_dir / 'final_video.mp4'
                if output_video.exists():
                    timestamp = int(time.time())
                    final_video_name = f'video_{timestamp}.mp4'
                    final_video_path = output_dir / final_video_name
                    
                    shutil.copy(output_video, final_video_path)
                    
                    yield f"data: {json.dumps({'type': 'complete', 'message': 'Video generated successfully!', 'videoUrl': f'/api/download/{final_video_name}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Output video not found'})}\n\n"
                
            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_video(filename):
    """Download the generated video"""
    video_path = PROJECT_ROOT / 'output' / filename
    if video_path.exists():
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name='generated_video.mp4'
        )
    return jsonify({'error': 'Video not found'}), 404


@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    """Clear all input and output files from the server"""
    try:
        input_dir = PROJECT_ROOT / 'input'
        output_dir = PROJECT_ROOT / 'output'

        deleted_count = 0
        errors = []

        # Clear input directory
        if input_dir.exists():
            for item in input_dir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"Failed to delete {item.name}: {str(e)}")

        # Clear output directory
        if output_dir.exists():
            for item in output_dir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"Failed to delete {item.name}: {str(e)}")

        if errors:
            return jsonify({
                'message': f'Cleared {deleted_count} items with some errors',
                'errors': errors
            }), 207  # Multi-Status
        else:
            return jsonify({
                'message': f'Successfully cleared {deleted_count} items from input and output directories'
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regional-mix', methods=['POST'])
def regional_mix():
    """Handle Regional Mix video generation request with images and videos"""
    try:
        # Extract pair info (includes media type)
        pair_info_json = request.form.get('pair_info', '[]')
        pair_info = json.loads(pair_info_json)

        # Get no_transitions setting
        no_transitions = request.form.get('no_transitions', 'false') == 'true'

        # Extract media and audio files
        media_files = {}
        media_types = {}
        audio_files = {}

        for field_name in request.files:
            file = request.files[field_name]
            if field_name.startswith('media_'):
                num = int(field_name.replace('media_', ''))
                media_files[num] = file
            elif field_name.startswith('audio_'):
                num = int(field_name.replace('audio_', ''))
                audio_files[num] = file

        # Get media types from form data
        for field_name in request.form:
            if field_name.startswith('mediatype_'):
                num = int(field_name.replace('mediatype_', ''))
                media_types[num] = request.form[field_name]

        # Use project directories
        input_dir = PROJECT_ROOT / 'input'
        output_dir = PROJECT_ROOT / 'output'

        # Clear and recreate directories
        rm_input_dir = input_dir / 'regional_mix'
        if rm_input_dir.exists():
            shutil.rmtree(rm_input_dir)
        rm_input_dir.mkdir(parents=True, exist_ok=True)

        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        media_dir = rm_input_dir / 'media'
        audio_dir = rm_input_dir / 'audio'
        media_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Save files and track paths
        saved_pairs = []

        for info in pair_info:
            num = info['number']
            media_type = info['mediaType']

            if num in media_files and num in audio_files:
                media_file = media_files[num]
                aud_file = audio_files[num]

                # Get file extensions
                media_ext = Path(media_file.filename).suffix
                aud_ext = Path(aud_file.filename).suffix

                media_path = media_dir / f'{num}{media_ext}'
                aud_path = audio_dir / f'{num}{aud_ext}'

                media_file.save(str(media_path))
                aud_file.save(str(aud_path))

                saved_pairs.append({
                    'number': num,
                    'media': str(media_path),
                    'mediaType': media_type,
                    'audio': str(aud_path)
                })

        # Save pairs config
        config_path = rm_input_dir / 'pairs_config.json'
        with open(config_path, 'w') as f:
            json.dump(saved_pairs, f, indent=2)

        # Generator function for streaming logs
        def generate():
            try:
                yield f"data: {json.dumps({'type': 'log', 'message': 'Files saved successfully'})}\n\n"

                pair_count = len(saved_pairs)
                image_count = sum(1 for p in saved_pairs if p['mediaType'] == 'image')
                video_count = sum(1 for p in saved_pairs if p['mediaType'] == 'video')

                yield f"data: {json.dumps({'type': 'log', 'message': f'Processing {pair_count} pairs ({image_count} images, {video_count} videos)'})}\n\n"
                if no_transitions:
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Transitions disabled - direct cut between clips'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 15, 'message': 'Creating video clips...'})}\n\n"

                # Create individual video clips for each pair
                temp_clips = []
                clip_dir = rm_input_dir / 'clips'
                clip_dir.mkdir(parents=True, exist_ok=True)

                for i, pair in enumerate(saved_pairs):
                    num = pair['number']
                    media_path = pair['media']
                    media_type = pair['mediaType']
                    aud_path = pair['audio']

                    progress = 15 + int((i / pair_count) * 50)
                    yield f"data: {json.dumps({'type': 'progress', 'percentage': progress, 'message': f'Processing pair {num}...'})}\n\n"

                    type_label = 'video' if media_type == 'video' else 'image'
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Creating clip for pair {num} ({type_label})...'})}\n\n"

                    # Get audio duration using ffprobe
                    duration_cmd = [
                        'ffprobe', '-v', 'error', '-show_entries',
                        'format=duration', '-of',
                        'default=noprint_wrappers=1:nokey=1', aud_path
                    ]
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                    audio_duration = float(duration_result.stdout.strip())

                    yield f"data: {json.dumps({'type': 'log', 'message': f'  Audio duration: {audio_duration:.2f}s'})}\n\n"

                    # Create video clip
                    clip_path = str(clip_dir / f'clip_{num}.mp4')

                    # Calculate fade duration (max 0.5s or 10% of duration) - only used if transitions enabled
                    fade_duration = 0 if no_transitions else min(0.5, audio_duration * 0.1)

                    if media_type == 'video':
                        # For video: mute original audio, trim to audio duration, add new audio
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  Processing video (muting original audio, trimming to {audio_duration:.2f}s)...'})}\n\n"

                        # Get video duration
                        vid_duration_cmd = [
                            'ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of',
                            'default=noprint_wrappers=1:nokey=1', media_path
                        ]
                        vid_duration_result = subprocess.run(vid_duration_cmd, capture_output=True, text=True)
                        video_duration = float(vid_duration_result.stdout.strip())

                        yield f"data: {json.dumps({'type': 'log', 'message': f'  Original video duration: {video_duration:.2f}s'})}\n\n"

                        # Build FFmpeg command for video
                        # -an removes audio from video, -t trims to audio duration
                        # If video is shorter than audio, freeze the last frame
                        if video_duration >= audio_duration:
                            # Video is longer or equal - just trim
                            # Build video filter - with or without fade
                            # IMPORTANT: Add fps=30 to match image clips for proper concat
                            vf_base = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30'
                            if no_transitions:
                                vf_filter = vf_base
                            else:
                                vf_filter = f'{vf_base},fade=t=in:st=0:d={fade_duration},fade=t=out:st={audio_duration-fade_duration}:d={fade_duration}'

                            ffmpeg_cmd = [
                                'ffmpeg', '-y',
                                '-i', media_path,
                                '-i', aud_path,
                                '-map', '0:v',  # Take video from first input
                                '-map', '1:a',  # Take audio from second input
                                '-c:v', 'libx264',
                                '-preset', 'medium',
                                '-crf', '18',
                                '-c:a', 'aac',
                                '-b:a', '192k',
                                '-pix_fmt', 'yuv420p',
                                '-vf', vf_filter,
                                '-t', str(audio_duration),
                                clip_path
                            ]
                        else:
                            # Video is shorter - use tpad to freeze last frame (simple & reliable)
                            freeze_duration = audio_duration - video_duration
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  Video shorter than audio, freezing last frame for {freeze_duration:.2f}s...'})}\n\n"

                            # Use tpad filter to extend video by freezing the last frame
                            # This is much simpler and more reliable than zoompan
                            # IMPORTANT: Add fps=30 to match image clips for proper concat
                            vf_base = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30'

                            if no_transitions:
                                # Simple: scale, pad, freeze last frame
                                vf_filter = f'{vf_base},tpad=stop_mode=clone:stop_duration={freeze_duration}'
                            else:
                                # With fade effects
                                vf_filter = f'{vf_base},tpad=stop_mode=clone:stop_duration={freeze_duration},fade=t=in:st=0:d={fade_duration},fade=t=out:st={audio_duration-fade_duration}:d={fade_duration}'

                            ffmpeg_cmd = [
                                'ffmpeg', '-y',
                                '-i', media_path,
                                '-i', aud_path,
                                '-map', '0:v',
                                '-map', '1:a',
                                '-c:v', 'libx264',
                                '-preset', 'medium',
                                '-crf', '18',
                                '-c:a', 'aac',
                                '-b:a', '192k',
                                '-pix_fmt', 'yuv420p',
                                '-vf', vf_filter,
                                '-t', str(audio_duration),
                                clip_path
                            ]
                    else:
                        # For image: create video with exact duration matching audio
                        fps = 30

                        yield f"data: {json.dumps({'type': 'log', 'message': f'  Creating image clip at {fps}fps for {audio_duration:.3f}s'})}\n\n"

                        # Simple static image - scale to 1920x1080 with padding
                        vf_base = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30'

                        # Build video filter - with or without fade
                        if no_transitions:
                            vf_filter = vf_base
                        else:
                            vf_filter = f'{vf_base},fade=t=in:st=0:d={fade_duration},fade=t=out:st={audio_duration-fade_duration}:d={fade_duration}'

                        # Use -loop 1 to loop the image, -t for duration
                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-loop', '1',
                            '-i', media_path,
                            '-i', aud_path,
                            '-map', '0:v',
                            '-map', '1:a',
                            '-c:v', 'libx264',
                            '-preset', 'medium',
                            '-crf', '18',
                            '-c:a', 'aac',
                            '-b:a', '192k',
                            '-pix_fmt', 'yuv420p',
                            '-vf', vf_filter,
                            '-t', str(audio_duration),
                            '-shortest',
                            clip_path
                        ]

                    process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

                    if process.returncode != 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  FFmpeg error: {process.stderr}', 'level': 'error'})}\n\n"
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to create clip for pair {num}'})}\n\n"
                        return

                    # Verify clip was created and get its duration
                    if os.path.exists(clip_path):
                        clip_duration_cmd = [
                            'ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of',
                            'default=noprint_wrappers=1:nokey=1', clip_path
                        ]
                        clip_dur_result = subprocess.run(clip_duration_cmd, capture_output=True, text=True)
                        try:
                            actual_clip_duration = float(clip_dur_result.stdout.strip())
                            duration_diff = abs(actual_clip_duration - audio_duration)

                            # Check if duration matches within tolerance (0.05 seconds = 50ms)
                            if duration_diff > 0.05:
                                yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Clip duration mismatch: {actual_clip_duration:.3f}s vs expected {audio_duration:.3f}s (diff: {duration_diff:.3f}s)', 'level': 'warning'})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'log', 'message': f'  ✓ Clip created: {actual_clip_duration:.3f}s (expected {audio_duration:.3f}s)'})}\n\n"
                            temp_clips.append(clip_path)
                        except ValueError:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Warning: Could not read clip duration', 'level': 'warning'})}\n\n"
                            temp_clips.append(clip_path)
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  ❌ ERROR: Clip file not found at {clip_path}', 'level': 'error'})}\n\n"

                yield f"data: {json.dumps({'type': 'progress', 'percentage': 70, 'message': 'Concatenating clips...'})}\n\n"

                # Calculate expected total duration from all audio files
                total_expected_duration = 0
                for pair in saved_pairs:
                    aud_path = pair['audio']
                    dur_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', aud_path]
                    dur_result = subprocess.run(dur_cmd, capture_output=True, text=True)
                    try:
                        total_expected_duration += float(dur_result.stdout.strip())
                    except ValueError:
                        pass

                yield f"data: {json.dumps({'type': 'log', 'message': f'Expected total duration: {total_expected_duration:.3f}s'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': f'Concatenating {len(temp_clips)} clips into final video...'})}\n\n"

                # Validate all clips exist before concatenation
                valid_clips = []
                for clip_path in temp_clips:
                    if os.path.exists(clip_path) and os.path.getsize(clip_path) > 0:
                        valid_clips.append(clip_path)
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Skipping invalid/empty clip: {clip_path}', 'level': 'warning'})}\n\n"

                if len(valid_clips) != len(temp_clips):
                    yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Only {len(valid_clips)} of {len(temp_clips)} clips are valid', 'level': 'warning'})}\n\n"

                yield f"data: {json.dumps({'type': 'log', 'message': f'  Valid clips to concatenate: {len(valid_clips)}'})}\n\n"

                # Create concat file
                concat_file = rm_input_dir / 'concat.txt'
                with open(concat_file, 'w') as f:
                    for clip_path in valid_clips:
                        f.write(f"file '{clip_path}'\n")

                # Log what we're concatenating
                for i, clip_path in enumerate(valid_clips):
                    clip_name = os.path.basename(clip_path)
                    yield f"data: {json.dumps({'type': 'log', 'message': f'  [{i+1}/{len(valid_clips)}] {clip_name}'})}\n\n"

                # Concatenate all clips using stream copy (preserves exact durations)
                # All clips now have identical params: fps=30, 1920x1080, libx264, yuv420p
                final_video = output_dir / 'final_video.mp4'
                concat_cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(concat_file),
                    '-c', 'copy',  # Stream copy preserves exact timing
                    str(final_video)
                ]

                process = subprocess.run(concat_cmd, capture_output=True, text=True)

                if process.returncode != 0:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Concat error: {process.stderr}', 'level': 'error'})}\n\n"
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to concatenate video clips'})}\n\n"
                    return

                yield f"data: {json.dumps({'type': 'progress', 'percentage': 95, 'message': 'Finalizing video...'})}\n\n"

                # Log final video duration and compare against expected
                if final_video.exists():
                    final_dur_cmd = [
                        'ffprobe', '-v', 'error', '-show_entries',
                        'format=duration', '-of',
                        'default=noprint_wrappers=1:nokey=1', str(final_video)
                    ]
                    final_dur_result = subprocess.run(final_dur_cmd, capture_output=True, text=True)
                    try:
                        final_duration = float(final_dur_result.stdout.strip())
                        duration_drift = final_duration - total_expected_duration
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Final video duration: {final_duration:.3f}s (expected: {total_expected_duration:.3f}s)'})}\n\n"
                        if abs(duration_drift) > 0.1:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'⚠ Duration drift detected: {duration_drift:+.3f}s', 'level': 'warning'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Duration sync OK (drift: {duration_drift:+.3f}s)'})}\n\n"
                    except ValueError:
                        pass

                # Check if output file exists
                if final_video.exists():
                    timestamp = int(time.time())
                    final_video_name = f'regional_mix_{timestamp}.mp4'
                    final_video_path = output_dir / final_video_name

                    shutil.copy(final_video, final_video_path)

                    yield f"data: {json.dumps({'type': 'log', 'message': 'Video created successfully!'})}\n\n"
                    yield f"data: {json.dumps({'type': 'complete', 'message': 'Regional Mix video generated successfully!', 'videoUrl': f'/api/download/{final_video_name}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Output video not found'})}\n\n"

            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("VIDEO MAKER - Web Server")
    print("=" * 80)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:8080")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8080)
