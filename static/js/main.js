// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeFileBtn = document.getElementById('removeFile');
const simplifyBtn = document.getElementById('simplifyBtn');
const progressSection = document.getElementById('progressSection');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const errorResetBtn = document.getElementById('errorResetBtn');

let selectedFile = null;
let downloadUrl = null;

// Upload area click handler
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Drag and drop handlers
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

// Handle file selection
function handleFile(file) {
    const validTypes = ['application/pdf', 'text/plain'];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a PDF or TXT file.');
        return;
    }

    if (file.size > maxSize) {
        showError('File is too large. Maximum size is 50MB.');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    simplifyBtn.disabled = false;
}

// Remove file handler
removeFileBtn.addEventListener('click', () => {
    resetForm();
});

// Simplify button handler
simplifyBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const format = document.querySelector('input[name="format"]:checked').value;

    // Hide previous results/errors
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';

    // Show progress
    progressSection.style.display = 'block';
    simplifyBtn.disabled = true;

    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('format', format);

    try {
        progressText.textContent = 'Uploading file...';

        const response = await fetch('/api/simplify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'An error occurred while processing your file.');
        }

        if (data.success) {
            downloadUrl = data.download_url;
            progressSection.style.display = 'none';
            resultSection.style.display = 'block';

            // Display SCP commands if available
            if (data.scp_commands) {
                const scpSection = document.getElementById('scpCommandsSection');
                const scpNote = document.getElementById('scpNote');
                const scpCommandSimplified = document.getElementById('scpCommandSimplified');
                const scpCommandOriginal = document.getElementById('scpCommandOriginal');

                scpNote.textContent = data.scp_commands.note || '';
                scpCommandSimplified.textContent = data.scp_commands.simplified || '';
                scpCommandOriginal.textContent = data.scp_commands.original || '';
                scpSection.style.display = 'block';
            }
        } else {
            throw new Error(data.error || 'Unknown error occurred.');
        }

    } catch (error) {
        console.error('Error:', error);
        progressSection.style.display = 'none';
        showError(error.message);
    }
});

// Download button handler
downloadBtn.addEventListener('click', () => {
    if (downloadUrl) {
        window.location.href = downloadUrl;
    }
});

// Reset button handlers
resetBtn.addEventListener('click', resetForm);
errorResetBtn.addEventListener('click', () => {
    errorSection.style.display = 'none';
    resetForm();
});

// Reset form function
function resetForm() {
    selectedFile = null;
    downloadUrl = null;
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    simplifyBtn.disabled = true;

    // Hide SCP commands section
    const scpSection = document.getElementById('scpCommandsSection');
    if (scpSection) {
        scpSection.style.display = 'none';
    }
}

// Show error function
function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    simplifyBtn.disabled = false;
}
