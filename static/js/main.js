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

    // Debug message to check if the script is loading
    console.log('ResuMatch JS loaded successfully');

    // Set up click handler for the entire dropzone to trigger file input
    if (dropzone) {
        dropzone.addEventListener('click', function(e) {
            // Prevent clicks on buttons inside the dropzone from triggering this
            if (e.target.tagName.toLowerCase() !== 'button' && 
                e.target.tagName.toLowerCase() !== 'input' &&
                e.target.tagName.toLowerCase() !== 'label') {
                resumeInput.click();
            }
        });
    }

    // Handle file selection via input
    if (resumeInput) {
        console.log('File input element found');
        resumeInput.addEventListener('change', function(e) {
            console.log('File input change event fired');
            const file = e.target.files[0];
            if (file) {
                console.log('File selected:', file.name);
                handleFileSelection(file);
            }
        });
    } else {
        console.error('File input element not found');
    }

    // Handle drag and drop
    if (dropzone) {
        console.log('Dropzone element found');
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
            console.log('File dropped on dropzone');
            const file = e.dataTransfer.files[0];
            if (file) {
                try {
                    // This approach may not work in all browsers
                    resumeInput.files = e.dataTransfer.files;
                    console.log('File attached to input via dataTransfer');
                } catch (err) {
                    console.error('Error setting files:', err);
                    // Alternative approach: trigger a change event manually
                    const dT = new DataTransfer();
                    dT.items.add(file);
                    resumeInput.files = dT.files;
                    console.log('File attached to input via DataTransfer');
                }
                handleFileSelection(file);
            }
        });
    } else {
        console.error('Dropzone element not found');
    }

    // Handle file removal
    if (removeFile) {
        removeFile.addEventListener('click', function(e) {
            console.log('Remove file button clicked');
            e.preventDefault();
            e.stopPropagation(); // Prevent this from triggering the dropzone click
            resumeInput.value = '';
            fileInfo.classList.add('d-none');
            dropzone.classList.remove('has-file');
        });
    }

    // Handle form submission
    if (resumeForm) {
        console.log('Form element found');
        resumeForm.addEventListener('submit', function(e) {
            console.log('Form submit event fired');
            
            if (!resumeInput.files.length) {
                console.log('No file selected, preventing form submission');
                e.preventDefault();
                alert('Please select a resume file first.');
                return;
            }

            console.log('File selected, proceeding with form submission');
            
            // Show loading spinner on submit
            submitBtn.disabled = true;
            if (loadingSpinner) {
                loadingSpinner.classList.remove('d-none');
            }
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing...';
        });
    } else {
        console.error('Form element not found');
    }

    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        console.log('Highlighting dropzone');
        dropzone.classList.add('border-info');
    }

    function unhighlight() {
        console.log('Unhighlighting dropzone');
        dropzone.classList.remove('border-info');
    }

    function handleFileSelection(file) {
        if (!file) {
            console.error('No file provided to handleFileSelection');
            return;
        }

        console.log('Handling file selection:', file.name, file.type);

        // Check if file is PDF or DOCX
        const fileType = file.type;
        const fileExtension = file.name.split('.').pop().toLowerCase();
        console.log('File type:', fileType, 'Extension:', fileExtension);
        
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const validExtensions = ['pdf', 'docx'];

        // Check both MIME type and extension for better compatibility
        if (!validTypes.includes(fileType) && !validExtensions.includes(fileExtension)) {
            console.error('Invalid file type:', fileType);
            alert('Please upload a PDF or DOCX file');
            resumeInput.value = '';
            return;
        }

        // Update UI with file info
        if (fileName && fileInfo) {
            fileName.textContent = file.name;
            fileInfo.classList.remove('d-none');
            dropzone.classList.add('has-file');
            console.log('UI updated with file info');
        } else {
            console.error('File info UI elements not found');
        }
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // Explicitly check if the "Browse Files" button works
    const browseButton = document.querySelector('label[for="resume"]');
    if (browseButton) {
        console.log('Browse button found');
        browseButton.addEventListener('click', function(e) {
            console.log('Browse button clicked');
            // The label's 'for' attribute should automatically trigger the file input
        });
    } else {
        console.error('Browse button not found');
    }
});
