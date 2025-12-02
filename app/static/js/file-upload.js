// File upload handling for Step 1

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('data_file');
    const uploadForm = document.getElementById('upload-form');
    const uploadProgress = document.getElementById('upload-progress');
    const filePreview = document.getElementById('file-preview');
    const nextBtn = document.getElementById('next-btn');
    const errorMessage = document.getElementById('error-message');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#f0f2ff';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '#f8f9ff';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('border-primary', 'bg-primary/10');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    });

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
        const file = fileInput.files[0];
        if (!file) return;

        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
            showError('error-message', 'Please upload a CSV or Excel file.');
            return;
        }

        // Upload file
        uploadFile();
    }

    function uploadFile() {
        const formData = new FormData(uploadForm);
        
        document.getElementById('upload-progress').classList.remove('hidden');
        document.getElementById('file-preview').classList.add('hidden');
        document.getElementById('error-message').classList.add('hidden');

        // Simulate progress (in real app, use XMLHttpRequest with progress event)
        let progress = 0;
        const progressBar = document.getElementById('progress-fill');
        const progressInterval = setInterval(() => {
            progress += 10;
            progressBar.value = progress;
            if (progress >= 90) clearInterval(progressInterval);
        }, 200);

        fetch(uploadForm.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                return response.text().then(text => {
                    throw new Error('Server returned non-JSON response. Check server logs.');
                });
            }
            return response.json();
        })
        .then(data => {
            clearInterval(progressInterval);
            document.getElementById('progress-fill').style.width = '100%';

            if (data.error) {
                errorMessage.textContent = data.error;
                errorMessage.style.display = 'block';
                uploadProgress.style.display = 'none';
                return;
            }

            if (data.success) {
                // Show preview
                displayFilePreview(data);
                uploadProgress.style.display = 'none';
                filePreview.style.display = 'block';
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            errorMessage.textContent = 'Error uploading file: ' + error.message;
            errorMessage.style.display = 'block';
            uploadProgress.style.display = 'none';
        });
    }

    function displayFilePreview(data) {
        // Display columns
        const columnsList = document.getElementById('columns-list');
        columnsList.innerHTML = '';
        data.columns.forEach(column => {
            const badge = document.createElement('div');
            badge.className = 'badge badge-primary badge-lg font-mono';
            badge.textContent = `{{${column}}}`;
            columnsList.appendChild(badge);
        });

        // Display data preview
        const dataPreview = document.getElementById('data-preview');
        if (data.preview && data.preview.length > 0) {
            let tableHTML = '<div class="overflow-x-auto"><table class="table table-zebra w-full"><thead><tr>';
            data.columns.forEach(col => {
                tableHTML += `<th class="font-semibold">${col}</th>`;
            });
            tableHTML += '</tr></thead><tbody>';

            data.preview.forEach(row => {
                tableHTML += '<tr>';
                data.columns.forEach(col => {
                    tableHTML += `<td>${row[col] || ''}</td>`;
                });
                tableHTML += '</tr>';
            });
            tableHTML += '</tbody></table></div>';
            dataPreview.innerHTML = tableHTML;
        }

        // Store project ID for navigation
        nextBtn.onclick = () => {
            window.location.href = `/step2/${data.project_id}/`;
        };
    }

    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

