// AWS Quiz Platform - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    autoHideFlashMessages();
    
    // Add smooth scrolling for anchor links
    addSmoothScrolling();
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Add keyboard shortcuts
    addKeyboardShortcuts();
    
    // Initialize tooltips if any
    initializeTooltips();
});

function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        // Auto-hide after 5 seconds (close button already exists in HTML)
        setTimeout(() => hideFlashMessage(message), 5000);
    });
}

function hideFlashMessage(message) {
    message.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => {
        if (message.parentNode) {
            message.parentNode.removeChild(message);
        }
    }, 300);
}

function addSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

function addLoadingStates() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.textContent;
                const loadingText = submitBtn.getAttribute('data-loading-text') || 'Loading...';
                
                submitBtn.innerHTML = `<div class="loading"></div> ${loadingText}`;
                submitBtn.disabled = true;
                
                // Re-enable after 10 seconds as failsafe
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });
}

function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / for help (if implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
        
        // Escape to close modals or go back
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            if (modals.length > 0) {
                modals.forEach(modal => modal.style.display = 'none');
            } else if (window.history.length > 1) {
                // Only go back if there's history
                window.history.back();
            }
        }
    });
}

function showKeyboardShortcuts() {
    // Show keyboard shortcuts help (implement if needed)
    console.log('Keyboard shortcuts help would appear here');
}

function initializeTooltips() {
    const elementsWithTooltips = document.querySelectorAll('[data-tooltip]');
    elementsWithTooltips.forEach(function(element) {
        let tooltip;
        
        element.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            if (text) {
                tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = text;
                tooltip.style.cssText = `
                    position: absolute;
                    background: var(--dark-bg);
                    color: var(--white);
                    padding: 0.5rem;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    z-index: 1000;
                    pointer-events: none;
                    border: 1px solid var(--gray-dark);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                `;
                
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
            }
        });
        
        element.addEventListener('mouseleave', function() {
            if (tooltip && tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
                tooltip = null;
            }
        });
    });
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    container.appendChild(notification);
    
    setTimeout(() => hideFlashMessage(notification), 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Animation utilities
function fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';
    
    let start = performance.now();
    
    function animate(timestamp) {
        const progress = (timestamp - start) / duration;
        element.style.opacity = Math.min(progress, 1);
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    let start = performance.now();
    const initialOpacity = parseFloat(getComputedStyle(element).opacity) || 1;
    
    function animate(timestamp) {
        const progress = (timestamp - start) / duration;
        element.style.opacity = initialOpacity - (initialOpacity * Math.min(progress, 1));
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}

// Export functions for global use
window.AWSQuiz = {
    showNotification,
    validateEmail,
    validatePassword,
    fadeIn,
    fadeOut
};