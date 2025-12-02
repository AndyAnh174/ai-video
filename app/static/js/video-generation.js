// Video generation and status polling for Step 3

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-generation-btn');
    const generationProgress = document.getElementById('generation-progress');
    const overallProgressFill = document.getElementById('overall-progress-fill');
    const progressText = document.getElementById('progress-text');
    const videosGrid = document.getElementById('videos-grid');

    const projectId = window.projectId || getProjectIdFromURL();
    const totalRows = window.totalRows || 0;

    let statusPollingInterval = null;

    // Start generation
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            startGeneration();
        });
    }

    function startGeneration() {
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> Starting...';
        document.getElementById('generation-progress').classList.remove('hidden');

        fetch(`/api/veo/start/${projectId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
                startBtn.disabled = false;
                startBtn.textContent = 'Start Generating Videos';
                return;
            }

            startBtn.style.display = 'none';
            
            // Start polling for status updates
            startStatusPolling();
            
            // Reload page after a short delay to show new video cards
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        })
        .catch(error => {
            alert('Error starting generation: ' + error.message);
            startBtn.disabled = false;
            startBtn.textContent = 'Start Generating Videos';
        });
    }

    function startStatusPolling() {
        // Poll every 5 seconds for status updates
        statusPollingInterval = setInterval(() => {
            updateVideoStatuses();
        }, 5000);

        // Also update immediately
        updateVideoStatuses();
    }

    function updateVideoStatuses() {
        const videoCards = document.querySelectorAll('.video-card[data-video-id]');
        let completedCount = 0;
        let processingCount = 0;

        videoCards.forEach(card => {
            const videoId = card.getAttribute('data-video-id');
            const currentStatus = card.getAttribute('data-status');

            // Only poll if video is pending or processing
            if (currentStatus === 'pending' || currentStatus === 'processing') {
                fetch(`/api/veo/status/${videoId}/`)
                    .then(response => response.json())
                    .then(data => {
                        updateVideoCard(card, videoId, data);
                        
                        // Count statuses
                        if (data.status === 'completed') {
                            completedCount++;
                        } else if (data.status === 'processing') {
                            processingCount++;
                        }
                    })
                    .catch(error => {
                        console.error('Error checking status for video', videoId, error);
                    });
            } else if (currentStatus === 'completed') {
                completedCount++;
            }
        });

            // Update overall progress
        if (totalRows > 0) {
            const progress = (completedCount / totalRows) * 100;
            overallProgressFill.value = progress;
            progressText.textContent = `${completedCount} / ${totalRows} videos generated`;
        }

        // Stop polling if all videos are completed or failed
        if (completedCount + processingCount === 0 || completedCount === totalRows) {
            if (statusPollingInterval) {
                clearInterval(statusPollingInterval);
                statusPollingInterval = null;
            }
        }
    }

    function updateVideoCard(card, videoId, statusData) {
        const status = statusData.status;
        card.setAttribute('data-status', status);

        // Update status badge
        const statusBadge = card.querySelector('.badge');
        if (statusBadge) {
            let badgeClass = 'badge ';
            let badgeText = status.charAt(0).toUpperCase() + status.slice(1);
            if (status === 'pending') {
                badgeClass += 'badge-warning';
            } else if (status === 'processing') {
                badgeClass += 'badge-info gap-2';
                badgeText = '<span class="loading loading-spinner loading-xs"></span> Processing';
            } else if (status === 'completed') {
                badgeClass += 'badge-success';
            } else if (status === 'failed') {
                badgeClass += 'badge-error';
            }
            statusBadge.className = badgeClass;
            statusBadge.innerHTML = badgeText;
        }

        // Update video preview
        const videoPreview = card.querySelector('.aspect-video');
        if (status === 'completed' && statusData.video_url && videoPreview) {
            videoPreview.innerHTML = `<video class="w-full h-full rounded-lg" controls><source src="${statusData.video_url}" type="video/mp4"></video>`;
        } else if (status === 'processing' && videoPreview) {
            videoPreview.innerHTML = `
                <div class="text-center">
                    <span class="loading loading-spinner loading-lg text-primary"></span>
                    <p class="mt-2 text-sm">Generating...</p>
                </div>
            `;
        } else if (status === 'failed' && videoPreview) {
            const errorMsg = statusData.error || 'Generation failed';
            videoPreview.innerHTML = `
                <div class="text-center text-error">
                    <svg class="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <p class="text-sm">${errorMsg}</p>
                </div>
            `;
        }

        // Update error message if any
        if (statusData.error) {
            let errorText = card.querySelector('.error-text');
            if (!errorText) {
                const videoInfo = card.querySelector('.video-info');
                if (videoInfo) {
                    errorText = document.createElement('p');
                    errorText.className = 'error-text';
                    videoInfo.appendChild(errorText);
                }
            }
            if (errorText) {
                errorText.textContent = statusData.error;
            }
        }
    }

    function getProjectIdFromURL() {
        const match = window.location.pathname.match(/step3\/(\d+)/);
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

    // Auto-start polling if there are videos already
    if (videosGrid && videosGrid.querySelectorAll('.video-card').length > 0) {
        startStatusPolling();
    }
});

