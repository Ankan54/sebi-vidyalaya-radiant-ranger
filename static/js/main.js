// SEBI Vidyalaya Main JavaScript

// Global variables
let isConnected = false;
let currentTheme = 'light';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('SEBI Vidyalaya initialized');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize theme
    initializeTheme();
    
    // Initialize accessibility features
    initializeAccessibility();
    
    // Initialize error handling
    initializeErrorHandling();
    
    // Check browser compatibility
    checkBrowserCompatibility();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Theme management
function initializeTheme() {
    const savedTheme = localStorage.getItem('sebi-theme') || 'light';
    setTheme(savedTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sebi-theme', theme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Accessibility features
function initializeAccessibility() {
    // Add skip links
    addSkipLinks();
    
    // Enhanced keyboard navigation
    enhanceKeyboardNavigation();
    
    // Focus management
    manageFocus();
    
    // Screen reader announcements
    initializeScreenReaderSupport();
}

function addSkipLinks() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link position-absolute start-0';
    skipLink.style.transform = 'translateY(-100%)';
    skipLink.style.transition = 'transform 0.3s';
    skipLink.textContent = 'Skip to main content';
    
    skipLink.addEventListener('focus', () => {
        skipLink.style.transform = 'translateY(0)';
    });
    
    skipLink.addEventListener('blur', () => {
        skipLink.style.transform = 'translateY(-100%)';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
}

function enhanceKeyboardNavigation() {
    // Add keyboard support for custom elements
    document.addEventListener('keydown', function(event) {
        // Enter key activates buttons and links
        if (event.key === 'Enter') {
            const target = event.target;
            if (target.classList.contains('certification-card')) {
                target.click();
            }
        }
        
        // Escape key closes modals
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) modal.hide();
            }
        }
    });
}

function manageFocus() {
    // Trap focus in modals
    document.addEventListener('shown.bs.modal', function(event) {
        const modal = event.target;
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }
    });
}

function initializeScreenReaderSupport() {
    // Create live region for announcements
    const liveRegion = document.createElement('div');
    liveRegion.id = 'live-region';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'visually-hidden';
    document.body.appendChild(liveRegion);
}

function announceToScreenReader(message) {
    const liveRegion = document.getElementById('live-region');
    if (liveRegion) {
        liveRegion.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
}

// Error handling
function initializeErrorHandling() {
    // Global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        showNotification('An unexpected error occurred. Please refresh the page.', 'error');
    });
    
    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showNotification('A network error occurred. Please check your connection.', 'error');
    });
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${getBootstrapAlertClass(type)} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    // Announce to screen readers
    announceToScreenReader(message);
}

function getBootstrapAlertClass(type) {
    const mapping = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return mapping[type] || 'info';
}

function getNotificationIcon(type) {
    const mapping = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return mapping[type] || 'info-circle';
}

// Browser compatibility check
function checkBrowserCompatibility() {
    const requiredFeatures = [
        'fetch',
        'Promise',
        'localStorage',
        'addEventListener'
    ];
    
    const missingFeatures = requiredFeatures.filter(feature => !window[feature]);
    
    if (missingFeatures.length > 0) {
        showNotification(
            'Your browser may not support all features. Please consider updating to a modern browser.',
            'warning',
            10000
        );
    }
    
    // Check for WebRTC support (for voice features)
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('WebRTC not supported - voice features may be limited');
    }
    
    // Check for Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech Recognition not supported');
    }
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Performance monitoring
function measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    
    console.log(`Performance [${name}]: ${(end - start).toFixed(2)}ms`);
    
    return result;
}

// Local storage utilities
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// Network status monitoring
function initializeNetworkMonitoring() {
    if ('navigator' in window && 'onLine' in navigator) {
        window.addEventListener('online', function() {
            showNotification('Connection restored', 'success', 3000);
            announceToScreenReader('Internet connection restored');
        });
        
        window.addEventListener('offline', function() {
            showNotification('No internet connection', 'warning', 0);
            announceToScreenReader('Internet connection lost');
        });
    }
}

// Initialize network monitoring when DOM is ready
document.addEventListener('DOMContentLoaded', initializeNetworkMonitoring);

// Export for use in other modules
window.SEBIVidyalaya = {
    showNotification,
    announceToScreenReader,
    formatBytes,
    debounce,
    throttle,
    measurePerformance,
    saveToLocalStorage,
    loadFromLocalStorage
};
