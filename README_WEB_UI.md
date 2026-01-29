# Video Maker - Web UI with Mixed Images & Videos

Create professional videos with a mix of images and video clips, perfectly synced to your narration!

## Features

- **Web-based interface** - No command line needed
- **Mixed media** - Use both images AND videos in the same project
- **Scene-level control** - Choose image or video for each scene individually
- **AI-powered sync** - Automatic audio transcription and timing
- **Professional output** - Smooth transitions, perfect sync, subtitle generation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure you have **ffmpeg** installed:
- Mac: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`
- Windows: Download from https://ffmpeg.org

### 2. Start the Server

```bash
python server.py
```

Open your browser to: **http://localhost:8080**

### 3. Create Your Video

#### Step 1: Upload Your Content
- **Transcript**: Your script as a text file (.txt)
- **Audio**: Your narration recording (.mp3)
- **Images**: Scene images (.png, .jpg) - name them 1.png, 2.png, etc.

#### Step 1.5: Configure Scenes (Optional)
After uploading the transcript, you'll see all your scenes listed.

For each scene, you can:
- Leave it as **image** (default)
- Toggle to **video** and browse to select a video clip

The video clip will play during that scene's narration, with the original audio replaced by your narration.

#### Step 2: Generate Video
Click the **"Generate Video"** button!

Watch the progress as your video is created:
- Files upload
- Audio transcription
- Scene timing calculation
- Video clip processing
- Final assembly

#### Step 3: Download
When complete, click **"Download Video"** to get your finished video!

## Example Workflow

Let's say you have a 5-scene video:

1. **Scene 1**: Intro - Use a video clip of your logo animation
2. **Scene 2**: Overview - Use an image with bullet points
3. **Scene 3**: Demo - Use a screen recording video
4. **Scene 4**: Benefits - Use an image with icons
5. **Scene 5**: Call to action - Use a video clip of your product

### How to Set This Up:

1. Upload your transcript with 5 paragraphs
2. Upload 5 images (even for video scenes - as fallback)
3. Upload your audio narration
4. In the scene configurator:
   - Scene 1: Toggle "Use Video", browse and select logo.mp4
   - Scene 2: Leave as image
   - Scene 3: Toggle "Use Video", browse and select demo.mp4
   - Scene 4: Leave as image
   - Scene 5: Toggle "Use Video", browse and select cta.mp4
5. Click "Generate Video"

Done! Your video will have videos for scenes 1, 3, and 5, and images for scenes 2 and 4.

## Output

Your generated video will have:
- Perfect audio-visual synchronization
- Smooth fade transitions between scenes
- Consistent resolution and formatting
- Professional quality output

Plus these additional files:
- `subtitles.srt` - Subtitle file for your video
- `paragraph_timings.json` - Detailed timing data
- `paragraph_timings.txt` - Human-readable timing info

## Tips

### Image Naming
Name your images with numbers for proper ordering:
- `1.png`, `2.png`, `3.png` ✓
- `image1.png`, `image2.png`, `image3.png` ✓
- `scene_001.jpg`, `scene_002.jpg` ✓

### Video Clips
- Make sure video clips are **at least as long** as the narration for that scene
- Videos are automatically trimmed to match scene duration
- Original audio is removed and replaced with your narration
- All videos are scaled to match your output resolution

### Transcript Format
Each paragraph in your transcript becomes one scene:

```
This is the first scene. It introduces the topic.

This is the second scene. It explains the concept.

This is the third scene. It demonstrates the solution.
```

Blank lines separate scenes.

### Scene Videos
- Upload videos one at a time per scene using "Browse Video"
- The filename doesn't matter - each video is linked to its scene number
- You can change videos by clicking "Browse Video" again
- Click "Reset All to Images" to quickly remove all video selections

## Technical Details

### How It Works

1. **Upload Phase**: All files are uploaded to the server
2. **Transcription**: Audio is transcribed using Whisper AI
3. **Sync**: Transcript paragraphs are matched to audio timestamps
4. **Scene Processing**:
   - Images are converted to video clips
   - Video clips are trimmed and scaled
   - Fade transitions are applied
5. **Assembly**: All clips are concatenated with the audio track
6. **Output**: Final video is generated and made available for download

### Video Processing

For image scenes:
- Image displayed for the duration of narration
- Scaled to output resolution
- Fade in/out transitions

For video scenes:
- Video plays for the duration of narration
- Trimmed if too long
- Original audio removed
- Scaled to output resolution
- Fade in/out transitions

### Performance

Processing time depends on:
- Number of scenes
- Total video duration
- Number of video scenes (slower than images)
- Your computer's CPU

Typical processing time: **2-5 minutes** for a 2-minute video with mixed media.

## Troubleshooting

### "Server error: 500"
- Check the terminal for error messages
- Make sure ffmpeg is installed
- Verify all files are valid (not corrupted)

### "Video not found for scene X"
- The video file couldn't be loaded
- Try re-uploading the video
- Check the file format (.mp4, .mov, .avi)

### Video Quality Issues
- Increase source image/video resolution
- Adjust VIDEO_CRF in `scripts/create_video.py` (lower = better quality)

### Audio Sync Issues
- Make sure your transcript matches your audio exactly
- Check that audio file is not corrupted
- Try a different audio format

## Advanced Usage

### Command Line (No Server)

If you prefer the command line:

1. Place files in `input/` folder
2. Optionally create `input/scene_config.json`
3. Run: `python scripts/create_video.py`

### Custom Configuration

Edit `scripts/create_video.py` to customize:
- Video quality (VIDEO_CRF)
- Output resolution (OUTPUT_WIDTH, OUTPUT_HEIGHT)
- Transition duration (TRANSITION_DURATION)
- Transcription model (MODEL_SIZE)

## Support

For issues or questions:
- Check [VIDEO_SCENES_GUIDE.md](VIDEO_SCENES_GUIDE.md) for detailed instructions
- Check [START_SERVER.md](START_SERVER.md) for server setup help
- Review logs in the terminal for error messages

## License

This project is provided as-is for video creation purposes.

---

**Enjoy creating amazing videos with mixed images and video clips! 🎬🎥**
