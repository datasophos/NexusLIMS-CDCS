/**
 * NexusLIMS Main JavaScript
 * 
 * Central location for all NexusLIMS customizations.
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeNexusLIMS();
    });

    /**
     * Main initialization function
     */
    function initializeNexusLIMS() {
        console.log('NexusLIMS initializing...');
        
        // Initialize components
        initializeToolbar();
        initializeDownloadButtons();
        initializeTooltips();
        initializeTutorial();
        
        console.log('NexusLIMS initialized');
    }

    /**
     * Initialize custom toolbar
     */
    function initializeToolbar() {
        // Edit button
        const editBtn = document.getElementById('nexuslims-edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', function(e) {
                e.preventDefault();
                // Open edit in new window
                const editUrl = this.dataset.editUrl;
                if (editUrl) {
                    window.open(editUrl, '_blank');
                }
            });
        }

        // Copy PID button
        const copyPidBtn = document.getElementById('nexuslims-copy-pid');
        if (copyPidBtn) {
            copyPidBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const pid = this.dataset.pid;
                if (pid) {
                    copyToClipboard(pid);
                    showNotification('PID copied to clipboard');
                }
            });
        }
    }

    /**
     * Initialize download buttons
     */
    function initializeDownloadButtons() {
        const downloadSingle = document.getElementById('nexuslims-download-single');
        const downloadAll = document.getElementById('nexuslims-download-all');

        if (downloadSingle) {
            downloadSingle.addEventListener('click', handleDownloadSingle);
        }

        if (downloadAll) {
            downloadAll.addEventListener('click', handleDownloadAll);
        }
    }

    /**
     * Handle single file download
     */
    function handleDownloadSingle(e) {
        e.preventDefault();
        const downloadUrl = this.dataset.downloadUrl;
        if (downloadUrl) {
            window.location.href = downloadUrl;
        }
    }

    /**
     * Handle download all files as ZIP
     */
    function handleDownloadAll(e) {
        e.preventDefault();
        const downloadUrl = this.dataset.downloadUrl;
        if (downloadUrl) {
            showNotification('Preparing download...');
            // Use StreamSaver or fetch API for large files
            window.location.href = downloadUrl;
        }
    }

    /**
     * Initialize tooltips (Bootstrap 5 compatible)
     */
    function initializeTooltips() {
        // Check if Bootstrap is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="tooltip"]')
            );
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl, {
                    trigger: 'hover'
                });
            });
        }
    }

    /**
     * Initialize Shepherd.js tutorial if available
     */
    function initializeTutorial() {
        const tutorialLink = document.getElementById('homepage-tutorial');
        if (tutorialLink && typeof Shepherd !== 'undefined') {
            tutorialLink.addEventListener('click', function(e) {
                e.preventDefault();
                startTutorial();
            });
        }
    }

    /**
     * Start the interactive tutorial
     */
    function startTutorial() {
        // Tutorial implementation using Shepherd.js
        // This would be populated with actual tutorial steps
        console.log('Tutorial started');
    }

    /**
     * Copy text to clipboard
     */
    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
    }

    /**
     * Show notification to user
     */
    function showNotification(message, type = 'info') {
        // Simple notification - could be replaced with Bootstrap toast
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Optional: Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Export to global scope if needed
    window.NexusLIMS = {
        copyToClipboard: copyToClipboard,
        showNotification: showNotification
    };

})();
