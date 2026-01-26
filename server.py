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
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / 'input'
            output_dir = temp_path / 'output'

            input_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)

            images_dir = input_dir / 'images'
            videos_dir = input_dir / 'videos'
            images_dir.mkdir(parents=True)
            videos_dir.mkdir(parents=True)

            # Generator function for streaming logs
            def generate():
                try:
                    # Save uploaded files
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Saving uploaded files...'})}\n\n"

                    # Save transcript
                    transcript_file = request.files.get('transcript')
                    if transcript_file:
                        transcript_path = input_dir / 'transcript.txt'
                        transcript_file.save(str(transcript_path))
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ Saved transcript'})}\n\n"

                    # Save audio
                    audio_file = request.files.get('audio')
                    if audio_file:
                        audio_path = input_dir / 'audio.mp3'
                        audio_file.save(str(audio_path))
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ Saved audio file'})}\n\n"

                    # Save images
                    image_files = request.files.getlist('images')
                    for i, img_file in enumerate(image_files):
                        img_path = images_dir / img_file.filename
                        img_file.save(str(img_path))
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved {len(image_files)} images'})}\n\n"

                    # Build scene configuration from scene videos
                    scene_config = {'scenes': {}}
                    scene_video_count = 0

                    # Get all scene video files (they have field names like 'scene_video_1', 'scene_video_2', etc.)
                    for field_name in request.files:
                        if field_name.startswith('scene_video_'):
                            scene_number = field_name.replace('scene_video_', '')
                            video_file = request.files[field_name]

                            if video_file and video_file.filename:
                                # Save video file
                                video_path = videos_dir / video_file.filename
                                video_file.save(str(video_path))

                                # Add to scene config
                                scene_config['scenes'][scene_number] = {
                                    'type': 'video',
                                    'path': f'input/videos/{video_file.filename}'
                                }
                                scene_video_count += 1

                    if scene_video_count > 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Saved {scene_video_count} scene video(s)'})}\n\n"

                        # Save scene config
                        config_path = input_dir / 'scene_config.json'
                        with open(config_path, 'w') as f:
                            json.dump(scene_config, f, indent=2)
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ Created scene configuration'})}\n\n"

                    yield f"data: {json.dumps({'type': 'progress', 'percentage': 10, 'message': 'Files uploaded, starting video generation...'})}\n\n"

                    # Read the create_video.py script and modify it for our temp directory
                    script_path = PROJECT_ROOT / 'scripts' / 'create_video.py'
                    with open(script_path, 'r') as f:
                        script_content = f.read()

                    # Replace PROJECT_ROOT definition
                    modified_script = script_content.replace(
                        'PROJECT_ROOT = SCRIPT_DIR.parent',
                        f'PROJECT_ROOT = Path("{temp_path}")'
                    )

                    # Write modified script to temp directory
                    temp_script = temp_path / 'create_video_temp.py'
                    with open(temp_script, 'w') as f:
                        f.write(modified_script)

                    # Run the modified script
                    process = subprocess.Popen(
                        ['python3', str(temp_script)],
                        cwd=str(temp_path),
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

                    # Copy the output video to a permanent location
                    output_video = output_dir / 'final_video.mp4'
                    if output_video.exists():
                        # Save to project output directory with timestamp
                        project_output_dir = PROJECT_ROOT / 'output'
                        project_output_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = int(time.time())
                        final_video_name = f'video_{timestamp}.mp4'
                        final_video_path = project_output_dir / final_video_name

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

if __name__ == '__main__':
    print("=" * 80)
    print("VIDEO MAKER - Web Server")
    print("=" * 80)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
