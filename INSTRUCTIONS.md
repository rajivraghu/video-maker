# Detailed Instructions - Video Maker

## 📋 Table of Contents
1. [File Preparation](#file-preparation)
2. [Input Requirements](#input-requirements)
3. [Running the Script](#running-the-script)
4. [Understanding the Output](#understanding-the-output)
5. [Customization Options](#customization-options)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)

---

## 📁 File Preparation

### 1. Transcript File (transcript.txt)

**Location:** `input/transcript.txt`

**Format:**
- Plain text file
- One paragraph per section
- Separate paragraphs with blank lines
- UTF-8 encoding

**Example:**
```
Many of us, while sitting at our desks working, drift into imagination.

But when that evening time actually arrives, we completely waste it.

We start scrolling, and we lose track of time entirely.
```

**Tips:**
- Each paragraph = one scene/image
- Keep paragraphs concise (1-3 sentences)
- Match the exact wording from your narration
- Don't include headers or metadata

---

### 2. Audio File (audio.mp3)

**Location:** `input/audio.mp3`

**Supported Formats:**
- MP3 (recommended)
- WAV
- M4A
- Any format FFmpeg supports

**Requirements:**
- Must match your transcript
- Clear narration (no background music if possible)
- Mono or stereo
- Any bitrate (will be normalized to 192kbps)

**Tips:**
- Higher quality audio = better transcription accuracy
- Remove long silences at start/end
- Consistent volume throughout

---

### 3. Images Folder

**Location:** `input/images/`

**Naming Convention:**
```
1_description.png
2_description.png
3_description.png
...
60_description.png
```

**Rules:**
- Must start with a number (1, 2, 3...)
- Number determines the order
- Everything after the number is ignored
- Supported formats: PNG, JPG, JPEG

**Examples:**
✅ Good:
- `1_intro.png`
- `2_problem.jpg`
- `3_solution_slide.png`
- `10_conclusion.jpeg`

❌ Bad:
- `intro_1.png` (number not at start)
- `slide1.png` (no underscore separator)
- `image.png` (no number)

**Image Requirements:**
- Any resolution (will be scaled)
- Same aspect ratio recommended
- RGB or RGBA color space
- File size: any (will be compressed)

---

## 🚀 Running the Script

### Basic Usage

1. **Navigate to project folder:**
   ```bash
   cd video_maker
   ```

2. **Run the script:**
   ```bash
   python scripts/create_video.py
   ```

3. **Wait for completion:**
   - Progress will be shown in terminal
   - Typical time: 5-10 minutes for 7-minute video
   - Do not interrupt the process

4. **Check output:**
   ```bash
   ls output/
   ```

### What Happens During Processing

1. **Step 1: Loading Files** (5 seconds)
   - Reads transcript
   - Validates image files
   - Checks audio file

2. **Step 2: Transcription** (2-4 minutes)
   - Uses WhisperX to transcribe audio
   - Generates word-level timestamps
   - Detects language automatically

3. **Step 3: Matching** (10 seconds)
   - Matches transcript paragraphs to audio
   - Calculates precise timing for each scene
   - Adjusts for perfect synchronization

4. **Step 4: Creating SRT** (5 seconds)
   - Generates subtitle file
   - Formats timestamps

5. **Step 5: Video Assembly** (3-5 minutes)
   - Creates video from images
   - Syncs with audio
   - Burns in captions
   - Encodes final video

---

## 📤 Understanding the Output

### Generated Files

**output/final_video.mp4**
- Your complete video
- H.264 codec (universal compatibility)
- Burned-in captions
- Ready to upload anywhere

**output/subtitles.srt**
- Standard subtitle file
- Can be used separately
- Upload to YouTube for multi-language support
- Compatible with all video players

**output/paragraph_timings.json**
- Technical timing data
- Shows when each paragraph starts/ends
- Useful for verification
- Machine-readable format

**output/paragraph_timings.txt**
- Human-readable timing info
- Review synchronization quality
- Debug timing issues

---

## 🎨 Customization Options

### Caption Styling

Edit `scripts/create_video.py`, find this section:

```python
# Caption style configuration
FONT_NAME = "Arial"           # Change font
FONT_SIZE = 22               # Change size (bigger = larger text)
FONT_COLOR = "&H00FFFFFF"    # White (in BGR hex)
OUTLINE_COLOR = "&H00000000" # Black outline
OUTLINE_WIDTH = 2            # Outline thickness
MARGIN_BOTTOM = 50           # Distance from bottom (pixels)
```

**Color Format:**
- Use BGR (not RGB) in hex format
- Format: `&H00BBGGRR`
- Examples:
  - White: `&H00FFFFFF`
  - Black: `&H00000000`
  - Red: `&H000000FF`
  - Blue: `&H00FF0000`
  - Yellow: `&H0000FFFF`

### Video Quality

```python
# Video quality settings
VIDEO_CRF = 23    # Lower = better quality (18-28 recommended)
VIDEO_PRESET = "medium"  # Options: ultrafast, fast, medium, slow, slower
AUDIO_BITRATE = "192k"   # 128k, 192k, or 256k
```

### Transcription Model

```python
# WhisperX model selection
MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large
# tiny   = fastest, least accurate
# base   = good balance (recommended)
# small  = better accuracy, slower
# medium = high accuracy, much slower
# large  = best accuracy, very slow
```

### Output Resolution

```python
# Force specific resolution (optional)
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
# Or leave as None to use image resolution
```

---

## 🔧 Advanced Usage

### Processing Part of a Video

If you only want to process paragraphs 1-10:

```python
# In create_video.py, add this near the top:
MAX_PARAGRAPHS = 10
```

### Using Different Audio Format

The script auto-detects format. Just rename your file:
```bash
mv input/audio.wav input/audio.mp3
```

### Batch Processing

Create a script to process multiple videos:

```bash
#!/bin/bash
for dir in project1 project2 project3; do
  cd $dir
  python scripts/create_video.py
  cd ..
done
```

### Custom Image Sequence

To skip certain paragraphs, create placeholder images:
```
1_intro.png
2_skip.png     # Black image or duplicate
3_content.png
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'faster_whisper'"**

Solution:
```bash
pip install faster-whisper
```

**Issue: "FileNotFoundError: audio.mp3"**

Solution:
- Check filename is exactly `audio.mp3`
- Check it's in `input/` folder
- Check file permissions

**Issue: "Not enough images for paragraphs"**

Solution:
- Count paragraphs: `grep -c "^$" input/transcript.txt`
- Count images: `ls input/images/*.png | wc -l`
- Add more images or reduce paragraphs

**Issue: "FFmpeg not found"**

Solution Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

Solution MacOS:
```bash
brew install ffmpeg
```

**Issue: Video sync is slightly off**

Solution:
- Use higher quality audio
- Speak clearly in narration
- Try different transcription model (small or medium)
- Manually adjust in `paragraph_timings.json`

**Issue: Captions are cut off**

Solution:
- Increase `MARGIN_BOTTOM` value
- Reduce `FONT_SIZE`
- Use shorter paragraphs

**Issue: Processing is very slow**

Solution:
- Use `tiny` or `base` model
- Close other applications
- Process shorter videos
- Use `fast` or `ultrafast` preset

**Issue: Output video is too large**

Solution:
- Increase `VIDEO_CRF` (23 → 26)
- Use `fast` preset
- Reduce audio bitrate (192k → 128k)
- Lower output resolution

---

## 💡 Best Practices

### For Best Results:

1. **Audio Quality:**
   - Use noise-free environment
   - Consistent speaking pace
   - Clear pronunciation
   - No background music during speech

2. **Transcript Accuracy:**
   - Match narration exactly
   - Include filler words if in audio
   - Same punctuation as spoken

3. **Image Consistency:**
   - Same aspect ratio for all images
   - Similar color schemes
   - Professional quality
   - Appropriate resolution (1920x1080 or higher)

4. **Paragraph Structure:**
   - 1-3 sentences per paragraph
   - Natural break points
   - Similar length paragraphs
   - Clear topic per paragraph

### Workflow Recommendations:

1. Start with 5-10 paragraphs to test
2. Verify sync quality
3. Adjust settings if needed
4. Process full video
5. Review output
6. Make final adjustments

---

## 📊 Performance Guide

### Processing Time Estimates:

| Video Length | Paragraphs | Model | Time |
|--------------|------------|-------|------|
| 2 minutes    | 15-20      | base  | 2-3 min |
| 5 minutes    | 40-50      | base  | 4-6 min |
| 7 minutes    | 60-70      | base  | 6-8 min |
| 10 minutes   | 80-100     | base  | 8-12 min |

### File Size Estimates:

| Video Length | Resolution | CRF 23 | CRF 28 |
|--------------|------------|--------|--------|
| 2 minutes    | 1920x1080  | 8-12 MB | 5-8 MB |
| 5 minutes    | 1920x1080  | 15-20 MB | 10-15 MB |
| 7 minutes    | 1344x768   | 15-20 MB | 10-12 MB |
| 10 minutes   | 1920x1080  | 25-35 MB | 15-25 MB |

---

## 🎓 Example Workflow

Here's a complete example:

```bash
# 1. Set up project
cd video_maker

# 2. Add your files
# - Copy transcript.txt to input/
# - Copy audio.mp3 to input/
# - Copy numbered images to input/images/

# 3. Verify file count
echo "Paragraphs:" $(grep -c "^$" input/transcript.txt)
echo "Images:" $(ls input/images/*.png | wc -l)

# 4. Run the script
python scripts/create_video.py

# 5. Check output
ls -lh output/final_video.mp4

# 6. Play video
# (Use your favorite video player)

# 7. Upload or share!
```

---

## 🎯 Quality Checklist

Before publishing, verify:

- [ ] Audio and captions are synchronized
- [ ] All images appear in correct order
- [ ] Captions are readable (not cut off)
- [ ] No missing scenes
- [ ] Audio quality is good
- [ ] Video plays smoothly
- [ ] File size is acceptable
- [ ] Compatible with target platform

---

**You're all set! Happy video making! 🎬**
