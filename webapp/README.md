# 🎬 Video Maker Web Application

A beautiful, modern web interface for creating professional videos from transcripts, audio, and images.

## ✨ Features

- **Intuitive Upload Interface** - Drag & drop or click to upload files
- **Real-time Progress Tracking** - See exactly what's happening during video generation
- **Live Output Logs** - Monitor the entire process with color-coded logs
- **Instant Download** - Get your video immediately after processing
- **Clear Inputs** - Easily reset and start over
- **Modern UI** - Stunning design with smooth animations and gradients

## 🚀 Quick Start

### 1. Install Dependencies

First, install the Python dependencies for the web server:

```bash
cd webapp
pip install -r requirements.txt
```

Make sure you also have the main video maker dependencies installed:

```bash
cd ..
pip install -r scripts/requirements.txt
```

### 2. Start the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

### 3. Open in Browser

Navigate to `http://localhost:5000` in your web browser.

### 4. Upload Your Files

1. **Transcript** - Upload your script file (.txt)
2. **Audio** - Upload your narration (.mp3, .wav, or .m4a)
3. **Images** - Upload your scene images (.png, .jpg, or .jpeg)

### 5. Generate Video

Click the "Generate Video" button and watch the magic happen! You'll see:
- Real-time progress updates
- Detailed logs of each processing step
- A download link when complete

## 📁 File Requirements

### Transcript (transcript.txt)
- Plain text file
- One paragraph per scene
- Separated by blank lines

Example:
```
This is the first scene.

This is the second scene.

This is the third scene.
```

### Audio (audio.mp3)
- MP3, WAV, or M4A format
- Should match the transcript content
- Clear narration recommended

### Images
- PNG, JPG, or JPEG format
- Number of images should match number of paragraphs
- Files will be automatically sorted and numbered

## 🎨 Features in Detail

### Drag & Drop Support
Simply drag files onto the upload areas instead of clicking to browse.

### Real-time Logs
Watch the video creation process in real-time with color-coded logs:
- 🔵 **Info** - General information
- 🟢 **Success** - Completed steps
- 🟡 **Warning** - Important notices
- 🔴 **Error** - Issues that need attention

### Progress Bar
Beautiful animated progress bar shows exactly where you are in the process.

### Clear All
Reset everything with one click - perfect for starting a new project.

## 🛠️ Technical Details

### Backend
- **Flask** - Python web framework
- **Server-Sent Events (SSE)** - Real-time log streaming
- **Subprocess** - Executes the video creation script

### Frontend
- **Vanilla JavaScript** - No frameworks, pure performance
- **Modern CSS** - Gradients, animations, glassmorphism
- **Responsive Design** - Works on all screen sizes

## 🔧 Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `server.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
```

### Files Not Uploading
- Check file formats match requirements
- Ensure files aren't corrupted
- Try smaller file sizes first

### Video Generation Fails
- Check the logs for specific error messages
- Ensure FFmpeg is installed
- Verify all dependencies are installed
- Check that input files are valid

### Browser Compatibility
Works best in modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari

## 📝 API Endpoints

### POST `/api/generate-video`
Upload files and generate video
- **Body**: FormData with transcript, audio, and images
- **Response**: Server-Sent Events stream

### GET `/api/download-video`
Download the generated video
- **Response**: MP4 file

### POST `/api/clear`
Clear all uploaded files
- **Response**: JSON success message

## 🎯 Tips for Best Results

1. **Match Counts** - Ensure number of images equals number of paragraphs
2. **Clear Audio** - Use high-quality audio for better transcription
3. **Consistent Images** - Use images with similar aspect ratios (16:9 recommended)
4. **File Naming** - Name images sequentially (1.png, 2.png, etc.) for easier tracking
5. **Test First** - Try with a small project first to verify everything works

## 🌟 Future Enhancements

Potential features for future versions:
- Video preview before download
- Custom caption styling
- Multiple video format exports
- Batch processing
- Project saving/loading
- Cloud storage integration

## 📄 License

Part of the Video Maker project.

---

**Enjoy creating amazing videos!** 🎬✨
