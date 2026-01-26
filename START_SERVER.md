# How to Start the Video Maker Web Server

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `flask` - Web server
- `flask-cors` - CORS support for web interface
- `faster-whisper` - Audio transcription
- `ffmpeg` - Video processing (must be installed separately)

### 2. Start the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

You'll see:
```
================================================================================
VIDEO MAKER - Web Server
================================================================================

Starting server...
Open your browser and navigate to: http://localhost:5000

Press Ctrl+C to stop the server
================================================================================
```

### 3. Open Your Browser

Navigate to: **http://localhost:5000**

## Using the Web Interface

### Step 1: Upload Your Content
1. **Transcript** - Upload your script (.txt file)
2. **Audio** - Upload your narration (.mp3 file)
3. **Images** - Upload scene images (.png, .jpg)

### Step 1.5: Configure Scenes (Optional)
After uploading the transcript, you can:
1. Toggle any scene to "Use Video"
2. Click "Browse Video" and select a video file
3. Repeat for other scenes you want as videos

### Step 2: Generate Video
Click the **"Generate Video"** button!

The system will:
- Upload all your files
- Process the audio with AI transcription
- Sync scenes with audio timing
- Mix images and videos based on your configuration
- Apply transitions and effects
- Generate the final video

### Step 3: Download
Once complete, click **"Download Video"** to get your finished video!

## Features

### Mixed Media
- Use images for some scenes
- Use video clips for other scenes
- Seamless transitions between all media types

### Automatic Sync
- AI-powered audio transcription
- Automatic scene timing
- Perfect audio-visual synchronization

### Professional Output
- Fade transitions between scenes
- Consistent resolution and formatting
- Subtitle generation (.srt file)
- Timing data for reference

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `server.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
to a different port (e.g., 5001)

### FFmpeg Not Found
Make sure ffmpeg is installed:
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html

### Video Processing Fails
Check the server logs in the terminal for error messages. Common issues:
- Not enough images for scenes
- Video files are corrupted or unsupported format
- Insufficient disk space

### Browser Doesn't Connect
- Make sure the server is running
- Try `http://127.0.0.1:5000` instead of `localhost`
- Check your firewall settings

## Advanced Usage

### Command Line
You can still use the command-line script directly:
```bash
python scripts/create_video.py
```

This requires files in the `input/` folder as before.

### Custom Configuration
For advanced users, you can:
1. Save scene configuration by clicking "Save Config (Advanced)"
2. Manually edit `scene_config.json`
3. Place files in `input/` folder
4. Run `python scripts/create_video.py`

## Output Location

Generated videos are saved to:
```
output/video_<timestamp>.mp4
```

Each video has a unique timestamp to prevent overwriting.

## Tips

1. **Use numbered images** - Name your images 1.png, 2.png, etc. for proper ordering
2. **Match video durations** - Ensure scene videos are at least as long as the narration for that scene
3. **Test with small files first** - Start with a short transcript to test the workflow
4. **Check logs** - The web interface shows detailed progress and any errors
5. **Video quality** - Videos are trimmed and scaled to match your configuration

## System Requirements

- Python 3.8 or higher
- FFmpeg installed on system
- 4GB+ RAM recommended
- Sufficient disk space for temporary files

Enjoy creating videos! 🎬
