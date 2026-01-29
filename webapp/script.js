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
    transitionSounds: {},  // Maps position (0=intro, 1=after scene 1, etc.) to file
    isProcessing: false,
    currentPage: 'video-maker'
};

// Regional Mix State
const rmState = {
    mediaFiles: [], // Can be images or videos
    audioFiles: [],
    matchedPairs: [], // { number, media (file), mediaType ('image' or 'video'), audio (file) }
    isProcessing: false
};

// Helper to check if file is video
function isVideoFile(file) {
    const videoExtensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    return videoExtensions.includes(ext);
}

// Helper to get audio duration from file
function getAudioDuration(file) {
    return new Promise((resolve) => {
        const audio = new Audio();
        audio.addEventListener('loadedmetadata', () => {
            resolve(audio.duration);
        });
        audio.addEventListener('error', () => {
            resolve(null);
        });
        audio.src = URL.createObjectURL(file);
    });
}

// Helper to format duration as MM:SS
function formatDuration(seconds) {
    if (seconds === null || isNaN(seconds)) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

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
    state.transitionSounds = {};

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

        // Add per-scene transition sounds if any are configured
        const transitionSoundKeys = Object.keys(state.transitionSounds);
        if (transitionSoundKeys.length > 0) {
            transitionSoundKeys.forEach(position => {
                const file = state.transitionSounds[position];
                if (file) {
                    formData.append(`transition_sound_${position}`, file);
                }
            });
            addLog(`Including ${transitionSoundKeys.length} transition sound(s)...`, 'info');
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

    // Helper to render transition sound slot
    const renderTransitionSlot = (position, label) => {
        const hasSound = state.transitionSounds[position];
        const fileName = hasSound ? state.transitionSounds[position].name : '';
        return `
            <div class="transition-sound-slot" data-position="${position}">
                <div class="transition-slot-line"></div>
                <div class="transition-slot-content ${hasSound ? 'has-sound' : ''}">
                    <span class="transition-slot-label">${label}</span>
                    <input type="file"
                           id="transition-sound-${position}"
                           accept=".mp3,.wav"
                           onchange="handleTransitionSoundUpload(${position}, this.files[0])"
                           style="display: none;">
                    ${hasSound ? `
                        <div class="transition-sound-info">
                            <span class="transition-sound-name">${fileName}</span>
                            <button type="button" class="btn-remove-transition" onclick="removeTransitionSound(${position})">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    ` : `
                        <label for="transition-sound-${position}" class="btn-add-transition">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M19 12h-6m3-3v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                            Add Sound
                        </label>
                    `}
                </div>
                <div class="transition-slot-line"></div>
            </div>
        `;
    };

    // Build the HTML with transition slots between scenes
    let html = '';

    // Add intro transition slot (before first scene)
    html += renderTransitionSlot(0, 'Intro Sound');

    state.scenes.forEach((scene, index) => {
        const sceneKey = scene.number.toString();
        const sceneInfo = state.sceneConfig.scenes[sceneKey] || { type: 'image' };
        const isVideo = sceneInfo.type === 'video';
        const videoFileName = sceneInfo.file ? sceneInfo.file.name : '';

        html += `
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

        // Add transition slot after each scene (except the last one)
        if (index < state.scenes.length - 1) {
            html += renderTransitionSlot(scene.number, `Transition ${scene.number} → ${scene.number + 1}`);
        }
    });

    elements.scenesContainer.innerHTML = html;
}

// Handle transition sound upload for specific position
function handleTransitionSoundUpload(position, file) {
    if (!file) return;

    state.transitionSounds[position] = file;
    renderSceneConfiguration();
    addLog(`Added transition sound at position ${position}: ${file.name}`, 'info');
}

// Remove transition sound from specific position
function removeTransitionSound(position) {
    delete state.transitionSounds[position];
    renderSceneConfiguration();
    addLog(`Removed transition sound at position ${position}`, 'info');
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
// Navigation
// ============================================
const navBtns = document.querySelectorAll('.nav-btn');
const uploadSection = document.querySelector('.upload-section');
const sceneConfigSection = document.getElementById('sceneConfigSection');
const outputSection = document.getElementById('outputSection');
const regionalMixSection = document.getElementById('regionalMixSection');
const rmOutputSection = document.getElementById('rmOutputSection');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        switchPage(page);
    });
});

function switchPage(page) {
    state.currentPage = page;

    // Update nav buttons
    navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === page);
    });

    // Show/hide sections based on page
    if (page === 'video-maker') {
        uploadSection.style.display = 'block';
        sceneConfigSection.style.display = state.scenes.length > 0 ? 'block' : 'none';
        outputSection.style.display = state.isProcessing || elements.resultContainer.style.display === 'block' ? 'block' : 'none';
        regionalMixSection.style.display = 'none';
        rmOutputSection.style.display = 'none';
    } else if (page === 'regional-mix') {
        uploadSection.style.display = 'none';
        sceneConfigSection.style.display = 'none';
        outputSection.style.display = 'none';
        regionalMixSection.style.display = 'block';
        rmOutputSection.style.display = rmState.isProcessing || document.getElementById('rmResultContainer').style.display === 'block' ? 'block' : 'none';
    }
}

// ============================================
// Regional Mix - DOM Elements
// ============================================
const rmElements = {
    imageFiles: document.getElementById('rmImageFiles'),
    audioFiles: document.getElementById('rmAudioFiles'),
    imagesStatus: document.getElementById('rmImagesStatus'),
    audioStatus: document.getElementById('rmAudioStatus'),
    previewSection: document.getElementById('rmPreviewSection'),
    previewGrid: document.getElementById('rmPreviewGrid'),
    clearBtn: document.getElementById('rmClearBtn'),
    clearServerBtn: document.getElementById('rmClearServerBtn'),
    generateBtn: document.getElementById('rmGenerateBtn'),
    outputSection: document.getElementById('rmOutputSection'),
    progressFill: document.getElementById('rmProgressFill'),
    progressText: document.getElementById('rmProgressText'),
    logsContent: document.getElementById('rmLogsContent'),
    clearLogsBtn: document.getElementById('rmClearLogsBtn'),
    resultContainer: document.getElementById('rmResultContainer'),
    downloadLink: document.getElementById('rmDownloadLink')
};

// ============================================
// Regional Mix - File Upload Handlers
// ============================================
rmElements.imageFiles.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        rmState.mediaFiles = files.sort((a, b) => {
            const numA = extractNumber(a.name);
            const numB = extractNumber(b.name);
            return numA - numB;
        });
        const imageCount = files.filter(f => !isVideoFile(f)).length;
        const videoCount = files.filter(f => isVideoFile(f)).length;
        let statusText = '';
        if (imageCount > 0 && videoCount > 0) {
            statusText = `${imageCount} image(s) + ${videoCount} video(s) selected`;
        } else if (imageCount > 0) {
            statusText = `${imageCount} image(s) selected`;
        } else {
            statusText = `${videoCount} video(s) selected`;
        }
        rmElements.imagesStatus.textContent = statusText;
        rmElements.imagesStatus.className = 'file-status success';
        updateRMPreview();
        checkRMFormValidity();
    }
});

rmElements.audioFiles.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        rmState.audioFiles = files.sort((a, b) => {
            const numA = extractNumber(a.name);
            const numB = extractNumber(b.name);
            return numA - numB;
        });
        rmElements.audioStatus.textContent = `${files.length} audio file(s) selected - loading durations...`;
        rmElements.audioStatus.className = 'file-status success';

        // Get total duration of all audio files
        const durations = await Promise.all(files.map(f => getAudioDuration(f)));
        const totalDuration = durations.reduce((sum, d) => sum + (d || 0), 0);
        const totalFormatted = formatDuration(totalDuration);

        rmElements.audioStatus.textContent = `${files.length} audio file(s) - Total: ${totalFormatted}`;

        updateRMPreview();
        checkRMFormValidity();
    }
});

function extractNumber(filename) {
    // Extract number from filename like "1.png", "2.mp3", "image_1.jpg", etc.
    const match = filename.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
}

function checkRMFormValidity() {
    const isValid = rmState.mediaFiles.length > 0 && rmState.audioFiles.length > 0;
    rmElements.generateBtn.disabled = !isValid;
}

// ============================================
// Regional Mix - Preview
// ============================================
async function updateRMPreview() {
    if (rmState.mediaFiles.length === 0 && rmState.audioFiles.length === 0) {
        rmElements.previewSection.style.display = 'none';
        return;
    }

    rmElements.previewSection.style.display = 'block';

    // Match media (images/videos) and audio by their numbers
    const mediaMap = new Map();
    const audioMap = new Map();

    rmState.mediaFiles.forEach(file => {
        const num = extractNumber(file.name);
        mediaMap.set(num, { file, type: isVideoFile(file) ? 'video' : 'image' });
    });

    rmState.audioFiles.forEach(file => {
        const num = extractNumber(file.name);
        audioMap.set(num, file);
    });

    // Get all unique numbers
    const allNumbers = new Set([...mediaMap.keys(), ...audioMap.keys()]);
    const sortedNumbers = Array.from(allNumbers).sort((a, b) => a - b);

    // Build matched pairs (preserve any manually changed media)
    const existingPairs = new Map(rmState.matchedPairs.map(p => [p.number, p]));

    // Build pairs and load audio durations
    const pairsPromises = sortedNumbers.map(async num => {
        const existing = existingPairs.get(num);
        const mediaInfo = mediaMap.get(num);
        const audioFile = audioMap.get(num);

        // If there's an existing pair with manually changed media, keep it
        if (existing && existing.manuallyChanged) {
            // Update duration if audio changed
            let duration = existing.audioDuration;
            if (audioFile && audioFile !== existing.audio) {
                duration = await getAudioDuration(audioFile);
            }
            return {
                ...existing,
                audio: audioFile || existing.audio,
                audioDuration: duration
            };
        }

        // Get audio duration for new pairs
        let duration = null;
        if (audioFile) {
            duration = await getAudioDuration(audioFile);
        }

        return {
            number: num,
            media: mediaInfo ? mediaInfo.file : null,
            mediaType: mediaInfo ? mediaInfo.type : 'image',
            audio: audioFile || null,
            audioDuration: duration,
            manuallyChanged: false
        };
    });

    rmState.matchedPairs = await Promise.all(pairsPromises);

    renderRMPreviewCards();
}

function renderRMPreviewCards() {
    rmElements.previewGrid.innerHTML = '';

    rmState.matchedPairs.forEach((pair, index) => {
        const card = document.createElement('div');
        card.className = 'rm-preview-card' + (!pair.media || !pair.audio ? ' warning' : '');
        card.dataset.pairIndex = index;

        let mediaHtml = '';
        if (pair.media) {
            if (pair.mediaType === 'video') {
                const videoUrl = URL.createObjectURL(pair.media);
                mediaHtml = `
                    <div class="rm-preview-media-container">
                        <video class="rm-preview-video" src="${videoUrl}" muted></video>
                        <div class="rm-media-badge video-badge">VIDEO</div>
                    </div>
                `;
            } else {
                mediaHtml = `
                    <div class="rm-preview-media-container">
                        <img class="rm-preview-image" alt="Image ${pair.number}" src="">
                        <div class="rm-media-badge image-badge">IMAGE</div>
                    </div>
                `;
                // Load image async
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = card.querySelector('.rm-preview-image');
                    if (img) img.src = e.target.result;
                };
                reader.readAsDataURL(pair.media);
            }
        } else {
            mediaHtml = `
                <div class="rm-preview-media-container">
                    <div class="rm-preview-image missing">No Media</div>
                </div>
            `;
        }

        let audioHtml = '';
        if (pair.audio) {
            const audioUrl = URL.createObjectURL(pair.audio);
            const durationStr = formatDuration(pair.audioDuration);
            audioHtml = `
                <div class="rm-preview-audio">
                    <div class="rm-audio-duration">${durationStr}</div>
                    <audio controls src="${audioUrl}"></audio>
                    <div class="rm-preview-audio-name">${pair.audio.name}</div>
                </div>
            `;
        } else {
            audioHtml = `<div class="rm-preview-missing">No audio file</div>`;
        }

        card.innerHTML = `
            <div class="rm-preview-header">
                <span class="rm-preview-number">${pair.number}</span>
                <span class="rm-preview-title">Pair ${pair.number}</span>
            </div>
            <div class="rm-preview-content">
                <div class="rm-media-section">
                    ${mediaHtml}
                    <div class="rm-media-actions">
                        <input type="file"
                               id="rm-change-media-${pair.number}"
                               accept=".png,.jpg,.jpeg,.mp4,.mov,.avi,.webm"
                               style="display: none;"
                               data-pair-number="${pair.number}">
                        <label for="rm-change-media-${pair.number}" class="rm-change-btn">
                            Change
                        </label>
                    </div>
                    ${pair.media ? `<div class="rm-media-filename">${pair.media.name}</div>` : ''}
                </div>
                ${audioHtml}
            </div>
        `;

        rmElements.previewGrid.appendChild(card);

        // Add event listener for changing media
        const changeInput = card.querySelector(`#rm-change-media-${pair.number}`);
        changeInput.addEventListener('change', (e) => handleRMMediaChange(pair.number, e.target.files[0]));
    });
}

function handleRMMediaChange(pairNumber, file) {
    if (!file) return;

    const pairIndex = rmState.matchedPairs.findIndex(p => p.number === pairNumber);
    if (pairIndex === -1) return;

    const mediaType = isVideoFile(file) ? 'video' : 'image';

    rmState.matchedPairs[pairIndex] = {
        ...rmState.matchedPairs[pairIndex],
        media: file,
        mediaType: mediaType,
        manuallyChanged: true
    };

    renderRMPreviewCards();
    rmAddLog(`Pair ${pairNumber}: Changed to ${mediaType} - ${file.name}`, 'info');
}

// ============================================
// Regional Mix - Clear
// ============================================
rmElements.clearBtn.addEventListener('click', () => {
    if (rmState.isProcessing) {
        if (!confirm('Processing is in progress. Are you sure you want to clear?')) {
            return;
        }
    }

    rmState.mediaFiles = [];
    rmState.audioFiles = [];
    rmState.matchedPairs = [];

    rmElements.imageFiles.value = '';
    rmElements.audioFiles.value = '';
    rmElements.imagesStatus.textContent = '';
    rmElements.imagesStatus.className = 'file-status';
    rmElements.audioStatus.textContent = '';
    rmElements.audioStatus.className = 'file-status';
    rmElements.previewSection.style.display = 'none';
    rmElements.previewGrid.innerHTML = '';
    rmElements.outputSection.style.display = 'none';
    rmElements.resultContainer.style.display = 'none';

    rmUpdateProgress(0, 'Ready');
    rmClearLogs();
    checkRMFormValidity();

    rmAddLog('All inputs cleared', 'info');
});

// Clear Server Files button
rmElements.clearServerBtn.addEventListener('click', async () => {
    if (!confirm('This will delete all input and output files from the server. Are you sure?')) {
        return;
    }

    rmElements.clearServerBtn.disabled = true;
    rmElements.clearServerBtn.textContent = 'Clearing...';

    try {
        const response = await fetch('/api/clear-files', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            rmAddLog(`Server files cleared: ${data.message}`, 'success');
            alert('Server files cleared successfully!');
        } else {
            rmAddLog(`Error clearing files: ${data.error}`, 'error');
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        rmAddLog(`Error: ${error.message}`, 'error');
        alert(`Error: ${error.message}`);
    } finally {
        rmElements.clearServerBtn.disabled = false;
        rmElements.clearServerBtn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Clear Server Files
        `;
    }
});

rmElements.clearLogsBtn.addEventListener('click', rmClearLogs);

// ============================================
// Regional Mix - Logging
// ============================================
function rmAddLog(message, type = 'info') {
    const logLine = document.createElement('div');
    logLine.className = `log-line ${type}`;
    logLine.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    rmElements.logsContent.appendChild(logLine);
    rmElements.logsContent.scrollTop = rmElements.logsContent.scrollHeight;
}

function rmUpdateProgress(percentage, message) {
    rmElements.progressFill.style.width = `${percentage}%`;
    rmElements.progressText.textContent = message;
}

function rmClearLogs() {
    rmElements.logsContent.innerHTML = '<div class="log-line">Ready to process...</div>';
}

// ============================================
// Regional Mix - Video Generation
// ============================================
rmElements.generateBtn.addEventListener('click', async () => {
    if (rmState.isProcessing) return;

    // Check that we have valid pairs (both media and audio)
    const validPairs = rmState.matchedPairs.filter(p => p.media && p.audio);
    if (validPairs.length === 0) {
        alert('No valid media-audio pairs found. Make sure your files are numbered (e.g., 1.png with 1.mp3).');
        return;
    }

    rmState.isProcessing = true;
    rmElements.generateBtn.disabled = true;
    rmElements.outputSection.style.display = 'block';
    rmElements.resultContainer.style.display = 'none';

    rmElements.outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    rmClearLogs();
    rmAddLog('Starting Regional Mix video generation...', 'info');

    const imageCount = validPairs.filter(p => p.mediaType === 'image').length;
    const videoCount = validPairs.filter(p => p.mediaType === 'video').length;
    rmAddLog(`Found ${validPairs.length} valid pairs (${imageCount} images, ${videoCount} videos)`, 'info');
    rmUpdateProgress(5, 'Preparing files...');

    try {
        const formData = new FormData();

        // Add media files with their numbers and type info
        validPairs.forEach(pair => {
            formData.append(`media_${pair.number}`, pair.media);
            formData.append(`mediatype_${pair.number}`, pair.mediaType);
        });

        // Add audio files with their numbers
        validPairs.forEach(pair => {
            formData.append(`audio_${pair.number}`, pair.audio);
        });

        // Add the pair order and types
        const pairInfo = validPairs.map(p => ({
            number: p.number,
            mediaType: p.mediaType
        }));
        formData.append('pair_info', JSON.stringify(pairInfo));

        rmAddLog(`Uploading ${validPairs.length} media files and ${validPairs.length} audio files...`, 'info');
        rmUpdateProgress(10, 'Uploading files...');

        const response = await fetch('/api/regional-mix', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        handleRMServerMessage(data);
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        rmAddLog(`Error: ${error.message}`, 'error');
        rmUpdateProgress(0, 'Failed');
        rmState.isProcessing = false;
        rmElements.generateBtn.disabled = false;
    }
});

function handleRMServerMessage(data) {
    switch (data.type) {
        case 'log':
            rmAddLog(data.message, data.level || 'info');
            break;

        case 'progress':
            rmUpdateProgress(data.percentage, data.message);
            break;

        case 'complete':
            rmAddLog('Video generation completed successfully!', 'success');
            rmUpdateProgress(100, 'Complete!');
            showRMResult(data.videoUrl);
            rmState.isProcessing = false;
            break;

        case 'error':
            rmAddLog(`Error: ${data.message}`, 'error');
            rmUpdateProgress(0, 'Failed');
            rmState.isProcessing = false;
            rmElements.generateBtn.disabled = false;
            break;
    }
}

function showRMResult(videoUrl) {
    rmElements.resultContainer.style.display = 'block';
    rmElements.downloadLink.href = videoUrl;
    rmElements.resultContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Setup drag and drop for Regional Mix inputs
setupDragAndDrop(rmElements.imageFiles, rmElements.imagesStatus, 'images');
setupDragAndDrop(rmElements.audioFiles, rmElements.audioStatus, 'audio');

// ============================================
// Initialize
// ============================================
addLog('Application ready. Upload your files to begin.', 'info');
