/**
 * NexusLIMS Detail Page - Progress Tracker Module
 *
 * Manages UI updates for download progress and status messages
 */

(function($, window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.Downloads = window.NexusLIMSDetail.Downloads || {};

    // jQuery selectors cached
    const $progressBar = $('#progress_bar');
    const $progressBarInner = $('#progress_bar .progress-bar');
    const $downloadResult = $('#download-result');
    const $downloadExtra = $('#download-extra');
    const $btnCancelRow = $('#btn-cancel-row');
    const $progressbarRow = $('#progressbar-row');
    const $dlResultRow = $('#dl-result-row');
    const $dlExtraRow = $('#dl-extra-row');

    /**
     * Reset and show the message area
     */
    function resetMessage() {
        if (!$downloadResult.is(':visible')) {
            $dlResultRow.slideDown();
        }
        $downloadResult.text(' ');
    }

    /**
     * Show a message with a specific alert type
     * @param {string} text - Message text
     * @param {string} type - Bootstrap alert type (info, warning, danger, success)
     */
    function showMessage(text, type) {
        resetMessage();
        $downloadResult
            .removeClass('alert-warning alert-success alert-info alert-danger')
            .addClass('alert alert-' + type)
            .text(text);
    }

    /**
     * Show an additional warning or info message
     * @param {string} text - Message text
     * @param {string} type - Bootstrap alert type
     */
    function showExtraMessage(text, type) {
        $dlExtraRow.slideDown();
        $downloadExtra
            .removeClass('alert-warning alert-success alert-info alert-danger')
            .addClass('alert alert-' + type)
            .text(text);
    }

    /**
     * Hide the extra message area
     */
    function hideExtraMessage() {
        $dlExtraRow.slideUp();
    }

    /**
     * Show a warning message
     * @param {string} text - Warning text
     */
    function showWarning(text) {
        showMessage(text, 'warning');
    }

    /**
     * Show an error message
     * @param {string} text - Error text
     */
    function showError(text) {
        showMessage(text, 'danger');
    }

    /**
     * Show a success message
     * @param {string} text - Success text
     */
    function showSuccess(text) {
        showMessage(text, 'success');
    }

    /**
     * Show an info message
     * @param {string} text - Info text
     */
    function showInfo(text) {
        showMessage(text, 'info');
    }

    /**
     * Update progress bar percentage
     * @param {number} percent - Percentage (0-100)
     */
    function updatePercent(percent) {
        $progressBar
            .addClass('active')
            .closest('.row').slideDown();

        $progressBarInner
            .attr('aria-valuenow', percent)
            .removeClass('progress-bar-warning progress-bar-success progress-bar-danger bg-warning bg-success bg-danger')
            .addClass('progress-bar-info bg-info progress-bar-striped progress-bar-animated')
            .css({
                width: percent + '%',
                'min-width': '5%'
            })
            .text(percent + '%');
    }

    /**
     * Update progress bar with bytes downloaded and total
     * @param {number} bytesDownloaded - Bytes downloaded so far
     * @param {number} totalToDownload - Total bytes to download
     */
    function updateProgress(bytesDownloaded, totalToDownload) {
        const percent = Math.floor((bytesDownloaded / totalToDownload) * 100);
        updatePercent(percent);

        // Update progress message
        const humanBytes = window.NexusLIMSDetail.humanFileSize(bytesDownloaded);
        const humanTotal = window.NexusLIMSDetail.humanFileSize(totalToDownload);
        const msg = (bytesDownloaded === 0) ?
            'Download is starting, please be patient...' :
            'Downloaded ' + humanBytes + ' out of ' + humanTotal + '.';

        showInfo(msg);
    }

    /**
     * Set progress bar to error state
     */
    function setErrorProgress() {
        $progressBar
            .removeClass('active')
            .closest('.row').slideDown();

        $progressBarInner
            .attr('aria-valuenow', 100)
            .removeClass('progress-bar-info progress-bar-success progress-bar-warning bg-info bg-success bg-warning active progress-bar-striped progress-bar-animated')
            .addClass('progress-bar-danger bg-danger')
            .css({
                width: '100%',
                'min-width': '5%'
            })
            .text('Error!');
    }

    /**
     * Set progress bar to finished state
     */
    function setFinishedProgress() {
        $progressBar
            .removeClass('active')
            .closest('.row').slideDown();

        $progressBarInner
            .attr('aria-valuenow', 100)
            .removeClass('progress-bar-info progress-bar-danger progress-bar-warning bg-info bg-danger bg-warning active progress-bar-striped progress-bar-animated')
            .addClass('progress-bar-success bg-success')
            .css({
                width: '100%',
                'min-width': '5%'
            })
            .text('Finished!');
    }

    /**
     * Reset all UI elements to initial state
     */
    function reset() {
        updatePercent(0);
        $downloadResult.text('');
        $downloadExtra.text('');
        $progressbarRow.hide();
        $dlResultRow.hide();
        $dlExtraRow.hide();
        $btnCancelRow.hide();
    }

    /**
     * Show cancel button
     */
    function showCancelButton() {
        $btnCancelRow.slideDown();
    }

    /**
     * Hide cancel button
     */
    function hideCancelButton() {
        $btnCancelRow.slideUp();
    }

    /**
     * Mark download as finished (success)
     */
    function finish() {
        setFinishedProgress();
        showSuccess('Finished downloading all files!');
        hideExtraMessage();
        hideCancelButton();

        // Hide progress bar after 3 seconds
        setTimeout(function() {
            $progressbarRow.slideUp();
        }, 3000);
    }

    /**
     * Mark download as errored
     */
    function error() {
        setErrorProgress();
        hideExtraMessage();
        hideCancelButton();
    }

    // Public API
    window.NexusLIMSDetail.Downloads.ProgressTracker = {
        reset,
        updateProgress,
        updatePercent,
        showMessage,
        showExtraMessage,
        hideExtraMessage,
        showWarning,
        showError,
        showSuccess,
        showInfo,
        showCancelButton,
        hideCancelButton,
        finish,
        error
    };

})(jQuery, window);
