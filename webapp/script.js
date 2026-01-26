// ============================================
// State Management
// ============================================
const state = {
    files: {
        transcript: null,
        audio: null,
        images: [],
        videos: []
    },
    scenes: [],
    sceneConfig: { scenes: {} },
    isProcessing: false
};

// ============================================
// DOM Elements
// ============================================
const elements = {
    transcriptFile: document.getElementById('transcriptFile'),
    audioFile: document.getElementById('audioFile'),
    imageFiles: document.getElementById('imageFiles'),
    videoFiles: document.getElementById('videoFiles'),
    transcriptStatus: document.getElementById('transcriptStatus'),
    audioStatus: document.getElementById('audioStatus'),
    imagesStatus: document.getElementById('imagesStatus'),
    videosStatus: document.getElementById('videosStatus'),
    imagePreviewContainer: document.getElementById('imagePreviewContainer'),
    sceneConfigSection: document.getElementById('sceneConfigSection'),
    scenesContainer: document.getElementById('scenesContainer'),
    resetScenesBtn: document.getElementById('resetScenesBtn'),
    saveSceneConfigBtn: document.getElementById('saveSceneConfigBtn'),
    clearBtn: document.getElementById('clearBtn'),
    generateBtn: document.getElementById('generateBtn'),
    outputSection: document.getElementById('outputSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    logsContent: document.getElementById('logsContent'),
    clearLogsBtn: document.getElementById('clearLogsBtn'),
    resultContainer: document.getElementById('resultContainer'),
    downloadLink: document.getElementById('downloadLink')
};

// ============================================
// File Upload Handlers
// ============================================
elements.transcriptFile.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        state.files.transcript = file;
        updateFileStatus('transcript', file.name, true);

        // Parse transcript to get scenes
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            const lines = content.split('\n');

            state.scenes = [];
            lines.forEach(line => {
                line = line.trim();
                if (line) {
                    state.scenes.push({
                        number: state.scenes.length + 1,
                        text: line
                    });
                }
            });

            if (state.scenes.length > 0) {
                renderSceneConfiguration();
                elements.sceneConfigSection.style.display = 'block';
            }
        };
        reader.readAsText(file);

        checkFormValidity();
    }
});

elements.audioFile.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        state.files.audio = file;
        updateFileStatus('audio', file.name, true);
        checkFormValidity();
    }
});

elements.imageFiles.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        // Sort files by name to ensure proper ordering
        state.files.images = files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
        updateFileStatus('images', `${files.length} file(s) selected`, true);
        displayImagePreviews(state.files.images);
        checkFormValidity();
    }
});

elements.videoFiles.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        state.files.videos = files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
        updateFileStatus('videos', `${files.length} video(s) selected`, true);
    }
});

// ============================================
// UI Update Functions
// ============================================
function updateFileStatus(type, message, success = false) {
    const statusElement = elements[`${type}Status`];
    statusElement.textContent = message;
    statusElement.className = success ? 'file-status success' : 'file-status';
}

function checkFormValidity() {
    const isValid = state.files.transcript &&
        state.files.audio &&
        state.files.images.length > 0;
    elements.generateBtn.disabled = !isValid;
}

function displayImagePreviews(files) {
    // Clear existing previews
    elements.imagePreviewContainer.innerHTML = '';

    // Create preview for each image
    files.forEach((file, index) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'image-preview-item';

            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = `Image ${index + 1}`;

            const numberBadge = document.createElement('div');
            numberBadge.className = 'image-preview-number';
            numberBadge.textContent = index + 1;

            previewItem.appendChild(img);
            previewItem.appendChild(numberBadge);
            elements.imagePreviewContainer.appendChild(previewItem);
        };

        reader.readAsDataURL(file);
    });
}

function addLog(message, type = 'info') {
    const logLine = document.createElement('div');
    logLine.className = `log-line ${type}`;
    logLine.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    elements.logsContent.appendChild(logLine);
    elements.logsContent.scrollTop = elements.logsContent.scrollHeight;
}

function updateProgress(percentage, message) {
    elements.progressFill.style.width = `${percentage}%`;
    elements.progressText.textContent = message;
}

function clearLogs() {
    elements.logsContent.innerHTML = '<div class="log-line">Ready to process...</div>';
}

// ============================================
// Clear Functionality
// ============================================
elements.clearBtn.addEventListener('click', () => {
    if (state.isProcessing) {
        if (!confirm('Processing is in progress. Are you sure you want to clear?')) {
            return;
        }
    }

    // Reset state
    state.files = {
        transcript: null,
        audio: null,
        images: [],
        videos: []
    };
    state.scenes = [];
    state.sceneConfig = { scenes: {} };

    // Reset file inputs
    elements.transcriptFile.value = '';
    elements.audioFile.value = '';
    elements.imageFiles.value = '';
    elements.videoFiles.value = '';

    // Reset status displays
    elements.transcriptStatus.textContent = '';
    elements.transcriptStatus.className = 'file-status';
    elements.audioStatus.textContent = '';
    elements.audioStatus.className = 'file-status';
    elements.imagesStatus.textContent = '';
    elements.imagesStatus.className = 'file-status';
    elements.videosStatus.textContent = '';
    elements.videosStatus.className = 'file-status';

    // Clear image previews
    elements.imagePreviewContainer.innerHTML = '';

    // Hide scene configuration section
    elements.sceneConfigSection.style.display = 'none';
    elements.scenesContainer.innerHTML = '';

    // Hide output section
    elements.outputSection.style.display = 'none';
    elements.resultContainer.style.display = 'none';

    // Reset progress
    updateProgress(0, 'Ready');
    clearLogs();

    // Disable generate button
    checkFormValidity();

    addLog('All inputs cleared', 'info');
});

elements.clearLogsBtn.addEventListener('click', clearLogs);

// ============================================
// Video Generation
// ============================================
elements.generateBtn.addEventListener('click', async () => {
    if (state.isProcessing) return;

    state.isProcessing = true;
    elements.generateBtn.disabled = true;
    elements.outputSection.style.display = 'block';
    elements.resultContainer.style.display = 'none';

    // Scroll to output section
    elements.outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    clearLogs();
    addLog('Starting video generation process...', 'info');
    updateProgress(5, 'Preparing files...');

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('transcript', state.files.transcript);
        formData.append('audio', state.files.audio);

        // Add images with proper naming
        state.files.images.forEach((file, index) => {
            formData.append('images', file);
        });

        addLog(`Uploading ${state.files.images.length} images...`, 'info');

        // Add scene videos if any are configured
        let videoSceneCount = 0;
        Object.keys(state.sceneConfig.scenes).forEach(sceneKey => {
            const scene = state.sceneConfig.scenes[sceneKey];
            if (scene.type === 'video' && scene.file) {
                formData.append(`scene_video_${sceneKey}`, scene.file);
                videoSceneCount++;
            }
        });

        if (videoSceneCount > 0) {
            addLog(`Uploading ${videoSceneCount} video scene(s)...`, 'info');
        }

        updateProgress(10, 'Uploading files...');

        // Send to server
        const response = await fetch('/api/generate-video', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        // Handle streaming response for logs
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        handleServerMessage(data);
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        addLog(`Error: ${error.message}`, 'error');
        updateProgress(0, 'Failed');
        state.isProcessing = false;
        elements.generateBtn.disabled = false;
    }
});

function handleServerMessage(data) {
    switch (data.type) {
        case 'log':
            addLog(data.message, data.level || 'info');
            break;

        case 'progress':
            updateProgress(data.percentage, data.message);
            break;

        case 'complete':
            addLog('Video generation completed successfully!', 'success');
            updateProgress(100, 'Complete!');
            showResult(data.videoUrl);
            state.isProcessing = false;
            break;

        case 'error':
            addLog(`Error: ${data.message}`, 'error');
            updateProgress(0, 'Failed');
            state.isProcessing = false;
            elements.generateBtn.disabled = false;
            break;
    }
}

function showResult(videoUrl) {
    elements.resultContainer.style.display = 'block';
    elements.downloadLink.href = videoUrl;
    elements.resultContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============================================
// Drag and Drop Support
// ============================================
function setupDragAndDrop(inputElement, statusElement, fileType) {
    const label = inputElement.nextElementSibling;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        label.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        label.addEventListener(eventName, () => {
            label.style.borderColor = 'var(--color-primary)';
            label.style.background = 'var(--bg-hover)';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        label.addEventListener(eventName, () => {
            label.style.borderColor = '';
            label.style.background = '';
        });
    });

    label.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            inputElement.files = files;
            inputElement.dispatchEvent(new Event('change'));
        }
    });
}

// Setup drag and drop for all file inputs
setupDragAndDrop(elements.transcriptFile, elements.transcriptStatus, 'transcript');
setupDragAndDrop(elements.audioFile, elements.audioStatus, 'audio');
setupDragAndDrop(elements.imageFiles, elements.imagesStatus, 'images');
setupDragAndDrop(elements.videoFiles, elements.videosStatus, 'videos');

// ============================================
// Scene Configuration
// ============================================
function renderSceneConfiguration() {
    if (state.scenes.length === 0) {
        elements.scenesContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No scenes found. Please upload a transcript.</p>';
        return;
    }

    elements.scenesContainer.innerHTML = state.scenes.map(scene => {
        const sceneKey = scene.number.toString();
        const sceneInfo = state.sceneConfig.scenes[sceneKey] || { type: 'image' };
        const isVideo = sceneInfo.type === 'video';
        const videoFileName = sceneInfo.file ? sceneInfo.file.name : '';

        return `
            <div class="scene-card ${isVideo ? 'video-active' : ''}" data-scene="${scene.number}">
                <div class="scene-header">
                    <div class="scene-number">Scene ${scene.number}</div>
                    <div class="scene-toggle">
                        <span class="toggle-label">Use Video</span>
                        <label class="toggle-switch">
                            <input type="checkbox"
                                   ${isVideo ? 'checked' : ''}
                                   data-scene="${scene.number}"
                                   onchange="handleSceneToggle(${scene.number}, this.checked)">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
                <div class="scene-text">${scene.text}</div>
                <div class="video-input-container ${isVideo ? 'active' : ''}" id="video-input-${scene.number}">
                    <label class="video-input-label">Select Video File</label>
                    <div class="video-path-input-group">
                        <input type="file"
                               class="scene-video-file-input"
                               id="video-file-${scene.number}"
                               accept=".mp4,.mov,.avi"
                               onchange="handleSceneVideoUpload(${scene.number}, this.files[0])"
                               style="display: none;">
                        <label for="video-file-${scene.number}" class="btn-browse">
                            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Browse Video
                        </label>
                        <span class="video-file-name" id="video-name-${scene.number}">
                            ${videoFileName || 'No file selected'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function handleSceneToggle(sceneNumber, useVideo) {
    const sceneKey = sceneNumber.toString();
    const sceneCard = document.querySelector(`[data-scene="${sceneNumber}"]`);
    const videoInput = document.getElementById(`video-input-${sceneNumber}`);

    if (useVideo) {
        state.sceneConfig.scenes[sceneKey] = {
            type: 'video',
            file: state.sceneConfig.scenes[sceneKey]?.file || null
        };
        videoInput.classList.add('active');
        sceneCard.classList.add('video-active');
    } else {
        state.sceneConfig.scenes[sceneKey] = { type: 'image' };
        videoInput.classList.remove('active');
        sceneCard.classList.remove('video-active');
    }
}

function handleSceneVideoUpload(sceneNumber, file) {
    if (!file) return;

    const sceneKey = sceneNumber.toString();
    const videoNameSpan = document.getElementById(`video-name-${sceneNumber}`);

    // Store the file in the scene config
    if (!state.sceneConfig.scenes[sceneKey]) {
        state.sceneConfig.scenes[sceneKey] = { type: 'video' };
    }
    state.sceneConfig.scenes[sceneKey].file = file;

    // Update the display
    videoNameSpan.textContent = file.name;
    videoNameSpan.style.color = 'var(--color-success)';

    addLog(`Scene ${sceneNumber}: Video file selected - ${file.name}`, 'info');
}

// Reset scenes button
elements.resetScenesBtn.addEventListener('click', () => {
    if (confirm('Reset all scenes to use images?')) {
        state.sceneConfig = { scenes: {} };
        renderSceneConfiguration();
    }
});

// Save scene config button
elements.saveSceneConfigBtn.addEventListener('click', () => {
    // Check if any video scenes are configured
    const videoScenes = Object.keys(state.sceneConfig.scenes).filter(
        key => state.sceneConfig.scenes[key].type === 'video'
    );

    if (videoScenes.length === 0) {
        addLog('No video scenes configured. All scenes will use images.', 'info');
        return;
    }

    // Check if all video scenes have files
    const missingFiles = videoScenes.filter(
        key => !state.sceneConfig.scenes[key].file
    );

    if (missingFiles.length > 0) {
        alert(`Please select video files for scene(s): ${missingFiles.join(', ')}`);
        return;
    }

    // Create a zip-like structure with config and video files
    // For now, we'll create a simple config with video filenames
    const configForExport = {
        scenes: {}
    };

    Object.keys(state.sceneConfig.scenes).forEach(sceneKey => {
        const scene = state.sceneConfig.scenes[sceneKey];
        if (scene.type === 'video' && scene.file) {
            configForExport.scenes[sceneKey] = {
                type: 'video',
                path: `input/videos/${scene.file.name}`
            };
        }
    });

    // Download the config file
    const configJson = JSON.stringify(configForExport, null, 2);
    const configBlob = new Blob([configJson], { type: 'application/json' });
    const configUrl = URL.createObjectURL(configBlob);

    const configLink = document.createElement('a');
    configLink.href = configUrl;
    configLink.download = 'scene_config.json';
    document.body.appendChild(configLink);
    configLink.click();
    document.body.removeChild(configLink);
    URL.revokeObjectURL(configUrl);

    // Download all video files
    videoScenes.forEach(sceneKey => {
        const scene = state.sceneConfig.scenes[sceneKey];
        if (scene.file) {
            const videoUrl = URL.createObjectURL(scene.file);
            const videoLink = document.createElement('a');
            videoLink.href = videoUrl;
            videoLink.download = scene.file.name;
            document.body.appendChild(videoLink);
            videoLink.click();
            document.body.removeChild(videoLink);
            URL.revokeObjectURL(videoUrl);
        }
    });

    addLog('Scene configuration and video files downloaded!', 'success');
    addLog('Place scene_config.json in input/ folder', 'info');
    addLog('Place video files in input/videos/ folder', 'info');
});

// Make functions available globally
window.handleSceneToggle = handleSceneToggle;
window.handleSceneVideoUpload = handleSceneVideoUpload;

// ============================================
// Initialize
// ============================================
addLog('Application ready. Upload your files to begin.', 'info');
