# Video Maker - Automated Transcript to Video Generator

A powerful tool that creates synchronized videos from transcripts, images, **video clips**, and audio narration.

## ✨ NEW: Mixed Images & Videos

Now you can mix both **images** and **video clips** in the same project! Use images for static scenes and videos for action sequences, all perfectly synced to your narration.

### Quick Start (Web UI)
```bash
./start.sh
# Open http://localhost:8080
```

See [README_WEB_UI.md](README_WEB_UI.md) for the full web interface guide.

## 🎬 What It Does

This tool automatically:
1. Transcribes your audio using Whisper AI for word-level timestamps
2. Matches transcript paragraphs to audio timing
3. Syncs images/videos to change when each paragraph begins
4. **Mixes images and video clips seamlessly**
5. Applies smooth fade transitions
6. Creates professional subtitles
7. Generates a polished, production-ready video

## 📋 Requirements

### System Requirements
- Python 3.8+
- FFmpeg installed
- At least 2GB RAM
- ~5-10 minutes processing time for 7-minute videos

### Python Dependencies
Install with:
```bash
pip install faster-whisper
```

Note: WhisperX will be installed automatically if needed.

## 📁 Project Structure

```
video_maker/
├── README.md              # This file
├── INSTRUCTIONS.md        # Detailed usage guide
├── input/                 # Put your files here
│   ├── transcript.txt     # Your script (one paragraph per line)
│   ├── audio.mp3         # Your narration audio
│   └── images/           # Folder with numbered images
│       ├── 1_image.png
│       ├── 2_image.png
│       └── ... (as many as paragraphs)
├── output/               # Generated videos appear here
│   ├── final_video.mp4
│   ├── subtitles.srt
│   └── paragraph_timings.json
└── scripts/              # Processing scripts
    ├── create_video.py   # Main video creation script
    └── requirements.txt  # Python dependencies
```

## 🚀 Quick Start

### Step 1: Prepare Your Files

1. **Create your transcript** (`input/transcript.txt`):
   - One paragraph per line
   - Empty lines between paragraphs
   - Example:
     ```
     This is the first paragraph of narration.

     This is the second paragraph of narration.

     This is the third paragraph.
     ```

2. **Add your audio** (`input/audio.mp3`):
   - MP3 format recommended
   - Should match your transcript
   - Any length supported

3. **Add your images** (`input/images/`):
   - Name them: `1_name.png`, `2_name.png`, etc.
   - Number of images should match number of paragraphs
   - PNG or JPG format
   - Any resolution (will be scaled automatically)

### Step 2: Install Dependencies

```bash
cd video_maker
pip install -r scripts/requirements.txt
```

### Step 3: Run the Script

```bash
cd video_maker
python scripts/create_video.py
```

### Step 4: Get Your Video!

Your video will be in `output/final_video.mp4`

## 📖 Detailed Usage

See [INSTRUCTIONS.md](INSTRUCTIONS.md) for:
- File naming conventions
- Advanced options
- Troubleshooting
- Customization guide

## ✨ Features

- ✅ **Automatic Transcription** - Uses WhisperX for precise word-level timing
- ✅ **Perfect Sync** - Images change exactly when paragraphs change
- ✅ **Professional Captions** - Burned-in subtitles with clean styling
- ✅ **Smart Matching** - Automatically aligns transcript to audio
- ✅ **High Quality** - Optimized H.264 encoding
- ✅ **Flexible Input** - Supports various image sizes and formats
- ✅ **Reusable** - Run as many times as you want

## 🎨 Output Quality

- **Video Codec:** H.264 (universal compatibility)
- **Audio Codec:** AAC 192kbps
- **Frame Rate:** 25 fps
- **Caption Style:** White text, black outline, bottom center
- **Resolution:** Matches your input images

## 🔧 Configuration

Edit `scripts/create_video.py` to customize:
- Caption font, size, color
- Video quality settings
- Output resolution
- Transcription model (base/small/medium/large)

## 📊 Example Output

For a 7-minute video with 60 paragraphs:
- Processing time: ~5-7 minutes
- Output size: ~15-20 MB
- Quality: Production-ready

## ❓ Troubleshooting

### "No audio file found"
- Make sure `input/audio.mp3` exists
- Check the filename is exactly `audio.mp3`

### "Not enough images"
- Count your paragraphs in transcript.txt
- Make sure you have one image per paragraph
- Check image numbering starts at 1

### "FFmpeg not found"
- Install FFmpeg: `sudo apt install ffmpeg` (Linux)
- Or download from: https://ffmpeg.org/

### "Out of memory"
- Use smaller transcription model (edit script)
- Process shorter videos
- Close other applications

## 🎯 Tips for Best Results

1. **Clear Audio:** Use high-quality audio recording
2. **Match Length:** Ensure audio matches transcript
3. **Consistent Images:** Use same aspect ratio for all images
4. **Paragraph Length:** Keep paragraphs to 1-3 sentences
5. **Test First:** Try with 3-5 paragraphs before full video

## 📝 License

Free to use for any purpose. No attribution required.

## 🤝 Support

For issues or questions:
1. Check INSTRUCTIONS.md
2. Review troubleshooting section
3. Verify your input files format

## 🎉 You're Ready!

Just add your files to the `input/` folder and run the script. Your professional video will be ready in minutes!
