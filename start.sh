#!/bin/bash
# Video Maker - Web Server Startup Script

echo "================================================================================"
echo "VIDEO MAKER - Starting Web Server"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python 3 found"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed"
    echo "   Please install FFmpeg:"
    echo "   - Mac: brew install ffmpeg"
    echo "   - Linux: sudo apt-get install ffmpeg"
    exit 1
fi

echo "✓ FFmpeg found"

# Check if requirements are installed
echo ""
echo "Checking dependencies..."

if ! python3 -c "import flask" &> /dev/null; then
    echo "⚠️  Dependencies not installed"
    echo "   Installing requirements..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✓ Dependencies installed"
echo ""

# Start the server
echo "Starting server on http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================================================"
echo ""

python3 server.py
