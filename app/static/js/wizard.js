// Wizard navigation and progress tracking with DaisyUI

document.addEventListener('DOMContentLoaded', function() {
    // Initialize wizard state
    const currentStep = getCurrentStep();
    updateProgress(currentStep);
});

function getCurrentStep() {
    const path = window.location.pathname;
    if (path.includes('step1')) return 1;
    if (path.includes('step2')) return 2;
    if (path.includes('step3')) return 3;
    return 1;
}

function updateProgress(currentStep) {
    // Update DaisyUI steps
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, index) => {
        step.classList.remove('step-primary');
        if (index < currentStep) {
            step.classList.add('step-primary');
        }
    });
    console.log('Current step:', currentStep);
}

// Utility function to show error messages
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    const errorText = document.getElementById('error-text');
    if (container) {
        if (errorText) {
            errorText.textContent = message;
        } else {
            container.textContent = message;
        }
        container.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            container.classList.add('hidden');
        }, 5000);
    }
}

// Utility function to show success messages
function showSuccess(message) {
    // You can implement a toast notification system here
    console.log('Success:', message);
}

