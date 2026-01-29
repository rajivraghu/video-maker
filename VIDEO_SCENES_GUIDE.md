# Using Video Clips in Scenes

This guide explains how to use video clips instead of images for certain scenes in your video project.

## Overview

By default, all scenes use images. However, you can configure specific scenes to use video clips (.mp4 files) instead. The video will play for the duration of that scene's audio, with the original audio replaced by your narration.

## Setup

### 1. Project Structure

Your project should have this structure:

```
video_maker/
├── input/
│   ├── audio.mp3
│   ├── transcript.txt
│   ├── images/
│   │   ├── 1.png
│   │   ├── 2.png
│   │   └── ...
│   ├── videos/          # NEW: Place your video clips here
│   │   ├── scene2.mp4
│   │   ├── scene5.mp4
│   │   └── ...
│   └── scene_config.json  # NEW: Configuration file
├── scripts/
│   └── create_video.py
└── configure_scenes.html    # NEW: UI tool
```

### 2. Add Video Files

1. Create the `input/videos/` folder (if it doesn't exist)
2. Place your `.mp4` video files in this folder
3. Name them descriptively (e.g., `scene2.mp4`, `intro.mp4`, etc.)

### 3. Configure Scenes

#### Option A: Use the Web UI (Recommended - With Server)

1. Start the server: `python server.py`
2. Open http://localhost:8080 in your browser
3. Upload transcript, audio, and images
4. The scene configuration section will automatically appear
5. For each scene you want to use a video:
   - Toggle the "Use Video" switch
   - Click "Browse Video" button
   - Select the video file from your computer
6. Click "Generate Video" button
7. The server will process everything and create your video with mixed images/videos!

#### Option B: Manual Configuration (Without Server)

1. Place video files in `input/videos/` folder
2. Create `input/scene_config.json` manually:

```json
{
  "scenes": {
    "2": {
      "type": "video",
      "path": "input/videos/scene2.mp4"
    }
  }
}
```

3. Run: `python scripts/create_video.py`

#### Option C: Download Config (Advanced)

Create or edit `input/scene_config.json`:

```json
{
  "scenes": {
    "2": {
      "type": "video",
      "path": "input/videos/scene2.mp4"
    },
    "5": {
      "type": "video",
      "path": "input/videos/action_scene.mp4"
    }
  }
}
```

- Scene numbers correspond to paragraph numbers in your transcript
- Paths can be relative to project root or absolute
- Scenes not listed will use images by default

### 4. Run Video Creation

Run your script normally:

```bash
python scripts/create_video.py
```

The script will:
- Use images for scenes not configured as videos
- Use video clips for configured scenes
- Trim videos to match the scene duration
- Remove original audio from videos and use your narration
- Apply the same transitions and effects to all scenes

## How It Works

### Video Processing

When a scene is configured to use a video:

1. The video is trimmed to match the exact duration of that scene's audio
2. The original audio from the video is removed
3. Your narration audio is used instead
4. The video is scaled and padded to match your output resolution
5. Fade transitions are applied (if configured)

### Audio Sync

- Videos play at their normal speed
- If the video is longer than the scene duration, it's trimmed
- If the video is shorter, only the available duration is used (consider this when selecting videos)

## Tips

### Video Duration

- Make sure your video clips are **at least as long** as the scene duration
- Check `output/paragraph_timings.txt` to see each scene's duration
- Videos will be trimmed if they're too long, but won't be looped if too short

### Video Quality

- Use videos with similar quality/resolution for consistency
- Higher quality source videos produce better results
- The output resolution is set in `create_video.py` (default: same as images)

### Performance

- Video processing takes longer than images
- Use shorter video clips when possible
- Consider using lower resolution videos if output resolution is lower

### Best Practices

1. **Plan ahead**: Decide which scenes need videos before starting
2. **Test first**: Try with one video scene before configuring many
3. **Backup config**: Save your `scene_config.json` in version control
4. **Organize videos**: Use descriptive names for video files
5. **Check output**: Review `output/paragraph_timings.txt` to verify scene durations

## Examples

### Example 1: Intro with Video

```json
{
  "scenes": {
    "1": {
      "type": "video",
      "path": "input/videos/intro.mp4"
    }
  }
}
```

Scene 1 uses a video intro, all other scenes use images.

### Example 2: Multiple Video Scenes

```json
{
  "scenes": {
    "1": {
      "type": "video",
      "path": "input/videos/intro.mp4"
    },
    "5": {
      "type": "video",
      "path": "input/videos/demonstration.mp4"
    },
    "12": {
      "type": "video",
      "path": "input/videos/outro.mp4"
    }
  }
}
```

Scenes 1, 5, and 12 use videos; all others use images.

### Example 3: All Videos

```json
{
  "scenes": {
    "1": {"type": "video", "path": "input/videos/scene1.mp4"},
    "2": {"type": "video", "path": "input/videos/scene2.mp4"},
    "3": {"type": "video", "path": "input/videos/scene3.mp4"}
  }
}
```

All scenes use videos (still need corresponding images as fallback).

## Troubleshooting

### "Video not found" Warning

- Check that the video file exists at the specified path
- Verify the path is correct (relative to project root)
- The script will fall back to using the image for that scene

### Video Too Short

- The video plays for its full duration, even if shorter than the scene
- Consider using a longer video or an image for short scenes

### Quality Issues

- Ensure source videos have good quality
- Check that videos match your desired output resolution
- Adjust `VIDEO_CRF` in `create_video.py` for quality (lower = better)

### Performance/Speed

- Video processing is slower than images
- Use `VIDEO_PRESET = "ultrafast"` for faster encoding (lower quality)
- Use `VIDEO_PRESET = "slow"` for better quality (slower encoding)

## Advanced Usage

### Custom Video Paths

You can use absolute paths or paths from anywhere:

```json
{
  "scenes": {
    "1": {
      "type": "video",
      "path": "/Users/username/Videos/my_clip.mp4"
    }
  }
}
```

### Mixing Content Types

Create dynamic videos by mixing images and videos:
- Static scenes: Use images
- Action sequences: Use video clips
- Demonstrations: Use screen recordings
- Transitions: Use animated video clips

## Summary

1. Place video files in `input/videos/`
2. Use `configure_scenes.html` to set which scenes use videos
3. Save configuration to `input/scene_config.json`
4. Run `create_video.py` normally
5. Your video will use a mix of images and video clips as configured

Enjoy creating dynamic videos with mixed media content!
