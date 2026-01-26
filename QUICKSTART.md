# 🚀 Quick Start Guide

Get your video in 5 minutes!

## Step 1: Install Dependencies (One-time setup)

```bash
cd video_maker
pip install -r scripts/requirements.txt
```

**Also install FFmpeg:**
- Ubuntu/Debian: `sudo apt install ffmpeg`
- MacOS: `brew install ffmpeg`
- Windows: Download from https://ffmpeg.org/

## Step 2: Add Your Files

```
input/
├── transcript.txt     ← Your script (one paragraph per line)
├── audio.mp3         ← Your narration
└── images/           ← Numbered images (1_name.png, 2_name.png, ...)
```

### transcript.txt Example:
```
This is my first paragraph.

This is my second paragraph.

This is my third paragraph.
```

### images/ Example:
```
1_intro.png
2_content.png
3_conclusion.png
```

**Important:** Number of paragraphs = Number of images

## Step 3: Run the Script

```bash
python scripts/create_video.py
```

## Step 4: Get Your Video!

Your video will be in: `output/final_video.mp4`

---

## ⚡ That's It!

Your video is ready with:
- ✅ Synchronized images
- ✅ Professional captions
- ✅ Perfect timing

## 🐛 Troubleshooting

**"Module not found"**
```bash
pip install faster-whisper
```

**"FFmpeg not found"**
```bash
# Install FFmpeg first (see Step 1)
```

**"Not enough images"**
- Count paragraphs: Count non-empty lines in transcript.txt
- Count images: Check files in images/ folder
- They must match!

---

## 📖 Need More Help?

- See `README.md` for overview
- See `INSTRUCTIONS.md` for detailed guide
- Check example files in `input/`

**Happy video making!** 🎬
