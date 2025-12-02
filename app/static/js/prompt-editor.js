// Prompt editor with Gemini integration for Step 2

document.addEventListener('DOMContentLoaded', function() {
    const promptEditor = document.getElementById('prompt-editor');
    const geminiSuggestBtn = document.getElementById('gemini-suggest-btn');
    const savePromptBtn = document.getElementById('save-prompt-btn');
    const nextToVideosBtn = document.getElementById('next-to-videos-btn');
    const geminiLoading = document.getElementById('gemini-loading');
    const errorMessage = document.getElementById('error-message');

    // Get project ID from global variable set in template
    const projectId = window.projectId || getProjectIdFromURL();

    // Insert field function (called from template)
    window.insertField = function(fieldName) {
        const placeholder = `{{${fieldName}}}`;
        const textarea = promptEditor;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const before = text.substring(0, start);
        const after = text.substring(end, text.length);
        
        textarea.value = before + placeholder + after;
        textarea.focus();
        textarea.setSelectionRange(start + placeholder.length, start + placeholder.length);
    };

    // Highlight fields in prompt (visual feedback)
    function highlightFields() {
        // This could be enhanced with a rich text editor
        // For now, we'll just validate on blur
    }

    // Save prompt
    savePromptBtn.addEventListener('click', () => {
        const template = promptEditor.value;
        
        fetch(`/api/prompt/save/${projectId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ template: template })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError('error-message', data.error);
            } else {
                showSuccess('Prompt saved successfully!');
            }
        })
        .catch(error => {
            showError('error-message', 'Error saving prompt: ' + error.message);
        });
    });

    // Get Gemini suggestion
    geminiSuggestBtn.addEventListener('click', () => {
        const template = promptEditor.value.trim();
        const fields = window.fields || [];

        if (!template) {
            showError('error-message', 'Please write a prompt first.');
            return;
        }

        if (!fields || fields.length === 0) {
            showError('error-message', 'No fields available. Please upload a file first.');
            return;
        }

        document.getElementById('gemini-loading').classList.remove('hidden');
        document.getElementById('error-message').classList.add('hidden');

        fetch('/api/gemini/suggest-prompt/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                template: template,
                fields: Array.isArray(fields) ? fields : []
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('gemini-loading').classList.add('hidden');
            
            if (data.error) {
                showError('error-message', data.error);
            } else if (data.suggested_prompt) {
                promptEditor.value = data.suggested_prompt;
                showSuccess('Prompt enhanced by Gemini!');
            } else {
                showError('error-message', 'No suggestion received from Gemini');
            }
        })
        .catch(error => {
            document.getElementById('gemini-loading').classList.add('hidden');
            showError('error-message', 'Error getting suggestion: ' + error.message);
        });
    });

    // Next to videos
    nextToVideosBtn.addEventListener('click', () => {
        // Save prompt first
        const template = promptEditor.value;
        
        fetch(`/api/prompt/save/${projectId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ template: template })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError('error-message', data.error);
            } else {
                window.location.href = `/step3/${projectId}/`;
            }
        })
        .catch(error => {
            showError('error-message', 'Error saving prompt: ' + error.message);
        });
    });

    function getProjectIdFromURL() {
        const match = window.location.pathname.match(/step2\/(\d+)/);
        return match ? match[1] : null;
    }

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

    function showError(containerId, message) {
        const container = document.getElementById(containerId);
        const errorText = document.getElementById('error-text');
        if (container && errorText) {
            errorText.textContent = message;
            container.classList.remove('hidden');
        }
    }

    function showSuccess(message) {
        // Simple success feedback
        const btn = savePromptBtn;
        const originalText = btn.textContent;
        btn.textContent = '✓ Saved!';
        btn.style.background = '#28a745';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    }
});


