// UI Elements
const urlInput = document.getElementById('urlInput');
const checkBtn = document.getElementById('checkBtn');
const btnText = document.getElementById('btnText');
const errorMsg = document.getElementById('errorMsg');
const qualitySection = document.getElementById('qualitySection');
const qualityList = document.getElementById('qualityList');
const modeSection = document.getElementById('modeSection');
const modeBtns = document.querySelectorAll('.mode-btn');
const downloadBtn = document.getElementById('downloadBtn');
const filenameInput = document.getElementById('filenameInput');
const progressSection = document.getElementById('progressSection');
const progressAction = document.getElementById('progressAction');
const progressFill = document.getElementById('progressFill');
const progressPercent = document.getElementById('progressPercent');
const progressSpeed = document.getElementById('progressSpeed');
const downloadLinkContainer = document.getElementById('downloadLinkContainer');

// State
let selectedFormat = null;
let selectedMode = 'direct';
let currentFormats = [];
let downloadId = null;

// Helper: Format bytes
function humanbytes(size) {
    if (!size) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let i = 0;
    while (size >= 1024 && i < units.length - 1) {
        size /= 1024;
        i++;
    }
    return i === 0 ? `${size} ${units[i]}` : `${size.toFixed(2)} ${units[i]}`;
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
}

function hideError() {
    errorMsg.classList.add('hidden');
}

// Step 1: Check URL
checkBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return showError("Please enter a valid URL");

    hideError();
    qualitySection.classList.add('hidden');
    modeSection.classList.add('hidden');
    progressSection.classList.add('hidden');

    btnText.innerHTML = '<span class="loader"></span> Checking...';
    checkBtn.disabled = true;

    try {
        const response = await fetch('/api/formats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to fetch media details");
        }

        currentFormats = data.formats || [];
        const suggestedTitle = data.title || "";
        renderQualityButtons(currentFormats, suggestedTitle);

    } catch (err) {
        showError(err.message);
    } finally {
        btnText.textContent = 'Check URL';
        checkBtn.disabled = false;
    }
});

// Step 2: Render Quality Buttons
function renderQualityButtons(formats, title) {
    qualityList.innerHTML = '';
    selectedFormat = null;

    if (title) {
        filenameInput.value = title.replace(/[\\/*?:"<>|]/g, "") + ".mp4";
    }

    if (formats.length === 0) {
        // Direct link - skip to mode selection
        selectedFormat = "direct";
        qualitySection.classList.add('hidden');
        modeSection.classList.remove('hidden');
        return;
    }

    formats.forEach(f => {
        const btn = document.createElement('button');
        btn.className = 'quality-btn';
        btn.textContent = `${f.resolution} (${humanbytes(f.filesize)})`;
        btn.dataset.id = f.format_id;

        btn.addEventListener('click', () => {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedFormat = f.format_id;
            modeSection.classList.remove('hidden');
        });

        qualityList.appendChild(btn);
    });

    // Add Best Quality button
    const bestFmt = formats[0].format_id;
    const bestBtn = document.createElement('button');
    bestBtn.className = 'quality-btn';
    bestBtn.textContent = '✨ Best Quality';
    bestBtn.dataset.id = `best_${bestFmt}`;
    bestBtn.style.gridColumn = "1 / -1";

    bestBtn.addEventListener('click', () => {
        document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('selected'));
        bestBtn.classList.add('selected');
        selectedFormat = `best_${bestFmt}`;
        modeSection.classList.remove('hidden');
    });

    qualityList.appendChild(bestBtn);
    qualitySection.classList.remove('hidden');
}

// Step 3: Mode Selection
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        modeBtns.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedMode = btn.dataset.mode;
    });
});

// Step 4: Start Download
downloadBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return showError("Please enter a URL");

    downloadBtn.innerHTML = '<span class="loader"></span> Starting...';
    downloadBtn.disabled = true;

    try {
        const response = await fetch('/api/web-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                format_id: selectedFormat,
                mode: selectedMode,
                filename: filenameInput.value.trim()
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to start download");
        }

        downloadId = data.download_id;
        modeSection.classList.add('hidden');
        progressSection.classList.remove('hidden');
        startProgressPolling();

    } catch (err) {
        showError(err.message);
        downloadBtn.textContent = 'Start Download';
        downloadBtn.disabled = false;
    }
});

// Step 5: Progress Polling
function startProgressPolling() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${downloadId}`);
            if (!response.ok) {
                clearInterval(pollInterval);
                return;
            }

            const data = await response.json();

            if (data.status === 'error') {
                clearInterval(pollInterval);
                progressAction.textContent = `Error: ${data.message}`;
                progressAction.style.color = 'var(--danger)';
                return;
            }

            if (data.status === 'complete') {
                clearInterval(pollInterval);
                progressAction.textContent = 'Download Complete!';
                progressFill.style.width = '100%';
                progressPercent.textContent = '100%';

                // Show download link
                downloadLinkContainer.innerHTML = `
                    <a href="/api/download-file/${downloadId}" class="download-link" download>
                        📥 Download File
                    </a>
                `;
                return;
            }

            // Update progress
            progressAction.textContent = data.action || 'Downloading...';
            progressFill.style.width = `${data.percentage || 0}%`;
            progressPercent.textContent = `${data.percentage || 0}%`;
            progressSpeed.textContent = data.speed || '-- MB/s';

        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 1000);
}

// Allow Enter key to trigger check
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        checkBtn.click();
    }
});
