/**
 * NexusLIMS Detail Page - Download System Main Orchestrator
 *
 * Coordinates all download modules and provides public API
 */

(function($, window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.Downloads = window.NexusLIMSDetail.Downloads || {};

    // Import modules
    const FileCache = window.NexusLIMSDetail.Downloads.FileCache;
    const EmiBundler = window.NexusLIMSDetail.Downloads.EmiBundler;
    const ZipBuilder = window.NexusLIMSDetail.Downloads.ZipBuilder;
    const StreamWriter = window.NexusLIMSDetail.Downloads.StreamWriter;
    const ProgressTracker = window.NexusLIMSDetail.Downloads.ProgressTracker;
    const Detail = window.NexusLIMSDetail;

    // State
    let downloadInProgress = false;
    let currentAbortController = null;
    let wasUserCancelled = false;

    /**
     * Initialize file size cache for the page
     * @param {string[]} dataUrls - Array of data file URLs
     * @param {string[]} jsonUrls - Array of JSON metadata URLs
     * @returns {Promise<void>}
     */
    async function initialize(dataUrls, jsonUrls) {
        try {
            // Check if File System Access API is supported for ZIP downloads
            if (!StreamWriter.supportsFileSystemAccess()) {
                const errorMessage = '🚨 Warning! The NexusLIMS File Downloader will not work in your browser, ' +
                  'because it does not yet support the File System Access API. To use this tool, please ' +
                  'reopen this page in a recent version of Chrome, Edge, or Opera that supports this feature. ' +
                  'Please see <a target="_blank" href="https://caniuse.com/native-filesystem-api">this page</a> for details on ' +
                  'browser support for this feature. 🚨';
                ProgressTracker.showExtraMessage(errorMessage, 'danger');
                ProgressTracker.showWarning(
                  "You can still export the file list or download files by clicking on indivdual download buttons " +
                  "below, but for bulk downloads, please use a supported browser.");
                console.warn('File System Access API not supported:', errorMessage);

                // Remove ZIP download buttons from UI
                $('.btn-dl-all').remove();
                $('.btn-dl-selected').remove();

                return;
            }

            ProgressTracker.showInfo('Calculating download size...');

            // Get EMI URLs for .ser files
            const emiUrls = EmiBundler.getEmiUrlsForCache(dataUrls);

            // Initialize file cache with all URLs (already deduplicates in FileCache.initialize)
            await FileCache.initialize(dataUrls, jsonUrls, emiUrls);

            // Calculate and display total size (deduplicate for multi-signal datasets)
            const allUrls = [...dataUrls, ...jsonUrls, ...emiUrls.filter(u => u !== null)];
            const uniqueUrls = [...new Set(allUrls)];
            const totalSize = FileCache.getTotalSize(uniqueUrls);
            const humanSize = Detail.humanFileSize(totalSize);

            // Check if any .ser files exist
            const hasSer = dataUrls.some(url => url.endsWith('.ser'));
            let message = 'Total size of all datasets: ' + humanSize + '.';

            if (hasSer) {
                // Show warning about .emi files
                const warningMsg = 'At least one .ser file was detected in this record. ' +
                    'While not listed in this table, any associated .emi metadata file will be ' +
                    'added to the downloaded .zip archive and download size estimate.';
                ProgressTracker.showExtraMessage(warningMsg, 'warning');
            }

            ProgressTracker.showInfo(message);

            // Update DataTable with file sizes if available
            if (window.filelist_dt) {
                window.filelist_dt.rows().every(function(rowIdx) {
                    const d = this.data();
                    const url = $(d.data_dl).attr('href');
                    const size = FileCache.getSize(url);
                    if (!isNaN(size)) {
                        this.cell(rowIdx, 'size:name').data(Detail.humanFileSize(size));
                    }
                });
            }

        } catch (error) {
            console.error('Failed to initialize file cache:', error);
            ProgressTracker.showError('Failed to calculate download size: ' + error.message);
        }
    }

    /**
     * Update download size display for selected files
     * @param {string[]} dataUrls - Selected data file URLs
     * @param {string[]} jsonUrls - Selected JSON metadata URLs
     */
    function updateDownloadSize(dataUrls, jsonUrls) {
        if (!FileCache.isInitialized()) {
            console.warn('FileCache not initialized yet');
            return;
        }

        // Validate input URLs
        const hasUndefinedDataUrls = dataUrls.some(url => !url);
        const hasUndefinedJsonUrls = jsonUrls.some(url => !url);

        if (hasUndefinedDataUrls || hasUndefinedJsonUrls) {
            console.warn('updateDownloadSize called with undefined URLs');
            console.warn('Data URLs:', dataUrls);
            console.warn('JSON URLs:', jsonUrls);
            ProgressTracker.showWarning('Some files have missing download links.');
            return;
        }

        // Get EMI URLs for selected .ser files
        const emiUrls = EmiBundler.getEmiUrlsForCache(dataUrls);

        // Deduplicate URLs before calculating total size
        // (multi-signal datasets can reference the same files)
        const allUrls = [...dataUrls, ...jsonUrls, ...emiUrls.filter(u => u !== null)];
        const uniqueUrls = [...new Set(allUrls)];
        const totalSize = FileCache.getTotalSize(uniqueUrls);
        const humanSize = Detail.humanFileSize(totalSize);

        if (dataUrls.length === 0) {
            ProgressTracker.showInfo('No files selected.');
        } else {
            ProgressTracker.showInfo('Total download size: ' + humanSize + '.');
        }
    }

    /**
     * Main download function
     * @param {string[]} dataUrls - Array of data file URLs to download
     * @param {string[]} jsonUrls - Array of JSON metadata URLs
     * @param {string[]} paths - Array of file paths for ZIP structure
     * @param {string} zipTitle - Name for the ZIP file
     */
    async function download(dataUrls, jsonUrls, paths, zipTitle) {
        // Check browser compatibility
        // Check if File System Access API is supported for ZIP downloads
        if (!StreamWriter.supportsFileSystemAccess()) {
            const errorMessage = 'File System Access API is not supported in your browser. ' +
                'ZIP downloads require Chrome, Edge, or other modern browsers that support this feature. ' +
                'Please see <a target="_blank" href="https://caniuse.com/native-filesystem-api">this page</a> for details on ' +
                'browser support for this feature.';
            ProgressTracker.showError(errorMessage);
            console.warn('File System Access API not supported:', errorMessage);
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');
            return;
        }

        // File System Access API provides ZIP download functionality on Chrome/Edge
        // We already checked for FSA support above, so we can proceed with confidence

        if (downloadInProgress) {
            console.warn('Download already in progress');
            return;
        }

        try {
            downloadInProgress = true;
            wasUserCancelled = false; // Reset cancellation flag

            // Reset UI
            ProgressTracker.reset();
            ProgressTracker.updatePercent(0);
            ProgressTracker.showCancelButton();

            // Prepare file list with EMI files
            const fileList = EmiBundler.prepareFileList(dataUrls, jsonUrls, paths);

            console.info(`Downloading ${fileList.length} datasets`);

            // Build the complete file array with URLs for ZIP downloads
            let fileListWithUrls;
            let allUrls;
            let totalSize;

            try {
                console.debug('Starting file list processing...');
                console.debug('Input dataUrls:', dataUrls);
                console.debug('Input jsonUrls:', jsonUrls);
                console.debug('Input paths:', paths);

                // Validate input arrays
                if (!dataUrls || !jsonUrls || !paths) {
                    throw new Error('Input arrays are undefined');
                }

                if (dataUrls.length === 0 || jsonUrls.length === 0 || paths.length === 0) {
                    throw new Error('Input arrays are empty');
                }

                // Check for undefined URLs in the input arrays
                const hasUndefinedDataUrls = dataUrls.some(url => !url);
                const hasUndefinedJsonUrls = jsonUrls.some(url => !url);
                const hasUndefinedPaths = paths.some(path => !path);

                if (hasUndefinedDataUrls || hasUndefinedJsonUrls || hasUndefinedPaths) {
                    console.error('Input arrays contain undefined values:');
                    console.error('dataUrls:', dataUrls);
                    console.error('jsonUrls:', jsonUrls);
                    console.error('paths:', paths);
                    throw new Error('Input arrays contain undefined values');
                }

                // Validate input fileList
                if (!fileList || fileList.length === 0) {
                    throw new Error('Input fileList is empty or undefined');
                }

                // Check for undefined URLs in the input
                const hasUndefinedUrls = fileList.some(file => !file.dataUrl || !file.jsonUrl);
                if (hasUndefinedUrls) {
                    console.warn('File list contains entries with undefined URLs:', fileList);
                }

                console.debug('Calling ZipBuilder.buildZipFileArray with', fileList.length, 'files');
                const allZipFiles = ZipBuilder.buildZipFileArray(fileList);
                fileListWithUrls = allZipFiles; // This contains the actual file objects with URLs

                console.debug('File list processing completed');
                console.debug('Generated', fileListWithUrls.length, 'ZIP entries');

                if (!fileListWithUrls || fileListWithUrls.length === 0) {
                    throw new Error('File list processing resulted in empty array');
                }

                // Calculate total size using the file list with URLs
                allUrls = fileListWithUrls.map(f => f.url);
                console.debug('All URLs for size calculation:', allUrls);

                totalSize = FileCache.getTotalSize(allUrls);
                console.debug('Calculated total size:', totalSize, 'bytes');

                console.info(`Total download size: ${Detail.humanFileSize(totalSize)}`);

            } catch (error) {
                console.error('Failed to process file list:', error);
                ProgressTracker.showError('Failed to prepare files for download: ' + error.message);
                $(window).off('beforeunload', beforeUnloadHandler);
                downloadInProgress = false;
                $('button.dl-btns').removeClass('disabled');
                if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');
                return;
            }

            // Create abort controller for cancellation
            currentAbortController = new AbortController();
            const abortSignal = currentAbortController.signal;

            // Setup cancel button
            $('#btn-cancel-dl').off('click').on('click', () => {
                try {
                    cancel();
                } catch (error) {
                    console.warn('Cancel button error:', error);
                    ProgressTracker.showWarning('Download canceled by user');
                }
            });

            // Warn user before leaving page
            const beforeUnloadHandler = (e) => {
                e.preventDefault();
                return 'The download has not finished, are you sure you want to leave the page?';
            };
            $(window).on('beforeunload', beforeUnloadHandler);

            try {
                // Use ZIP download with File System Access API
                console.debug('Using ZIP download with File System Access API');

                // Create ZIP stream using the original file list
                // Note: createZipStream will handle the processing internally
                const zipStream = ZipBuilder.createZipStream(fileList, abortSignal);

                // Create stream writer - this will throw if FSA is not supported
                const writer = await StreamWriter.create(zipTitle, totalSize);

                // Validate writer object
                if (!writer) {
                    console.error('StreamWriter.create() returned null/undefined');
                    throw new Error('Failed to create download writer. No supported download method available.');
                }

                if (typeof writer.write !== 'function') {
                    console.error('Invalid writer object - missing write method:', {
                        writerType: writer.constructor ? writer.constructor.name : 'unknown',
                        writerKeys: Object.keys(writer),
                        writer: writer
                    });
                    throw new Error('Failed to create download writer. Writer object is invalid.');
                }

                console.debug('Using writer:', writer.constructor ? writer.constructor.name : 'unknown');

                // Track progress
                let bytesDownloaded = 0;
                const progressCallback = (chunkSize) => {
                    bytesDownloaded += chunkSize;
                    ProgressTracker.updateProgress(bytesDownloaded, totalSize);
                };

                // Write ZIP to disk with progress tracking
                await writer.write(zipStream, progressCallback, abortSignal);

            } catch (error) {
                if (error.name !== 'AbortError') {
                  console.error('Download failed:', error);
                }

                // Check if it was user cancellation
                const isUserCancelled = wasUserCancelled || error.name === 'AbortError' ||
                                       (error.message && error.message.includes('aborted')) ||
                                       (currentAbortController && currentAbortController.signal.aborted);

                if (isUserCancelled) {
                    // User cancellation - message already shown in cancel() function
                    console.warn('Download was canceled by user');
                    wasUserCancelled = false; // Reset flag
                } else if (error.message.includes('File System Access API is not supported')) {
                    // Handle the case where File System Access API is not supported
                    ProgressTracker.showError('File System Access API is not supported in your browser. Please use Chrome, Edge, or other modern browsers for ZIP downloads.');
                } else {
                    // Real error
                    ProgressTracker.showError('Failed to download files: ' + error.message);
                }

                // Clean up
                $(window).off('beforeunload', beforeUnloadHandler);
                downloadInProgress = false;
                $('button.dl-btns').removeClass('disabled');
                if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');

                // Hide progress bar and cancel button on error, but preserve messages
                ProgressTracker.hideProgressBar();
                ProgressTracker.hideCancelButton();
                return;
            }

            // Success!
            console.info('Download completed successfully');
            console.info('Calling ProgressTracker.finish for ZIP download');
            ProgressTracker.finish();

            console.info('Download process fully completed');

            // Cleanup
            $(window).off('beforeunload', beforeUnloadHandler);
            downloadInProgress = false;
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');

        } catch (error) {
            console.error('Download failed:', error);

            // Check if it was user cancellation
            const isUserCancelled = wasUserCancelled || error.name === 'AbortError' ||
                                   (error.message && error.message.includes('aborted')) ||
                                   (currentAbortController && currentAbortController.signal.aborted);

            if (isUserCancelled) {
                // User cancellation - message already shown in cancel() function
                console.info('Download was canceled by user');
                wasUserCancelled = false; // Reset flag
                // Don't show any additional error messages
            } else {
                // Real error
                ProgressTracker.error();
                ProgressTracker.showError('There was an error during the download: ' + error.message);
            }

            // Cleanup
            $(window).off('beforeunload');
            downloadInProgress = false;
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');

            // Hide progress bar and cancel button on error, but preserve messages
            ProgressTracker.hideProgressBar();
            ProgressTracker.hideCancelButton();
        }
    }

    /**
     * Cancel ongoing download
     */
    function cancel() {
        if (currentAbortController) {
            try {
                wasUserCancelled = true; // Set flag before aborting
                currentAbortController.abort();
                // Show user-friendly cancellation message
                ProgressTracker.showWarning('Download canceled by user (any already completed downloads were saved)');
            } catch (error) {
                console.warn('Error during cancellation:', error);
                ProgressTracker.showWarning('Download canceled by user');
            }
            currentAbortController = null;
        }
        downloadInProgress = false;

        // Clean up UI state
        $(window).off('beforeunload');
        $('button.dl-btns').removeClass('disabled');
        if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');

        // Hide progress bar and cancel button, but preserve messages
        ProgressTracker.hideProgressBar();
        ProgressTracker.hideCancelButton();
    }

    /**
     * Check if download is in progress
     * @returns {boolean}
     */
    function isDownloading() {
        return downloadInProgress;
    }


    // ============================================================================
    // Record Export/Download (triggered by #btn-xml-dl and #btn-json-dl )
    // ============================================================================

    async function prepDownloadXML() {
        if (window.location.href.includes('/pid/')) {
            try {
                let response = await fetch(window.location.href, { headers: { 'Accept': 'application/json' } });
                let res = await response.json();
                return res.id;
            } catch (err) {
                alert(`There was an error trying to download the record XML: ${err}`);
                console.error(err);
            }
        } else {
            let id = new URLSearchParams(window.location.search).get('id');
            return Promise.resolve(id);
        }
    };

    /**
     * Downloads a record in the specified format.
     * @param {string} format - The format to download, must be either "XML" or "JSON".
     */
    function downloadRecord(format) {
        if (format !== "XML" && format !== "JSON") {
            throw new Error("Invalid format. Must be either 'XML' or 'JSON'.");
        }
        let id = prepDownloadXML();
        id.then(i => {
            let url = `/exporter/rest/export?data_id=${i}&exporter=${format}`;

            // Just click on a link to the exported URL, which CDCS gives the correct filename
            const a = document.createElement('a');
            a.href = url;
            a.download = ''; // Empty download attribute lets browser use server's filename
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
    };

    // Public API (extend existing namespace)
    Object.assign(window.NexusLIMSDetail.Downloads, {
        initialize,
        updateDownloadSize,
        download,
        cancel,
        isDownloading,
        downloadRecord
    });

})(jQuery, window);
