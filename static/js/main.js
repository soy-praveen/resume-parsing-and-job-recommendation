// main.js - Client-side functionality for ResuMatch application

document.addEventListener('DOMContentLoaded', function() {
    // Resume upload form handling
    const resumeForm = document.getElementById('resume-form');
    const resumeInput = document.getElementById('resume');
    const dropzone = document.getElementById('dropzone');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    const submitBtn = document.getElementById('submit-btn');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Handle file selection via input
    if (resumeInput) {
        resumeInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            handleFileSelection(file);
        });
    }

    // Handle drag and drop
    if (dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropzone.addEventListener('drop', function(e) {
            const file = e.dataTransfer.files[0];
            resumeInput.files = e.dataTransfer.files;
            handleFileSelection(file);
        });
    }

    // Handle file removal
    if (removeFile) {
        removeFile.addEventListener('click', function() {
            resumeInput.value = '';
            fileInfo.classList.add('d-none');
            dropzone.classList.remove('has-file');
        });
    }

    // Handle form submission
    if (resumeForm) {
        resumeForm.addEventListener('submit', function(e) {
            if (!resumeInput.files.length) {
                e.preventDefault();
                alert('Please select a resume file first.');
                return;
            }

            // Show loading spinner on submit
            submitBtn.disabled = true;
            loadingSpinner.classList.remove('d-none');
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing...';
        });
    }

    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropzone.classList.add('border-info');
    }

    function unhighlight() {
        dropzone.classList.remove('border-info');
    }

    function handleFileSelection(file) {
        if (!file) return;

        // Check if file is PDF or DOCX
        const fileType = file.type;
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

        if (!validTypes.includes(fileType)) {
            alert('Please upload a PDF or DOCX file');
            resumeInput.value = '';
            return;
        }

        // Update UI with file info
        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        dropzone.classList.add('has-file');
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
});
