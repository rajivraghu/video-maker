#!/bin/bash

# Video Maker Web Application Launcher
# This script starts the web server for the Video Maker application

echo "============================================================"
echo "🎬 Video Maker Web Application"
echo "============================================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "server.py" ]; then
    echo "❌ Error: server.py not found!"
    echo "Please run this script from the webapp directory."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

# Start the server
echo "🚀 Starting Video Maker Web Server..."
echo ""
echo "📍 Access the application at:"
echo "   http://localhost:8081"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

python3 server.py
