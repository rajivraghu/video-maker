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
import re
import zipfile

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

# Get project root
PROJECT_ROOT = Path(__file__).parent

# FFmpeg path - use ffmpeg-full if available (has libass support for captions)
FFMPEG_FULL_PATH = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFMPEG_PATH = FFMPEG_FULL_PATH if Path(FFMPEG_FULL_PATH).exists() else "ffmpeg"

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


# ============================================
# Regional Mix Caption Helpers
# ============================================
def transcribe_audio_to_words(audio_path):
    """Transcribe audio file and return word-level timestamps in uppercase"""
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, word_timestamps=True, language="en")

    all_words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                all_words.append({
                    'word': word.word.strip().upper(),  # Convert to uppercase
                    'start': word.start,
                    'end': word.end
                })

    return all_words


# ============================================
# Cue Matching Algorithm for Split Audio
# ============================================

# --- Number-to-words conversion ---
_ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
         'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
         'seventeen', 'eighteen', 'nineteen']
_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
_ORDINAL_SUFFIX = {'1': 'first', '2': 'second', '3': 'third', '5': 'fifth',
                   '8': 'eighth', '9': 'ninth', '12': 'twelfth'}


def _int_to_words(n):
    """Convert integer 0-99999 to English words."""
    if n == 0:
        return 'zero'
    if n < 0:
        return 'negative ' + _int_to_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ((' ' + _ONES[n % 10]) if n % 10 else '')
    if n < 1000:
        return _ONES[n // 100] + ' hundred' + ((' ' + _int_to_words(n % 100)) if n % 100 else '')
    if n < 100000:
        return _int_to_words(n // 1000) + ' thousand' + ((' ' + _int_to_words(n % 1000)) if n % 1000 else '')
    return str(n)


def _ordinal_to_words(n):
    """Convert integer to ordinal words: 1->first, 2->second, 21->twenty first."""
    if n <= 0:
        return _int_to_words(n)
    # Special ordinals
    special = {1: 'first', 2: 'second', 3: 'third', 5: 'fifth',
               8: 'eighth', 9: 'ninth', 12: 'twelfth'}
    if n in special:
        return special[n]
    if n < 20:
        base = _ONES[n]
        if base.endswith('e'):
            return base[:-1] + 'th'
        return base + 'th'
    if n < 100 and n % 10 == 0:
        base = _TENS[n // 10]
        return base[:-1] + 'ieth'  # twenty -> twentieth
    if n < 100:
        return _TENS[n // 10] + ' ' + _ordinal_to_words(n % 10)
    # For larger, just do cardinal + th
    return _int_to_words(n) + 'th'


def expand_numbers_in_text(text):
    """
    Expand number tokens in text to their word forms.
    '3 cats' -> 'three cats'
    '21st place' -> 'twenty first place'
    'item 100' -> 'item one hundred'
    """
    result_words = []
    for token in text.split():
        stripped = token.strip('.,!?;:\'"()-[]{}')
        lower = stripped.lower()

        # Ordinals: 1st, 2nd, 3rd, 4th, 21st, etc.
        ordinal_match = re.match(r'^(\d+)(st|nd|rd|th)$', lower)
        if ordinal_match:
            try:
                n = int(ordinal_match.group(1))
                result_words.append(_ordinal_to_words(n))
                continue
            except ValueError:
                pass

        # Pure numbers: 3, 21, 100, etc.
        if stripped.isdigit():
            try:
                n = int(stripped)
                result_words.append(_int_to_words(n))
                continue
            except ValueError:
                pass

        # Decimal numbers: 3.5 -> three point five
        decimal_match = re.match(r'^(\d+)\.(\d+)$', stripped)
        if decimal_match:
            try:
                whole = int(decimal_match.group(1))
                frac_digits = decimal_match.group(2)
                parts = [_int_to_words(whole), 'point']
                for d in frac_digits:
                    parts.append(_int_to_words(int(d)))
                result_words.append(' '.join(parts))
                continue
            except ValueError:
                pass

        result_words.append(token)

    return ' '.join(result_words)


# --- Word normalization and comparison ---

def normalize_word(w):
    """Normalize a word for matching: lowercase, strip punctuation."""
    return re.sub(r'[^\w]', '', w.lower())


# Build reverse lookup: word -> number string
_WORD_TO_NUM = {}
for _i in range(200):
    for _w in _int_to_words(_i).split():
        if _w:
            _WORD_TO_NUM[_w] = True  # just mark as a number-related word
_NUM_TO_WORDS = {}
for _i in range(200):
    _NUM_TO_WORDS[str(_i)] = _int_to_words(_i)


def words_similar(a, b):
    """
    Check if two normalized words match, considering:
    - Exact match
    - Number equivalence (3 == three, 21 == twenty one handled via expansion)
    - Whisper quirks (prefix match, 1 char diff)
    """
    if not a or not b:
        return False
    if a == b:
        return True

    # Number equivalence: "3" vs "three" etc.
    if a in _NUM_TO_WORDS:
        # a is a digit string, check if b matches any of its word forms
        word_forms = _NUM_TO_WORDS[a].split()
        if b in word_forms:
            return True
    if b in _NUM_TO_WORDS:
        word_forms = _NUM_TO_WORDS[b].split()
        if a in word_forms:
            return True

    # Allow single char difference for words 4+ chars
    if len(a) >= 4 and len(b) >= 4 and len(a) == len(b):
        diffs = sum(1 for x, y in zip(a, b) if x != y)
        if diffs <= 1:
            return True

    # Prefix match (e.g., "goin" vs "going", "wanna" vs "want")
    if len(a) >= 3 and len(b) >= 3:
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        if longer.startswith(shorter) and len(longer) - len(shorter) <= 2:
            return True

    return False


# --- Global sequence alignment ---

def align_sequences(cue_words, transcript_words):
    """
    Global alignment of flattened cue words against transcript words.
    Uses two-pointer with wide adaptive lookahead.

    Since cues ARE the script, the sequences are nearly identical.
    Returns dict: cue_word_index -> transcript_word_index (or missing if unmatched).
    """
    n = len(cue_words)
    m = len(transcript_words)
    alignment = {}

    c = 0  # cue pointer
    t = 0  # transcript pointer
    MAX_LOOK = 15  # wide lookahead to recover from misalignments

    while c < n and t < m:
        # Direct match - most common case
        if words_similar(cue_words[c], transcript_words[t]):
            alignment[c] = t
            c += 1
            t += 1
            continue

        # Mismatch: look ahead in both sequences to find where they re-sync

        # Option A: skip transcript words (Whisper added extra words)
        t_skip = -1
        for dt in range(1, min(MAX_LOOK + 1, m - t)):
            if words_similar(cue_words[c], transcript_words[t + dt]):
                t_skip = dt
                break

        # Option B: skip cue words (Whisper missed/merged cue words)
        c_skip = -1
        for dc in range(1, min(MAX_LOOK + 1, n - c)):
            if words_similar(cue_words[c + dc], transcript_words[t]):
                c_skip = dc
                break

        # Option C: skip both equally (substitution then re-sync)
        d_skip = -1
        for d in range(1, min(MAX_LOOK + 1, min(n - c, m - t))):
            if words_similar(cue_words[c + d], transcript_words[t + d]):
                d_skip = d
                break

        # Pick cheapest recovery
        best_action = None
        best_cost = MAX_LOOK + 1

        if t_skip >= 0 and t_skip < best_cost:
            best_cost = t_skip
            best_action = ('skip_t', t_skip)
        if c_skip >= 0 and c_skip < best_cost:
            best_cost = c_skip
            best_action = ('skip_c', c_skip)
        if d_skip >= 0 and d_skip < best_cost:
            best_cost = d_skip
            best_action = ('skip_both', d_skip)

        if best_action:
            action, skip = best_action
            if action == 'skip_t':
                # Extra words in transcript - skip them
                t += skip
                # Now match
                alignment[c] = t
                c += 1
                t += 1
            elif action == 'skip_c':
                # Whisper missed cue words - assign them to current transcript region
                for i in range(skip):
                    alignment[c + i] = t  # approximate position
                c += skip
                alignment[c] = t
                c += 1
                t += 1
            else:  # skip_both
                # Words were substituted - pair them up positionally
                for i in range(skip):
                    alignment[c + i] = t + i
                c += skip
                t += skip
                alignment[c] = t
                c += 1
                t += 1
        else:
            # No re-sync found within lookahead - force pair and move on
            alignment[c] = t
            c += 1
            t += 1

    # Handle remaining cue words (transcript ran out)
    if c < n and m > 0:
        for i in range(c, n):
            alignment[i] = m - 1  # assign to last transcript word

    return alignment


def match_cues_to_transcript(cue_lines, words):
    """
    Match cue lines to transcript words using GLOBAL alignment.

    Approach:
    1. Expand numbers in ALL cues to word form (3 -> three, 1st -> first)
    2. Flatten all expanded cue words into one sequence, tracking cue boundaries
    3. Normalize transcript words
    4. Globally align the flat cue sequence to the transcript (two-pointer)
    5. Use cue boundaries to extract start/end timestamps per cue
    6. Any unmatched cues get interpolated from neighbors (no failures possible)
    """
    # Step 1: Expand numbers in cue lines
    expanded_cues = []
    for line in cue_lines:
        expanded = expand_numbers_in_text(line)
        expanded_cues.append(expanded)

    # Step 2: Flatten cue words with boundary tracking
    flat_cue_words = []
    cue_ranges = []  # (start_idx, end_idx) in flat_cue_words for each cue
    for idx, line in enumerate(expanded_cues):
        words_in_cue = [normalize_word(w) for w in line.split() if normalize_word(w)]
        start = len(flat_cue_words)
        flat_cue_words.extend(words_in_cue)
        end = len(flat_cue_words) - 1
        cue_ranges.append((start, end))

    # Step 3: Normalize transcript words
    transcript_norm = [normalize_word(w['word']) for w in words]

    # Step 4: Global alignment
    alignment = align_sequences(flat_cue_words, transcript_norm)

    # Step 5: Extract per-cue results from alignment
    results = []
    for cue_idx, (cue_start, cue_end) in enumerate(cue_ranges):
        # Get all transcript indices this cue's words mapped to
        t_indices = []
        for c_idx in range(cue_start, cue_end + 1):
            if c_idx in alignment:
                t_indices.append(alignment[c_idx])

        if t_indices:
            first_t = min(t_indices)
            last_t = max(t_indices)
            # Score: how many cue words got aligned
            cue_word_count = cue_end - cue_start + 1
            aligned_count = len(t_indices)
            score = aligned_count / cue_word_count

            results.append({
                'cue_index': cue_idx,
                'cue_text': cue_lines[cue_idx],
                'status': 'matched' if score >= 0.5 else 'partial',
                'matched_text': ' '.join(words[i]['word'] for i in range(first_t, last_t + 1)),
                'start': words[first_t]['start'],
                'end': words[last_t]['end'],
                'score': round(score, 3)
            })
        else:
            results.append({
                'cue_index': cue_idx,
                'cue_text': cue_lines[cue_idx],
                'status': 'failed',
                'matched_text': '',
                'start': 0,
                'end': 0,
                'score': 0
            })

    # Step 6: Fix any failed cues by interpolating from neighbors
    for i, r in enumerate(results):
        if r['status'] == 'failed':
            prev_end = 0
            next_start = words[-1]['end'] if words else 0
            for j in range(i - 1, -1, -1):
                if results[j]['status'] != 'failed':
                    prev_end = results[j]['end']
                    break
            for j in range(i + 1, len(results)):
                if results[j]['status'] != 'failed':
                    next_start = results[j]['start']
                    break
            if prev_end > 0 or next_start > 0:
                results[i]['start'] = prev_end
                results[i]['end'] = next_start
                results[i]['status'] = 'partial'
                results[i]['matched_text'] = '(interpolated)'
                results[i]['score'] = 0.5

    return results


def format_ass_time(seconds):
    """Convert seconds to ASS timestamp format (H:MM:SS.CS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def generate_ass_captions(words, output_path, video_width=1920, video_height=1080):
    """Generate ASS subtitle file with karaoke-style word highlighting (ALL CAPS, bold yellow)"""

    # Font and style settings
    FONT_NAME = "Arial"
    FONT_SIZE = 52
    FONT_COLOR = "&H00FFFFFF"        # White (BGR format)
    OUTLINE_COLOR = "&H00000000"     # Black outline
    OUTLINE_WIDTH = 4
    SHADOW_DEPTH = 2
    MARGIN_BOTTOM = 60
    CAPTION_ALIGNMENT = 2            # Bottom center
    WORDS_PER_LINE = 5

    # Create ASS header with bold styling
    ass_content = f"""[Script Info]
Title: Regional Mix Captions
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

    # Group words into chunks
    chunks = []
    for i in range(0, len(words), WORDS_PER_LINE):
        chunk = words[i:i + WORDS_PER_LINE]
        chunks.append(chunk)

    # Generate dialogue events with karaoke effect
    for chunk in chunks:
        # Create one event per word in the chunk (for karaoke effect)
        for word_idx, current_word in enumerate(chunk):
            start_time = format_ass_time(current_word['start'])
            end_time = format_ass_time(current_word['end'])

            # Build caption with current word highlighted in light yellow
            caption_parts = []
            for j, w in enumerate(chunk):
                word_text = w['word']
                if j == word_idx:
                    # Current word - light/bright yellow (BGR: 80FFFF = light yellow)
                    caption_parts.append(f"{{\\c&H80FFFF&}}{word_text}{{\\c&HFFFFFF&}}")
                else:
                    # Other words - white
                    caption_parts.append(word_text)

            caption_text = " ".join(caption_parts)
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{caption_text}\n"

    # Write ASS file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)

    return output_path


@app.route('/api/regional-mix', methods=['POST'])
def regional_mix():
    """Handle Regional Mix video generation request with images and videos"""
    try:
        # Extract pair info (includes media type)
        pair_info_json = request.form.get('pair_info', '[]')
        pair_info = json.loads(pair_info_json)

        # Get no_transitions setting
        no_transitions = request.form.get('no_transitions', 'false') == 'true'

        # Get captions setting
        captions_enabled = request.form.get('captions', 'true') == 'true'

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

                    # If captions enabled, transcribe audio and generate ASS file
                    ass_file = None
                    if captions_enabled:
                        try:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  Transcribing audio for pair {num}...'})}\n\n"

                            # Transcribe audio
                            words = transcribe_audio_to_words(aud_path)

                            if words:
                                # Generate ASS subtitle file
                                ass_file = str(clip_dir / f'subtitle_{num}.ass')
                                generate_ass_captions(words, ass_file)

                                yield f"data: {json.dumps({'type': 'log', 'message': f'  ✓ Generated captions ({len(words)} words)'})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ No words detected in audio'})}\n\n"

                        except Exception as caption_error:
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Caption generation failed: {str(caption_error)}'})}\n\n"
                            ass_file = None

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
                                FFMPEG_PATH, '-y',
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
                                FFMPEG_PATH, '-y',
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
                        total_frames = int(audio_duration * fps) + 1

                        yield f"data: {json.dumps({'type': 'log', 'message': f'  Creating image clip at {fps}fps for {audio_duration:.3f}s'})}\n\n"

                        # Smooth subtle zoom-in effect (3% total zoom over clip duration)
                        # Using high source resolution + smooth interpolation
                        zoom_start = 1.0
                        zoom_end = 1.03

                        # Smooth zoom expression - interpolates over total frames
                        zoom_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*(on/{total_frames})"

                        # Build zoompan filter with smooth settings
                        # - Scale source to 8K for maximum interpolation quality
                        # - Use bilinear for smooth sub-pixel rendering
                        # - Center the zoom point
                        zoom_filter = (
                            f"scale=7680:-1:flags=bilinear,"
                            f"zoompan=z='{zoom_expr}':"
                            f"x='iw/2-(iw/zoom/2)':"
                            f"y='ih/2-(ih/zoom/2)':"
                            f"d={total_frames}:"
                            f"s=1920x1080:"
                            f"fps={fps}"
                        )

                        # Build video filter - with or without fade
                        if no_transitions:
                            vf_filter = zoom_filter
                        else:
                            vf_filter = f'{zoom_filter},fade=t=in:st=0:d={fade_duration},fade=t=out:st={audio_duration-fade_duration}:d={fade_duration}'

                        # Use zoompan to create the clip
                        ffmpeg_cmd = [
                            FFMPEG_PATH, '-y',
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

                    process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

                    if process.returncode != 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  FFmpeg error: {process.stderr}', 'level': 'error'})}\n\n"
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to create clip for pair {num}'})}\n\n"
                        return

                    # Add captions in second pass if ASS file exists
                    if ass_file and os.path.exists(ass_file) and os.path.exists(clip_path):
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  Burning captions into clip...'})}\n\n"

                        clip_with_subs = str(clip_dir / f'clip_{num}_subs.mp4')

                        # Escape the ASS path for FFmpeg filter (colons need escaping)
                        ass_path_escaped = ass_file.replace(':', '\\:')

                        subtitle_cmd = [
                            FFMPEG_PATH, '-y',
                            '-i', clip_path,
                            '-vf', f'ass={ass_path_escaped}',
                            '-c:v', 'libx264',
                            '-preset', 'medium',
                            '-crf', '18',
                            '-c:a', 'copy',
                            clip_with_subs
                        ]

                        sub_process = subprocess.run(subtitle_cmd, capture_output=True, text=True)

                        if sub_process.returncode == 0:
                            # Replace original clip with captioned version
                            os.remove(clip_path)
                            os.rename(clip_with_subs, clip_path)
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  ✓ Captions burned successfully'})}\n\n"
                        else:
                            # Log error but continue without captions
                            stderr_lines = sub_process.stderr.split('\n')
                            error_lines = [l for l in stderr_lines if 'error' in l.lower() or 'failed' in l.lower()]
                            error_msg = '; '.join(error_lines[-3:]) if error_lines else 'Unknown error'
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠ Could not burn captions: {error_msg}'})}\n\n"

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
                    FFMPEG_PATH, '-y',
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

@app.route('/api/transcribe-youtube', methods=['POST'])
def transcribe_youtube():
    """Transcribe YouTube video audio to English text"""
    try:
        data = request.json
        youtube_url = data.get('url')
        source_language = data.get('language', 'ta')  # 'ta' for Tamil, 'te' for Telugu

        def generate():
            try:
                from pytubefix import YouTube
                from faster_whisper import WhisperModel
                import tempfile
                import shutil

                yield f"data: {json.dumps({'type': 'log', 'message': 'Downloading YouTube audio...'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 10, 'message': 'Downloading audio...'})}\n\n"

                # Create temp directory
                temp_dir = tempfile.mkdtemp()
                video_dir = os.path.join(temp_dir, 'video')
                os.makedirs(video_dir, exist_ok=True)

                try:
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Fetching video information...'})}\n\n"

                    # Download using pytubefix
                    yt = YouTube(youtube_url)
                    video_title = yt.title

                    yield f"data: {json.dumps({'type': 'log', 'message': f'Video: {video_title}'})}\n\n"

                    # Get the audio stream
                    audio_stream = yt.streams.filter(only_audio=True).first()

                    if audio_stream is None:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'No audio stream found for this video'})}\n\n"
                        shutil.rmtree(temp_dir)
                        return

                    yield f"data: {json.dumps({'type': 'log', 'message': f'Downloading audio ({audio_stream.filesize / 1024 / 1024:.1f} MB)...'})}\n\n"

                    # Download the audio
                    downloaded_file = audio_stream.download(output_path=video_dir)

                    # Convert to MP3 using FFmpeg
                    audio_path = os.path.join(temp_dir, 'audio.mp3')
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Converting to MP3...'})}\n\n"

                    ffmpeg_cmd = [
                        FFMPEG_PATH, '-y',
                        '-i', downloaded_file,
                        '-q:a', '5',
                        '-map', 'a',
                        audio_path
                    ]

                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'FFmpeg conversion failed: {result.stderr}'})}\n\n"
                        shutil.rmtree(temp_dir)
                        return

                    yield f"data: {json.dumps({'type': 'log', 'message': '✓ Audio downloaded and converted successfully'})}\n\n"

                except Exception as download_error:
                    error_msg = str(download_error)
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to download YouTube audio: {error_msg}'})}\n\n"
                    shutil.rmtree(temp_dir)
                    return

                yield f"data: {json.dumps({'type': 'log', 'message': '✓ Audio downloaded successfully'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 40, 'message': 'Transcribing audio...'})}\n\n"

                # Initialize Whisper model
                model = WhisperModel("base", device="cpu", compute_type="int8")

                # Transcribe audio
                segments, info = model.transcribe(
                    audio_path,
                    language=source_language,
                    task="translate"  # This translates to English
                )

                yield f"data: {json.dumps({'type': 'log', 'message': f'✓ Detected language: {info.language}'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 70, 'message': 'Processing transcript...'})}\n\n"

                # Collect all segments into clean paragraphs
                transcript_text = ""
                for segment in segments:
                    transcript_text += segment.text.strip() + " "

                # Clean up the transcript
                transcript_text = transcript_text.strip()
                transcript_text = " ".join(transcript_text.split())  # Remove extra whitespace

                yield f"data: {json.dumps({'type': 'log', 'message': '✓ Transcript generated successfully'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 100, 'message': 'Complete!'})}\n\n"

                # Clean up temp files
                shutil.rmtree(temp_dir)

                yield f"data: {json.dumps({'type': 'complete', 'transcript': transcript_text})}\n\n"

            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Split Audio Feature
# ============================================

@app.route('/api/split-audio', methods=['POST'])
def split_audio():
    """Split audio file based on cue text matching"""
    try:
        audio_file = request.files.get('audio')
        cues_file = request.files.get('cues')

        if not audio_file or not cues_file:
            return jsonify({'error': 'Both audio and cues files are required'}), 400

        # Setup directories
        work_dir = PROJECT_ROOT / 'input' / 'split_audio'
        output_dir = PROJECT_ROOT / 'output' / 'split_audio'

        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save files while in request context
        audio_ext = Path(audio_file.filename).suffix or '.mp3'
        audio_path = work_dir / f'input_audio{audio_ext}'
        audio_file.save(str(audio_path))

        cues_path = work_dir / 'cues.txt'
        cues_file.save(str(cues_path))

        with open(cues_path, 'r', encoding='utf-8') as f:
            cue_lines = [line.strip() for line in f.readlines() if line.strip()]

        file_info = {
            'audio_name': audio_file.filename,
            'audio_path': str(audio_path),
            'audio_ext': audio_ext,
            'cue_count': len(cue_lines),
            'cue_lines': cue_lines,
            'output_dir': str(output_dir)
        }

        def generate():
            try:
                audio_name = file_info['audio_name']
                cue_count = file_info['cue_count']
                cue_lines = file_info['cue_lines']
                audio_path_str = file_info['audio_path']
                audio_ext = file_info['audio_ext']
                out_dir = file_info['output_dir']

                yield f"data: {json.dumps({'type': 'log', 'message': f'Audio file: {audio_name}'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': f'Cues loaded: {cue_count} lines'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 5, 'message': 'Files uploaded successfully'})}\n\n"

                # Step 1: Transcribe audio
                yield f"data: {json.dumps({'type': 'log', 'message': 'Transcribing audio with Whisper (this may take a moment)...'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 10, 'message': 'Transcribing audio...'})}\n\n"

                words = transcribe_audio_to_words(audio_path_str)

                yield f"data: {json.dumps({'type': 'log', 'message': f'Transcription complete: {len(words)} words detected'})}\n\n"

                # Log full transcript so user can see what Whisper heard
                full_transcript = ' '.join(w['word'] for w in words)
                yield f"data: {json.dumps({'type': 'log', 'message': f'Full transcript: {full_transcript}'})}\n\n"

                yield f"data: {json.dumps({'type': 'progress', 'percentage': 40, 'message': 'Matching cues to transcript...'})}\n\n"

                # Step 2: Match cues to transcript
                matches = match_cues_to_transcript(cue_lines, words)

                perfect_count = 0
                partial_count = 0
                failed_count = 0
                for i, m in enumerate(matches):
                    status = m['status']
                    if status == 'matched':
                        perfect_count += 1
                    elif status == 'partial':
                        partial_count += 1
                    else:
                        failed_count += 1
                    if m['start'] > 0 or m['end'] > 0:
                        start_t = m['start']
                        end_t = m['end']
                        score_v = m['score']
                        matched_txt = m['matched_text']
                        cue_txt = m['cue_text'][:50]
                        log_msg = f'Cue {i+1}: [{status.upper()}] {start_t:.2f}s - {end_t:.2f}s | "{cue_txt}" -> "{matched_txt}" (score: {score_v})'
                        yield f"data: {json.dumps({'type': 'log', 'message': log_msg})}\n\n"
                    else:
                        cue_txt = m['cue_text'][:50]
                        log_msg = f'Cue {i+1}: [FAILED] No match found for "{cue_txt}"'
                        yield f"data: {json.dumps({'type': 'log', 'message': log_msg})}\n\n"

                yield f"data: {json.dumps({'type': 'log', 'message': f'Match summary: {perfect_count} matched, {partial_count} partial, {failed_count} failed out of {cue_count}'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 60, 'message': 'Splitting audio files...'})}\n\n"

                # Step 3: Get total audio duration for boundary calculation
                duration_cmd = [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    audio_path_str
                ]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                total_audio_duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 0

                if total_audio_duration == 0 and words:
                    total_audio_duration = words[-1]['end'] + 0.5

                yield f"data: {json.dumps({'type': 'log', 'message': f'Total audio duration: {total_audio_duration:.2f}s'})}\n\n"

                # Step 4: Compute smooth split points using midpoints between cues
                # Instead of cutting exactly at word boundaries (which chops audio),
                # cut at the midpoint of silence BETWEEN consecutive cues.
                # First cue starts at 0, last cue ends at audio duration.
                split_points = []  # (start, end) for each cue
                for i, m in enumerate(matches):
                    if m['status'] == 'failed':
                        split_points.append(None)
                        continue

                    # Start: midpoint between previous cue's end and this cue's start
                    if i == 0:
                        cut_start = 0.0
                    else:
                        prev = matches[i - 1]
                        if prev['status'] != 'failed' and prev['end'] > 0:
                            # Midpoint of the gap between previous cue end and this cue start
                            gap_start = prev['end']
                            gap_end = m['start']
                            cut_start = (gap_start + gap_end) / 2.0
                        else:
                            cut_start = max(0, m['start'] - 0.15)

                    # End: midpoint between this cue's end and next cue's start
                    if i == len(matches) - 1:
                        cut_end = total_audio_duration
                    else:
                        nxt = matches[i + 1]
                        if nxt['status'] != 'failed' and nxt['start'] > 0:
                            gap_start = m['end']
                            gap_end = nxt['start']
                            cut_end = (gap_start + gap_end) / 2.0
                        else:
                            cut_end = m['end'] + 0.15

                    split_points.append((cut_start, cut_end))

                # Step 5: Split audio with FFmpeg using smooth boundaries
                split_files = []
                for i, sp in enumerate(split_points):
                    if sp is None:
                        split_files.append(None)
                        continue

                    cut_start, cut_end = sp
                    output_filename = f'{i+1}{audio_ext}'
                    output_path = os.path.join(out_dir, output_filename)

                    ffmpeg_cmd = [
                        FFMPEG_PATH, '-y',
                        '-i', audio_path_str,
                        '-ss', str(cut_start),
                        '-to', str(cut_end),
                        '-c', 'copy',
                        output_path
                    ]

                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'FFmpeg error for cue {i+1}: {result.stderr[:200]}'})}\n\n"
                        split_files.append(None)
                    else:
                        split_files.append(output_filename)
                        duration = cut_end - cut_start
                        yield f"data: {json.dumps({'type': 'log', 'message': f'Split cue {i+1}: {output_filename} ({duration:.2f}s) [{cut_start:.2f}s - {cut_end:.2f}s]'})}\n\n"

                    progress = 60 + int(((i + 1) / cue_count) * 30)
                    yield f"data: {json.dumps({'type': 'progress', 'percentage': progress, 'message': f'Splitting audio {i+1}/{cue_count}...'})}\n\n"

                # Step 4: Create ZIP
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 92, 'message': 'Creating ZIP archive...'})}\n\n"

                timestamp = int(time.time())
                zip_filename = f'split_audio_{timestamp}.zip'
                zip_path = os.path.join(out_dir, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for fname in split_files:
                        if fname:
                            file_path = os.path.join(out_dir, fname)
                            zf.write(file_path, fname)

                valid_count = sum(1 for f in split_files if f is not None)
                yield f"data: {json.dumps({'type': 'log', 'message': f'ZIP created with {valid_count} audio files'})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'percentage': 100, 'message': 'Complete!'})}\n\n"

                # Build match results for frontend (show actual cut points, not word boundaries)
                match_results = []
                for i, m in enumerate(matches):
                    sp = split_points[i]
                    if sp:
                        actual_start = round(sp[0], 3)
                        actual_end = round(sp[1], 3)
                    else:
                        actual_start = round(m['start'], 3)
                        actual_end = round(m['end'], 3)
                    match_results.append({
                        'cue_index': i,
                        'cue_text': m['cue_text'],
                        'status': m['status'],
                        'matched_text': m['matched_text'],
                        'start': actual_start,
                        'end': actual_end,
                        'score': m['score'],
                        'filename': split_files[i]
                    })

                yield f"data: {json.dumps({'type': 'complete', 'message': f'Audio split into {valid_count} files!', 'zipUrl': f'/api/download-split/{zip_filename}', 'matchResults': match_results, 'stats': {'total': cue_count, 'matched': perfect_count, 'partial': partial_count, 'failed': failed_count, 'valid_splits': valid_count}})}\n\n"

            except Exception as e:
                import traceback
                error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-split/<filename>')
def download_split(filename):
    """Download split audio ZIP file"""
    file_path = PROJECT_ROOT / 'output' / 'split_audio' / filename
    if file_path.exists():
        return send_file(
            file_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='split_audio.zip'
        )
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/download-split-file/<filename>')
def download_split_file(filename):
    """Download individual split audio file"""
    file_path = PROJECT_ROOT / 'output' / 'split_audio' / filename
    if file_path.exists():
        mime = 'audio/mpeg' if filename.endswith('.mp3') else 'audio/wav'
        return send_file(
            file_path,
            mimetype=mime,
            as_attachment=True,
            download_name=filename
        )
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    print("=" * 80)
    print("VIDEO MAKER - Web Server")
    print("=" * 80)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:8080")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8080)
