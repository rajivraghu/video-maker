#!/usr/bin/env python3
"""
Video Maker - Automated Transcript to Video Generator
Syncs images with audio narration based on transcript paragraphs
"""
import json
import subprocess
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

# =============================================================================
# CONFIGURATION - Edit these values to customize
# =============================================================================

# Caption Style Setting (can be overridden by CAPTION_STYLE environment variable)
# Options: 'default' (word highlighting), 'bold_caps' (bold all caps), 'none' (no captions)
CAPTION_STYLE = os.environ.get('CAPTION_STYLE', 'default')
print(f"[DEBUG] CAPTION_STYLE from environment: '{CAPTION_STYLE}'")

# Caption Style - Using Google Font (Poppins)
FONT_NAME = "Poppins"
FONT_SIZE = 48                  # Larger size for better readability
FONT_COLOR = "&H00FFFFFF"       # White text (BGR format)
HIGHLIGHT_COLOR = "&H00FFFF"    # Yellow for current word (BGR: 00FFFF = Yellow)
OUTLINE_COLOR = "&H00000000"    # Black outline
OUTLINE_WIDTH = 3               # Thicker outline for contrast
SHADOW_DEPTH = 2                # Shadow for better visibility
MARGIN_BOTTOM = 60              # Distance from bottom in pixels
CAPTION_ALIGNMENT = 2           # 2 = bottom center
WORDS_PER_LINE = 6              # Number of words to show per caption line

# Video Quality
VIDEO_CRF = 18                 # Lower = better quality (18-28 recommended, 18 for YouTube)
VIDEO_PRESET = "medium"        # ultrafast, fast, medium, slow, slower
AUDIO_BITRATE = "256k"         # Audio quality (YouTube recommended)

# Transcription
MODEL_SIZE = "base"            # tiny, base, small, medium, large
COMPUTE_TYPE = "int8"          # int8 or float16

# Output Resolution (None = use image resolution)
OUTPUT_WIDTH = None
OUTPUT_HEIGHT = None

# Transition Settings
TRANSITION_DURATION = 0.5       # Duration of crossfade between scenes in seconds
TRANSITION_SOUND_DURATION = 1.0 # Duration of transition sound effect in seconds

# FFmpeg path - use ffmpeg-full if available (has libass support for captions)
FFMPEG_FULL_PATH = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFMPEG_PATH = FFMPEG_FULL_PATH if Path(FFMPEG_FULL_PATH).exists() else "ffmpeg"

# =============================================================================
# FILE PATHS - Modify only if you change project structure
# =============================================================================

# Get project root (parent of scripts folder)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

TRANSCRIPT_FILE = INPUT_DIR / "transcript.txt"
AUDIO_FILE = INPUT_DIR / "audio.mp3"
IMAGES_DIR = INPUT_DIR / "images"
VIDEOS_DIR = INPUT_DIR / "videos"
SCENE_CONFIG_FILE = INPUT_DIR / "scene_config.json"
TRANSITION_SOUNDS_DIR = INPUT_DIR / "transition_sounds"

OUTPUT_VIDEO = OUTPUT_DIR / "final_video.mp4"
SRT_FILE = OUTPUT_DIR / "subtitles.srt"
ASS_FILE = OUTPUT_DIR / "subtitles.ass"
TIMING_JSON = OUTPUT_DIR / "paragraph_timings.json"
TIMING_TXT = OUTPUT_DIR / "paragraph_timings.txt"
FONTS_DIR = PROJECT_ROOT / "fonts"

# =============================================================================
# MAIN SCRIPT - No need to edit below unless customizing logic
# =============================================================================

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(text)
    print("="*80)

def print_step(step_num, text):
    """Print a step indicator"""
    print(f"\n[Step {step_num}] {text}")

def format_srt_time(seconds):
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def normalize_text(text):
    """Normalize text for matching"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join(text.split())
    return text

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        str(video_path)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        try:
            return float(result.stdout.strip())
        except ValueError:
            return None
    return None

def get_video_resolution(video_path):
    """Get video resolution (width, height) using ffprobe"""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0',
        str(video_path)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        try:
            width, height = map(int, result.stdout.strip().split(','))
            return width, height
        except (ValueError, AttributeError):
            return None, None
    return None, None


def download_google_font(font_name="Poppins"):
    """Download Google Font and return path to the font file"""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if font already exists
    font_file = FONTS_DIR / f"{font_name}-SemiBold.ttf"
    if font_file.exists():
        print(f"   Font already downloaded: {font_file.name}")
        return font_file

    # Also check for Regular variant
    font_file_regular = FONTS_DIR / f"{font_name}-Regular.ttf"
    if font_file_regular.exists():
        print(f"   Font already downloaded: {font_file_regular.name}")
        return font_file_regular

    print(f"   Downloading {font_name} font from Google Fonts...")

    # Direct download URLs for font files (GitHub mirrors)
    font_urls = {
        "Poppins": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
        "Poppins-Regular": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf"
    }

    url = font_urls.get(font_name)
    if not url:
        print(f"   ⚠️  Font {font_name} not configured, using system font")
        return None

    try:
        # Download the font file directly
        font_file = FONTS_DIR / f"{font_name}-SemiBold.ttf"
        urllib.request.urlretrieve(url, font_file)

        if font_file.exists() and font_file.stat().st_size > 1000:
            print(f"✓ Downloaded font: {font_file.name}")
            return font_file
        else:
            # Try regular variant as fallback
            font_file = FONTS_DIR / f"{font_name}-Regular.ttf"
            url = font_urls.get(f"{font_name}-Regular")
            if url:
                urllib.request.urlretrieve(url, font_file)
                if font_file.exists():
                    print(f"✓ Downloaded font: {font_file.name}")
                    return font_file

            print(f"   ⚠️  Could not download font file")
            return None

    except Exception as e:
        print(f"   ⚠️  Failed to download font: {e}")
        return None


def format_ass_time(seconds):
    """Convert seconds to ASS time format H:MM:SS.cc (centiseconds)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def generate_word_captions(all_words, font_path, video_width, video_height):
    """
    Generate ASS subtitle file with word-by-word highlighting.
    Shows groups of words with the current word highlighted in yellow.
    """
    # ASS Header with style definitions
    ass_header = f"""[Script Info]
Title: Video Captions with Word Highlighting
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},{FONT_SIZE},{FONT_COLOR},&H000000FF,{OUTLINE_COLOR},&H80000000,-1,0,0,0,100,100,0,0,1,{OUTLINE_WIDTH},{SHADOW_DEPTH},{CAPTION_ALIGNMENT},40,40,{MARGIN_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    if not all_words:
        return ass_header

    # Group words into chunks for display
    word_chunks = []
    current_chunk = []

    for i, word_info in enumerate(all_words):
        current_chunk.append({
            'word': word_info['word'].strip(),
            'start': word_info['start'],
            'end': word_info['end'],
            'index': i
        })

        # Create new chunk after WORDS_PER_LINE words or at natural breaks
        if len(current_chunk) >= WORDS_PER_LINE:
            word_chunks.append(current_chunk)
            current_chunk = []

    # Don't forget the last chunk
    if current_chunk:
        word_chunks.append(current_chunk)

    # Generate events for each word within each chunk
    for chunk in word_chunks:
        chunk_start = chunk[0]['start']
        chunk_end = chunk[-1]['end']

        # For each word in the chunk, create an event showing that word highlighted
        for word_idx, word_info in enumerate(chunk):
            word_start = word_info['start']
            # Word end is either the start of next word or end of chunk
            if word_idx < len(chunk) - 1:
                word_end = chunk[word_idx + 1]['start']
            else:
                word_end = word_info['end']

            # Build the caption text with current word highlighted
            caption_parts = []
            for j, w in enumerate(chunk):
                word_text = w['word']
                if j == word_idx:
                    # Current word - highlight in yellow
                    # ASS color format: {\c&HBBGGRR&}
                    caption_parts.append(f"{{\\c&H00FFFF&}}{word_text}{{\\c&HFFFFFF&}}")
                else:
                    # Other words - white
                    caption_parts.append(word_text)

            caption_text = " ".join(caption_parts)

            # Create ASS dialogue event
            start_time = format_ass_time(word_start)
            end_time = format_ass_time(word_end)

            event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{caption_text}"
            events.append(event)

    return ass_header + "\n".join(events)


def generate_bold_caps_captions(all_words, font_path, video_width, video_height):
    """
    Generate ASS subtitle file with bold all-caps captions.
    Shows groups of words in bold uppercase with yellow highlighting on current word.
    """
    # ASS Header with style definitions - Bold style
    ass_header = f"""[Script Info]
Title: Video Captions Bold Caps
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},{FONT_SIZE},{FONT_COLOR},&H000000FF,{OUTLINE_COLOR},&H80000000,-1,0,0,0,100,100,1,0,1,{OUTLINE_WIDTH + 1},{SHADOW_DEPTH},{CAPTION_ALIGNMENT},40,40,{MARGIN_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    if not all_words:
        return ass_header

    # Group words into chunks for display
    word_chunks = []
    current_chunk = []

    for i, word_info in enumerate(all_words):
        current_chunk.append({
            'word': word_info['word'].strip(),
            'start': word_info['start'],
            'end': word_info['end'],
            'index': i
        })

        # Create new chunk after WORDS_PER_LINE words
        if len(current_chunk) >= WORDS_PER_LINE:
            word_chunks.append(current_chunk)
            current_chunk = []

    # Don't forget the last chunk
    if current_chunk:
        word_chunks.append(current_chunk)

    # Generate events for each word within each chunk (with yellow highlighting)
    for chunk in word_chunks:
        # For each word in the chunk, create an event showing that word highlighted
        for word_idx, word_info in enumerate(chunk):
            word_start = word_info['start']
            # Word end is either the start of next word or end of chunk
            if word_idx < len(chunk) - 1:
                word_end = chunk[word_idx + 1]['start']
            else:
                word_end = word_info['end']

            # Build the caption text with current word highlighted in yellow (ALL CAPS)
            caption_parts = []
            for j, w in enumerate(chunk):
                word_text = w['word'].upper()  # Convert to uppercase
                if j == word_idx:
                    # Current word - highlight in yellow
                    # ASS color format: {\c&HBBGGRR&}
                    caption_parts.append(f"{{\\c&H00FFFF&}}{word_text}{{\\c&HFFFFFF&}}")
                else:
                    # Other words - white
                    caption_parts.append(word_text)

            caption_text = " ".join(caption_parts)

            # Create ASS dialogue event
            start_time = format_ass_time(word_start)
            end_time = format_ass_time(word_end)

            event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{caption_text}"
            events.append(event)

    return ass_header + "\n".join(events)


def main():
    print_header("VIDEO MAKER - Transcript to Video Generator")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # =============================================================================
    # STEP 1: VALIDATE INPUT FILES
    # =============================================================================
    print_step(1, "Validating Input Files")

    if not TRANSCRIPT_FILE.exists():
        print(f"❌ Error: Transcript file not found: {TRANSCRIPT_FILE}")
        print(f"   Please create: input/transcript.txt")
        sys.exit(1)

    if not AUDIO_FILE.exists():
        print(f"❌ Error: Audio file not found: {AUDIO_FILE}")
        print(f"   Please add: input/audio.mp3")
        sys.exit(1)

    if not IMAGES_DIR.exists():
        print(f"❌ Error: Images directory not found: {IMAGES_DIR}")
        print(f"   Please create: input/images/")
        sys.exit(1)

    print("✓ All input paths exist")

    # Download Google Font for captions
    print("   Downloading caption font...")
    font_path = download_google_font(FONT_NAME)

    # =============================================================================
    # STEP 2: READ TRANSCRIPT
    # =============================================================================
    print_step(2, "Reading Transcript")

    with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse paragraphs (non-empty lines)
    paragraphs = []
    for line in lines:
        line = line.strip()
        if line:
            paragraphs.append(line)

    print(f"✓ Found {len(paragraphs)} paragraphs in transcript")

    # =============================================================================
    # STEP 3: LOAD SCENE CONFIGURATION (Images/Videos)
    # =============================================================================
    print_step(3, "Loading Scene Configuration")

    # Create videos directory if it doesn't exist
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Load scene configuration
    scene_config = {}
    if SCENE_CONFIG_FILE.exists():
        with open(SCENE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            scene_config = config_data.get('scenes', {})
        print(f"✓ Loaded scene configuration")
    else:
        print(f"✓ No scene configuration found, using images for all scenes")

    # Get all image files and sort by number prefix
    image_files = sorted(
        list(IMAGES_DIR.glob("*.png")) + list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.jpeg")),
        key=lambda x: int(x.stem) if x.stem.isdigit() else int(x.stem.split('_')[0])
    )

    print(f"✓ Found {len(image_files)} images")

    # Count video scenes
    video_scene_count = sum(1 for scene in scene_config.values() if scene.get('type') == 'video')
    if video_scene_count > 0:
        print(f"✓ Found {video_scene_count} video scene(s) configured")

    if len(image_files) < len(paragraphs):
        print(f"❌ Error: Not enough images!")
        print(f"   Paragraphs: {len(paragraphs)}")
        print(f"   Images: {len(image_files)}")
        print(f"   Please add {len(paragraphs) - len(image_files)} more images")
        sys.exit(1)

    if len(image_files) > len(paragraphs):
        print(f"⚠️  Warning: More images than paragraphs")
        print(f"   Using first {len(paragraphs)} images")
        image_files = image_files[:len(paragraphs)]

    # =============================================================================
    # STEP 4: TRANSCRIBE AUDIO
    # =============================================================================
    print_step(4, "Transcribing Audio (this may take a few minutes)")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("❌ Error: faster-whisper not installed")
        print("   Please run: pip install faster-whisper")
        sys.exit(1)

    print(f"   Loading {MODEL_SIZE} model...")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)

    print(f"   Transcribing {AUDIO_FILE.name}...")
    segments, info = model.transcribe(str(AUDIO_FILE), word_timestamps=True)

    print(f"✓ Detected language: {info.language}")

    # Collect all words with timestamps
    all_words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                all_words.append({
                    'word': word.word,
                    'start': word.start,
                    'end': word.end
                })

    print(f"✓ Detected {len(all_words)} words")

    # =============================================================================
    # STEP 5: MATCH PARAGRAPHS TO AUDIO
    # =============================================================================
    print_step(5, "Matching Paragraphs to Audio Timing")

    paragraph_times = []
    current_word_idx = 0

    for i, para in enumerate(paragraphs):
        para_normalized = normalize_text(para)
        para_words = para_normalized.split()

        # Find matching position in audio
        best_match_idx = None
        best_match_score = 0

        search_word_count = min(8, len(para_words))
        search_words = para_words[:search_word_count]

        for j in range(current_word_idx, len(all_words) - search_word_count + 1):
            window_words = [normalize_text(all_words[k]['word'])
                          for k in range(j, min(j + search_word_count, len(all_words)))]
            window_text = " ".join(window_words)

            match_count = sum(1 for sw in search_words if sw in window_text)
            score = match_count / len(search_words)

            if score > best_match_score:
                best_match_score = score
                best_match_idx = j

            if score > 0.8:
                break

        if best_match_idx is not None and best_match_score > 0.5:
            start_time = all_words[best_match_idx]['start']

            # Calculate end time
            para_word_count = len(para_words)
            end_word_idx = min(best_match_idx + para_word_count, len(all_words) - 1)

            if end_word_idx < len(all_words):
                end_time = all_words[end_word_idx]['end']
            else:
                end_time = all_words[-1]['end']

            paragraph_times.append({
                'paragraph_num': i + 1,
                'text': para,
                'start': start_time,
                'end': end_time,
                'match_score': best_match_score
            })

            current_word_idx = end_word_idx
            print(f"   Para {i+1:3d}: {start_time:6.2f}s - {end_time:6.2f}s (score: {best_match_score:.2f})")
        else:
            print(f"   ⚠️  Para {i+1:3d}: Could not match (score: {best_match_score:.2f})")

    print(f"✓ Matched {len(paragraph_times)}/{len(paragraphs)} paragraphs")

    if len(paragraph_times) < len(paragraphs):
        print("⚠️  Warning: Some paragraphs could not be matched")
        print("   The video will only include matched paragraphs")

    # =============================================================================
    # STEP 6: ADJUST TIMINGS FOR PERFECT SYNC
    # =============================================================================
    print_step(6, "Adjusting Timings for Perfect Synchronization")

    adjusted_timings = []
    for i, timing in enumerate(paragraph_times):
        start_time = timing['start']

        # End time = start of next paragraph (for perfect sync)
        if i < len(paragraph_times) - 1:
            end_time = paragraph_times[i + 1]['start']
        else:
            end_time = timing['end']

        adjusted_timings.append({
            'paragraph_num': timing['paragraph_num'],
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time,
            'text': timing['text'],
            'match_score': timing['match_score']
        })

    total_duration = adjusted_timings[-1]['end'] if adjusted_timings else 0
    print(f"✓ Total video duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")

    # =============================================================================
    # STEP 7: CREATE SUBTITLE FILES
    # =============================================================================
    print_step(7, "Creating Subtitle Files")
    print(f"   Caption style: {CAPTION_STYLE}")

    if CAPTION_STYLE == 'none':
        print("   Skipping subtitle generation (no captions mode)")
    else:
        # Create standard SRT file (for external use)
        with open(SRT_FILE, 'w', encoding='utf-8') as f:
            for i, timing in enumerate(adjusted_timings):
                f.write(f"{i + 1}\n")
                f.write(f"{format_srt_time(timing['start'])} --> {format_srt_time(timing['end'])}\n")
                text = timing['text'].upper() if CAPTION_STYLE == 'bold_caps' else timing['text']
                f.write(f"{text}\n")
                f.write("\n")

        print(f"✓ Created: {SRT_FILE.name}")

        # Get video dimensions for ASS subtitle generation
        # Check video sources first, then images, then default
        video_width, video_height = None, None

        # Try to get resolution from first video in scene config
        for scene_key, scene_info in scene_config.items():
            if scene_info.get('type') == 'video':
                video_path = scene_info.get('path', '')
                if video_path:
                    video_file = Path(video_path)
                    if not video_file.is_absolute():
                        video_file = PROJECT_ROOT / video_path
                    if video_file.exists():
                        video_width, video_height = get_video_resolution(video_file)
                        if video_width and video_height:
                            break

        # Fall back to image dimensions
        if not video_width or not video_height:
            if image_files:
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height',
                    '-of', 'csv=p=0',
                    str(image_files[0])
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    video_width, video_height = map(int, result.stdout.strip().split(','))

        # Final fallback to 1920x1080
        if not video_width or not video_height:
            video_width, video_height = 1920, 1080

        # Create ASS subtitle file based on style
        if CAPTION_STYLE == 'bold_caps':
            print("   Generating bold CAPS captions with word highlighting...")
            ass_content = generate_bold_caps_captions(all_words, font_path, video_width, video_height)
            style_desc = "bold CAPS with word highlighting"
        else:  # default
            print("   Generating word-level captions with highlighting...")
            ass_content = generate_word_captions(all_words, font_path, video_width, video_height)
            style_desc = "word-by-word highlighting"

        with open(ASS_FILE, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        print(f"✓ Created: {ASS_FILE.name} ({style_desc})")

    # =============================================================================
    # STEP 8: SAVE TIMING DATA
    # =============================================================================
    print_step(8, "Saving Timing Data")

    # JSON format
    with open(TIMING_JSON, 'w', encoding='utf-8') as f:
        json.dump(adjusted_timings, f, indent=2)

    print(f"✓ Created: {TIMING_JSON.name}")

    # Human-readable format
    with open(TIMING_TXT, 'w', encoding='utf-8') as f:
        for timing in adjusted_timings:
            f.write(f"Paragraph {timing['paragraph_num']}\n")
            f.write(f"Time: {timing['start']:.2f}s - {timing['end']:.2f}s ")
            f.write(f"(duration: {timing['duration']:.2f}s, score: {timing['match_score']:.2f})\n")
            f.write(f"Text: {timing['text']}\n")
            f.write("-" * 80 + "\n")

    print(f"✓ Created: {TIMING_TXT.name}")

    # =============================================================================
    # STEP 9: CREATE VIDEO
    # =============================================================================
    print_step(9, "Creating Video (this will take several minutes)")

    # Get resolution from video sources first (if any), then images, then default
    detected_width, detected_height = None, None

    # Check if any scene uses video - get resolution from first video
    for scene_key, scene_info in scene_config.items():
        if scene_info.get('type') == 'video':
            video_path = scene_info.get('path', '')
            if video_path:
                video_file = Path(video_path)
                if not video_file.is_absolute():
                    video_file = PROJECT_ROOT / video_path
                if video_file.exists():
                    detected_width, detected_height = get_video_resolution(video_file)
                    if detected_width and detected_height:
                        print(f"   Video dimensions: {detected_width}x{detected_height}")
                        break

    # Fall back to image dimensions if no video resolution found
    if not detected_width or not detected_height:
        if image_files:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(image_files[0])
            ], capture_output=True, text=True)

            if result.returncode == 0:
                detected_width, detected_height = map(int, result.stdout.strip().split(','))
                print(f"   Image dimensions: {detected_width}x{detected_height}")

    # Final fallback to 1920x1080
    if not detected_width or not detected_height:
        detected_width, detected_height = 1920, 1080
        print(f"   Using default dimensions: {detected_width}x{detected_height}")

    # Use configured resolution or detected resolution
    width = OUTPUT_WIDTH if OUTPUT_WIDTH else detected_width
    height = OUTPUT_HEIGHT if OUTPUT_HEIGHT else detected_height

    print(f"   Assembling {len(adjusted_timings)} scenes with smooth transitions...")
    print(f"   Transition duration: {TRANSITION_DURATION}s fade effect")
    print(f"   Captions: Word-by-word highlighting with {FONT_NAME} font")

    # Create individual video clips with fade effects
    temp_clips = []
    for i in range(len(adjusted_timings)):
        if i < len(image_files):
            clip_path = OUTPUT_DIR / f"clip_{i:03d}.mp4"
            temp_clips.append(clip_path)

            duration = adjusted_timings[i]['duration']
            paragraph_num = adjusted_timings[i]['paragraph_num']

            # Check if this scene should use a video instead of image
            scene_key = str(paragraph_num)
            scene_info = scene_config.get(scene_key, {})
            use_video = scene_info.get('type') == 'video'
            video_path = scene_info.get('path', '')

            # Build fade filter
            # First clip: fade in at start
            # Middle clips: fade in at start, fade out at end
            # Last clip: fade out at end
            if i == 0 and len(adjusted_timings) > 1:
                # First clip - fade in only
                fade_filter = f"fade=t=in:st=0:d={TRANSITION_DURATION}"
            elif i == len(adjusted_timings) - 1 and i > 0:
                # Last clip - fade out only
                fade_filter = f"fade=t=out:st={duration - TRANSITION_DURATION}:d={TRANSITION_DURATION}"
            elif len(adjusted_timings) > 1:
                # Middle clips - fade in and out
                fade_filter = f"fade=t=in:st=0:d={TRANSITION_DURATION},fade=t=out:st={duration - TRANSITION_DURATION}:d={TRANSITION_DURATION}"
            else:
                # Single clip - no fade
                fade_filter = "null"

            if use_video and video_path:
                # Use video clip
                video_file = Path(video_path)
                if not video_file.is_absolute():
                    video_file = PROJECT_ROOT / video_path

                if not video_file.exists():
                    print(f"   ⚠️  Video not found for scene {paragraph_num}: {video_path}")
                    print(f"      Falling back to image")
                    use_video = False
                else:
                    print(f"   Scene {paragraph_num}: Using video clip ({video_file.name})")

            if use_video and video_path and video_file.exists():
                # Get actual video duration
                video_duration = get_video_duration(video_file)

                if video_duration is None:
                    print(f"   ⚠️  Could not detect video duration for scene {paragraph_num}")
                    print(f"      Falling back to image")
                    use_video = False
                elif video_duration < duration:
                    # Video is shorter than required - freeze last frame with smooth zoom-in effect
                    remaining_duration = duration - video_duration
                    print(f"   Scene {paragraph_num}: Video is {video_duration:.2f}s, adding {remaining_duration:.2f}s zoom effect on last frame")

                    # Calculate zoom parameters for ultra-smooth zoom
                    # Using subtle 10% zoom for professional look
                    target_zoom = 1.10
                    zoom_amount = target_zoom - 1.0
                    # Use 60fps for maximum smoothness
                    zoom_fps = 60
                    output_frames = int(remaining_duration * zoom_fps) + 1

                    # Strategy: Play video, then zoom-in on last frame for remaining time
                    # Get last frame by trimming near end, reversing, and taking first frame
                    last_frame_start = max(0, video_duration - 0.5)

                    # Ultra-smooth zoom using linear interpolation (simpler = more stable)
                    # Small zoom amount + high fps + linear = buttery smooth
                    zoom_per_frame = zoom_amount / max(output_frames, 1)
                    zoom_expr = f"1.0+{zoom_per_frame:.10f}*on"

                    # Scale up 4x for maximum quality interpolation
                    upscale_w = width * 4
                    upscale_h = height * 4

                    filter_complex = (
                        # Scale and pad the input video, split into two streams
                        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                        f"setsar=1,fps={zoom_fps},split=2[main][forlast];"
                        # Trim the main video to its actual duration
                        f"[main]trim=0:{video_duration},setpts=PTS-STARTPTS,format=yuv420p[trimmed];"
                        # Get the actual last frame: use select to get exactly one frame
                        f"[forlast]trim=start={last_frame_start},setpts=PTS-STARTPTS,"
                        f"reverse,select='eq(n\\,0)',setpts=PTS-STARTPTS,"
                        # Scale up 4x with high-quality bicubic for smooth zoom interpolation
                        f"scale={upscale_w}:{upscale_h}:flags=bicubic,"
                        # Apply smooth linear zoom - simpler expression = no floating point jitter
                        # Use floor() for consistent pixel positioning
                        f"zoompan=z='{zoom_expr}':"
                        f"x='floor((iw-iw/zoom)/2)':y='floor((ih-ih/zoom)/2)':"
                        f"d={output_frames}:s={width}x{height}:fps={zoom_fps},"
                        f"format=yuv420p[zoomed];"
                        # Concatenate original video with zoomed last frame, then apply fade
                        f"[trimmed][zoomed]concat=n=2:v=1:a=0,{fade_filter}"
                    )

                    cmd = [
                        'ffmpeg', '-y',
                        '-i', str(video_file),
                        '-filter_complex', filter_complex,
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-crf', '18',
                        '-pix_fmt', 'yuv420p',
                        '-an',
                        str(clip_path)
                    ]
                else:
                    # Video is long enough - trim to duration
                    print(f"   Scene {paragraph_num}: Using video clip ({video_file.name}), trimming to {duration:.2f}s")

                    filter_complex = (
                        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                        f"setsar=1,fps=25,{fade_filter}"
                    )

                    # Create clip from video (trim to duration)
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', str(video_file),
                        '-t', str(duration),
                        '-vf', filter_complex,
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-crf', '18',
                        '-pix_fmt', 'yuv420p',
                        '-an',  # Remove audio from video clip
                        str(clip_path)
                    ]
            else:
                # Complete filter with scaling and fade (for images)
                filter_complex = (
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                    f"setsar=1,fps=25,{fade_filter}"
                )

                # Create individual clip from image
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-t', str(duration),
                    '-i', str(image_files[i]),
                    '-vf', filter_complex,
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Fast preset for temp clips
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                    str(clip_path)
                ]

            subprocess.run(cmd, capture_output=True, check=True)
    
    print(f"   Created {len(temp_clips)} video clips with fade transitions")
    
    # Create concat file
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, 'w') as f:
        for clip in temp_clips:
            f.write(f"file '{clip.absolute()}'\n")
    
    # Concatenate all clips, add audio, and burn in captions
    # First create video without subtitles
    temp_video = OUTPUT_DIR / "temp_video_no_subs.mp4"

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-i', str(AUDIO_FILE),
        '-c:v', 'libx264',
        '-preset', VIDEO_PRESET,
        '-crf', str(VIDEO_CRF),
        '-c:a', 'aac',
        '-b:a', AUDIO_BITRATE,
        '-shortest',
        str(temp_video)
    ]

    print(f"   Encoding video (preset: {VIDEO_PRESET}, quality: CRF {VIDEO_CRF})...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Error creating video:")
        print(result.stderr[-1000:] if result.stderr else "Unknown error")
        sys.exit(1)

    # Check for per-scene transition sounds and mix them at appropriate times
    if TRANSITION_SOUNDS_DIR.exists():
        # Find all transition sound files (named by position: 0.mp3, 1.wav, etc.)
        sound_files = list(TRANSITION_SOUNDS_DIR.glob("*.mp3")) + list(TRANSITION_SOUNDS_DIR.glob("*.wav"))

        if sound_files:
            print("   Mixing per-scene transition sound effects...")

            # Build mapping of position -> (sound_file, timestamp)
            transition_sounds = []
            for sound_file in sound_files:
                try:
                    position = int(sound_file.stem)  # e.g., "0" from "0.mp3"

                    # Calculate timestamp for this position
                    if position == 0:
                        # Intro sound at start of video
                        timestamp = 0
                    elif position <= len(adjusted_timings) - 1:
                        # Sound between scenes: plays at start of scene N (position N)
                        # Centered around the transition
                        timestamp = adjusted_timings[position]['start'] - (TRANSITION_SOUND_DURATION / 2)
                        if timestamp < 0:
                            timestamp = 0
                    else:
                        continue  # Skip invalid positions

                    transition_sounds.append((position, sound_file, timestamp))
                except ValueError:
                    continue  # Skip files that aren't numbered

            if transition_sounds:
                # Sort by position
                transition_sounds.sort(key=lambda x: x[0])
                print(f"   Found {len(transition_sounds)} transition sound(s)")

                # Create a temporary video with mixed transition sounds
                temp_video_with_transitions = OUTPUT_DIR / "temp_video_with_transitions.mp4"

                # Build FFmpeg command with multiple audio inputs
                # Input 0 = video, Input 1+ = transition sounds
                cmd = [FFMPEG_PATH, '-y', '-i', str(temp_video)]

                # Add each transition sound as an input
                for _, sound_file, _ in transition_sounds:
                    cmd.extend(['-i', str(sound_file)])

                # Build filter complex
                filter_parts = []

                # Process each transition sound
                for i, (position, _, timestamp) in enumerate(transition_sounds):
                    input_idx = i + 1  # Video is input 0
                    delay_ms = int(timestamp * 1000)
                    # Trim, boost volume, and delay each sound
                    filter_parts.append(
                        f"[{input_idx}:a]atrim=0:{TRANSITION_SOUND_DURATION},"
                        f"asetpts=PTS-STARTPTS,volume=1.5,adelay={delay_ms}|{delay_ms}[trans{i}]"
                    )

                # Mix all sounds with original audio (normalize=0 prevents volume reduction)
                mix_inputs = "[0:a]" + "".join(f"[trans{i}]" for i in range(len(transition_sounds)))
                filter_parts.append(
                    f"{mix_inputs}amix=inputs={len(transition_sounds) + 1}:"
                    f"duration=first:dropout_transition=0:normalize=0[aout]"
                )

                filter_complex = ";".join(filter_parts)

                cmd.extend([
                    '-filter_complex', filter_complex,
                    '-map', '0:v',
                    '-map', '[aout]',
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', AUDIO_BITRATE,
                    str(temp_video_with_transitions)
                ])

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✓ Added {len(transition_sounds)} transition sound(s)")
                    # Replace temp_video with the one containing transition sounds
                    temp_video.unlink()
                    temp_video_with_transitions.rename(temp_video)
                else:
                    print("⚠️  Warning: Could not add transition sounds")
                    if result.stderr:
                        error_lines = result.stderr.strip().split('\n')[-3:]
                        for line in error_lines:
                            print(f"   {line}")
                    # Continue without transition sounds
                    if temp_video_with_transitions.exists():
                        temp_video_with_transitions.unlink()

    # Now burn in the subtitles (unless no captions mode)
    if CAPTION_STYLE == 'none':
        print("   Skipping caption burning (no captions mode)")
        # Just rename temp video to final output
        shutil.move(str(temp_video), str(OUTPUT_VIDEO))
        print("✓ Video created without captions")
    else:
        print("   Burning captions into video...")

        # Build the subtitle filter - FFmpeg ASS filter with proper escaping
        # For the ASS filter, colons in paths need to be escaped with backslash
        def escape_ffmpeg_path(path):
            """Escape path for FFmpeg filter syntax"""
            p = str(path)
            # Escape colons (required for macOS paths like /Users/...)
            # The colon is used as option separator in FFmpeg filters
            p = p.replace(':', '\\:')
            return p

        ass_path_escaped = escape_ffmpeg_path(ASS_FILE)

        # Add font directory to FFmpeg if we have a custom font
        if font_path and font_path.exists():
            font_dir_escaped = escape_ffmpeg_path(FONTS_DIR)
            subtitle_filter = f"ass={ass_path_escaped}:fontsdir={font_dir_escaped}"
        else:
            subtitle_filter = f"ass={ass_path_escaped}"

        # Use ffmpeg-full for subtitle burning (has libass support)
        cmd = [
            FFMPEG_PATH, '-y',
            '-i', str(temp_video),
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', VIDEO_PRESET,
            '-crf', str(VIDEO_CRF),
            '-c:a', 'copy',
            str(OUTPUT_VIDEO)
        ]

        print(f"   Using FFmpeg: {FFMPEG_PATH}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("⚠️  Warning: Could not burn captions (FFmpeg subtitle filter issue)")
            if result.stderr:
                # Print last part of error for debugging
                error_lines = result.stderr.strip().split('\n')[-5:]
                for line in error_lines:
                    print(f"   {line}")
            print("   Falling back to video without burned-in captions...")
            # Use the temp video without subtitles as the final output
            shutil.move(str(temp_video), str(OUTPUT_VIDEO))
        else:
            print("✓ Captions burned into video successfully")
            # Cleanup temp video
            if temp_video.exists():
                temp_video.unlink()

    # Cleanup temporary files
    concat_file.unlink()
    for clip in temp_clips:
        clip.unlink()

    # =============================================================================
    # COMPLETION
    # =============================================================================
    print_header("✅ VIDEO CREATION COMPLETE!")

    file_size = OUTPUT_VIDEO.stat().st_size / (1024 * 1024)

    print(f"\n📹 Output Video:")
    print(f"   Location: {OUTPUT_VIDEO}")
    print(f"   Size: {file_size:.2f} MB")
    print(f"   Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
    print(f"   Resolution: {width}x{height}")
    print(f"   Scenes: {len(adjusted_timings)}")

    print(f"\n📝 Additional Files:")
    if CAPTION_STYLE != 'none':
        print(f"   Subtitles (SRT): {SRT_FILE}")
        print(f"   Subtitles (ASS): {ASS_FILE}")
    print(f"   Timing data: {TIMING_JSON}")
    print(f"   Timing info: {TIMING_TXT}")

    print(f"\n🎬 Caption Features:")
    if CAPTION_STYLE == 'none':
        print(f"   Style: No captions")
    elif CAPTION_STYLE == 'bold_caps':
        print(f"   Font: {FONT_NAME} (Google Font)")
        print(f"   Style: Bold CAPS - all uppercase with yellow word highlighting")
    else:
        print(f"   Font: {FONT_NAME} (Google Font)")
        print(f"   Style: White text with yellow word highlighting")

    print(f"\n✨ Your video is ready to use!")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
