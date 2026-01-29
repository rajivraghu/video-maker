#!/usr/bin/env python3
"""
Flask server for Video Maker Web Application
Handles file uploads and video generation
"""
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path
from werkzeug.utils import secure_filename
import threading
import queue

# Setup paths
WEBAPP_DIR = Path(__file__).parent
PROJECT_ROOT = WEBAPP_DIR.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CREATE_VIDEO_SCRIPT = SCRIPTS_DIR / "create_video.py"

# Create Flask app
app = Flask(__name__, static_folder='.')
CORS(app)

# Configuration
ALLOWED_EXTENSIONS = {
    'transcript': {'txt'},
    'audio': {'mp3', 'wav', 'm4a'},
    'images': {'png', 'jpg', 'jpeg'},
    'videos': {'mp4', 'mov', 'avi', 'webm'},
    'transition_sound': {'mp3', 'wav'}
}

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]

def clear_input_directory():
    """Clear the input directory"""
    if INPUT_DIR.exists():
        shutil.rmtree(INPUT_DIR)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    (INPUT_DIR / "images").mkdir(exist_ok=True)
    (INPUT_DIR / "videos").mkdir(exist_ok=True)

def clear_output_directory():
    """Clear the output directory"""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def send_sse_message(msg_type, **kwargs):
    """Format Server-Sent Events message"""
    data = {'type': msg_type, **kwargs}
    return f"data: {json.dumps(data)}\n\n"

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Handle video generation request"""
    # Extract files from request BEFORE entering the generator
    # This avoids "Working outside of request context" error
    try:
        # Validate files exist in request
        if 'transcript' not in request.files:
            return Response(
                send_sse_message('error', message='No transcript file provided'),
                mimetype='text/event-stream'
            )
        
        if 'audio' not in request.files:
            return Response(
                send_sse_message('error', message='No audio file provided'),
                mimetype='text/event-stream'
            )
        
        if 'images' not in request.files:
            return Response(
                send_sse_message('error', message='No images provided'),
                mimetype='text/event-stream'
            )
        
        # Get files from request
        transcript_file = request.files['transcript']
        audio_file = request.files['audio']
        image_files = request.files.getlist('images')
        
        # Store file info (we'll save them in the generator)
        transcript_filename = transcript_file.filename
        audio_filename = audio_file.filename
        image_count = len(image_files)
        
        # Validate filenames
        if transcript_filename == '':
            return Response(
                send_sse_message('error', message='No transcript file selected'),
                mimetype='text/event-stream'
            )
        
        if audio_filename == '':
            return Response(
                send_sse_message('error', message='No audio file selected'),
                mimetype='text/event-stream'
            )
        
        if not image_files or all(f.filename == '' for f in image_files):
            return Response(
                send_sse_message('error', message='No images selected'),
                mimetype='text/event-stream'
            )
        
        # Validate file types
        if not allowed_file(transcript_filename, 'transcript'):
            return Response(
                send_sse_message('error', message='Invalid transcript file type. Only .txt allowed'),
                mimetype='text/event-stream'
            )
        
        if not allowed_file(audio_filename, 'audio'):
            return Response(
                send_sse_message('error', message='Invalid audio file type. Only .mp3, .wav, .m4a allowed'),
                mimetype='text/event-stream'
            )
        
        for img in image_files:
            if not allowed_file(img.filename, 'images'):
                return Response(
                    send_sse_message('error', message=f'Invalid image file type: {img.filename}'),
                    mimetype='text/event-stream'
                )
        
        # Save files immediately (while still in request context)
        # Clear both input and output directories before starting
        clear_input_directory()
        clear_output_directory()
        
        # Save transcript
        transcript_path = INPUT_DIR / "transcript.txt"
        transcript_file.save(str(transcript_path))
        
        # Save audio
        audio_path = INPUT_DIR / "audio.mp3"
        audio_file.save(str(audio_path))
        
        # Save images with proper numbering
        images_dir = INPUT_DIR / "images"
        for idx, img_file in enumerate(image_files, start=1):
            ext = img_file.filename.rsplit('.', 1)[1].lower()
            img_path = images_dir / f"{idx}.{ext}"
            img_file.save(str(img_path))

        # Handle scene videos and create scene configuration
        videos_dir = INPUT_DIR / "videos"
        videos_dir.mkdir(exist_ok=True)
        scene_config = {'scenes': {}}
        video_count = 0

        # Check for scene video uploads (format: scene_video_1, scene_video_2, etc.)
        for field_name in request.files:
            if field_name.startswith('scene_video_'):
                scene_number = field_name.replace('scene_video_', '')
                video_file = request.files[field_name]

                if video_file and video_file.filename != '':
                    # Validate video file type
                    if not allowed_file(video_file.filename, 'videos'):
                        continue  # Skip invalid video files

                    # Save video file
                    video_filename = secure_filename(video_file.filename)
                    video_path = videos_dir / video_filename
                    video_file.save(str(video_path))

                    # Add to scene configuration
                    scene_config['scenes'][scene_number] = {
                        'type': 'video',
                        'path': f'input/videos/{video_filename}'
                    }
                    video_count += 1

        # Save scene configuration if any videos were uploaded
        if video_count > 0:
            scene_config_path = INPUT_DIR / "scene_config.json"
            with open(scene_config_path, 'w', encoding='utf-8') as f:
                json.dump(scene_config, f, indent=2)

        # Handle per-scene transition sound files (optional)
        transition_sounds_dir = INPUT_DIR / "transition_sounds"
        transition_sounds_dir.mkdir(exist_ok=True)
        transition_sounds_saved = []

        # Check for transition sound uploads (format: transition_sound_0, transition_sound_1, etc.)
        for field_name in request.files:
            if field_name.startswith('transition_sound_'):
                position = field_name.replace('transition_sound_', '')
                sound_file = request.files[field_name]

                if sound_file and sound_file.filename != '':
                    if allowed_file(sound_file.filename, 'transition_sound'):
                        # Save with position in filename
                        sound_path = transition_sounds_dir / f"{position}.mp3"
                        sound_file.save(str(sound_path))
                        transition_sounds_saved.append(position)

    except Exception as e:
        return Response(
            send_sse_message('error', message=f'Upload error: {str(e)}'),
            mimetype='text/event-stream'
        )
    
    # Now create the generator function (files are already saved)
    def generate():
        try:
            yield send_sse_message('log', message='Files validated successfully', level='info')
            yield send_sse_message('progress', percentage=10, message='Saving uploaded files...')
            
            yield send_sse_message('log', message=f'✓ Saved transcript: {transcript_filename}', level='success')
            yield send_sse_message('log', message=f'✓ Saved audio: {audio_filename}', level='success')
            yield send_sse_message('log', message=f'✓ Saved {image_count} images', level='success')
            if video_count > 0:
                yield send_sse_message('log', message=f'✓ Saved {video_count} video scene(s)', level='success')
            if transition_sounds_saved:
                yield send_sse_message('log', message=f'✓ Saved {len(transition_sounds_saved)} transition sound(s)', level='success')
            yield send_sse_message('progress', percentage=20, message='Files uploaded successfully')
            
            # Run the video creation script
            yield send_sse_message('log', message='Starting video generation...', level='info')
            yield send_sse_message('progress', percentage=25, message='Processing...')
            
            # Execute the create_video.py script
            process = subprocess.Popen(
                [sys.executable, str(CREATE_VIDEO_SCRIPT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=str(PROJECT_ROOT)
            )
            
            # Stream output
            progress_map = {
                'Transcribing audio': 30,
                'Matching paragraphs': 45,
                'Creating image clips': 60,
                'Burning captions': 75,
                'Generating final video': 90
            }
            
            current_progress = 25
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Determine log level
                    level = 'info'
                    if '✓' in line or 'Success' in line or 'Complete' in line:
                        level = 'success'
                    elif '❌' in line or 'Error' in line or 'Failed' in line:
                        level = 'error'
                    elif '⚠' in line or 'Warning' in line:
                        level = 'warning'
                    
                    yield send_sse_message('log', message=line, level=level)
                    
                    # Update progress based on keywords
                    for keyword, progress in progress_map.items():
                        if keyword.lower() in line.lower():
                            current_progress = progress
                            yield send_sse_message('progress', percentage=progress, message=keyword)
                            break
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                # Check if output file exists
                output_video = OUTPUT_DIR / "final_video.mp4"
                if output_video.exists():
                    yield send_sse_message('log', message='✓ Video created successfully!', level='success')
                    yield send_sse_message('progress', percentage=100, message='Complete!')
                    yield send_sse_message('complete', videoUrl='/api/download-video')
                else:
                    yield send_sse_message('error', message='Video file not found after processing')
            else:
                yield send_sse_message('error', message=f'Video generation failed with code {return_code}')
                
        except Exception as e:
            yield send_sse_message('error', message=f'Processing error: {str(e)}')
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/download-video')
def download_video():
    """Download the generated video"""
    output_video = OUTPUT_DIR / "final_video.mp4"
    if output_video.exists():
        return send_from_directory(
            str(OUTPUT_DIR),
            'final_video.mp4',
            as_attachment=True,
            download_name=f'video_{int(time.time())}.mp4'
        )
    else:
        return jsonify({'error': 'Video not found'}), 404

@app.route('/api/clear', methods=['POST'])
def clear_files():
    """Clear all uploaded files"""
    try:
        clear_input_directory()
        return jsonify({'success': True, 'message': 'Files cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure directories exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (INPUT_DIR / "images").mkdir(exist_ok=True)
    (INPUT_DIR / "videos").mkdir(exist_ok=True)
    
    print("=" * 60)
    print("🎬 Video Maker Web Application")
    print("=" * 60)
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📁 Input Directory: {INPUT_DIR}")
    print(f"📁 Output Directory: {OUTPUT_DIR}")
    print(f"🔧 Script: {CREATE_VIDEO_SCRIPT}")
    print("=" * 60)
    print("🚀 Starting server on http://localhost:8081")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8081, threaded=True)
