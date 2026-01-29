# 🌐 Video Maker Web Application - Quick Start

## 🎯 What is This?

A beautiful, modern web interface for the Video Maker project that lets you:
- Upload files through a stunning UI
- Watch real-time progress as your video is created
- See detailed logs of the entire process
- Download your video instantly

## 🚀 Quick Start (3 Steps)

### 1️⃣ Navigate to the webapp folder
```bash
cd video_maker/webapp
```

### 2️⃣ Run the launcher script
```bash
./start.sh
```

### 3️⃣ Open your browser
Navigate to: **http://localhost:8081**

That's it! 🎉

## 📋 What You'll See

The web app has a gorgeous dark theme with:
- **Vibrant purple and blue gradients**
- **Smooth animations** on hover and interactions
- **Real-time progress bar** showing exactly where you are
- **Color-coded logs** (green for success, red for errors, etc.)
- **Instant download** when your video is ready

## 📁 How to Use

1. **Upload Transcript** - Click or drag your `.txt` file
2. **Upload Audio** - Click or drag your `.mp3` file  
3. **Upload Images** - Click or drag your image files (can select multiple)
4. **Click "Generate Video"** - Watch the magic happen!
5. **Download** - Get your video when it's done

### Clear All Button
Made a mistake? Click "Clear All" to reset everything and start over.

## 🎨 Features

✨ **Drag & Drop** - Just drag files onto the upload areas  
📊 **Live Progress** - Animated progress bar with percentage  
📝 **Real-time Logs** - See every step of the process  
🎯 **Smart Validation** - Only allows correct file types  
🔄 **Easy Reset** - Clear all inputs with one click  
💾 **Instant Download** - Get your video immediately  

## 🛠️ Technical Details

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript + Modern CSS
- **Real-time Updates**: Server-Sent Events (SSE)
- **Port**: 8081 (to avoid conflicts with macOS AirPlay)

## 📖 Full Documentation

For more details, see `webapp/README.md`

## 🎬 Enjoy!

Your video creation process just got a whole lot prettier! ✨
