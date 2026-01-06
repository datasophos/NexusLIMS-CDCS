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

    /**
     * Initialize file size cache for the page
     * @param {string[]} dataUrls - Array of data file URLs
     * @param {string[]} jsonUrls - Array of JSON metadata URLs
     * @returns {Promise<void>}
     */
    async function initialize(dataUrls, jsonUrls) {
        try {
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
        if (!Detail.supportsClientSideZip) {
            alert('Due to browser limitations, downloading of files into a zip archive is not supported in your current browser. Please use a modern browser instead.');
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');
            return;
        }

        if (!StreamWriter.supportsFileSystemAccess() && !StreamWriter.supportsStreamSaver()) {
            alert('Your browser does not support streaming downloads. Please use a modern browser (Chrome, Edge, Firefox, or Safari).');
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');
            return;
        }

        if (downloadInProgress) {
            console.warn('Download already in progress');
            return;
        }

        try {
            downloadInProgress = true;

            // Reset UI
            ProgressTracker.reset();
            ProgressTracker.updatePercent(0);
            ProgressTracker.showCancelButton();

            // Prepare file list with EMI files
            const fileList = EmiBundler.prepareFileList(dataUrls, jsonUrls, paths);

            console.info(`Downloading ${fileList.length} datasets`);

            // Calculate total size
            // Note: buildZipFileArray deduplicates at URL level, keeping:
            // - Each data file once (even if multiple datasets reference it)
            // - Each unique JSON file (even if they share the same data file)
            // - Each EMI file once
            const allZipFiles = ZipBuilder.buildZipFileArray(fileList);
            const allUrls = allZipFiles.map(f => f.url);
            const totalSize = FileCache.getTotalSize(allUrls);

            console.info(`Total download size: ${Detail.humanFileSize(totalSize)}`);

            // Create abort controller for cancellation
            currentAbortController = new AbortController();
            const abortSignal = currentAbortController.signal;

            // Setup cancel button
            $('#btn-cancel-dl').off('click').on('click', () => {
                cancel();
            });

            // Warn user before leaving page
            const beforeUnloadHandler = (e) => {
                e.preventDefault();
                return 'The download has not finished, are you sure you want to leave the page?';
            };
            $(window).on('beforeunload', beforeUnloadHandler);

            // Create ZIP stream
            const zipStream = ZipBuilder.createZipStream(fileList, abortSignal);

            // Create stream writer
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
            
            console.info('Using writer:', writer.constructor ? writer.constructor.name : 'unknown');

            // Track progress
            let bytesDownloaded = 0;
            const progressCallback = (chunkSize) => {
                bytesDownloaded += chunkSize;
                ProgressTracker.updateProgress(bytesDownloaded, totalSize);
            };

            // Write ZIP to disk with progress tracking
            await writer.write(zipStream, progressCallback, abortSignal);

            // Success!
            ProgressTracker.finish();

            // Cleanup
            $(window).off('beforeunload', beforeUnloadHandler);
            downloadInProgress = false;
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');

        } catch (error) {
            console.error('Download failed:', error);

            // Check if it was user cancellation
            if (error.name === 'AbortError' || currentAbortController?.signal.aborted) {
                ProgressTracker.showWarning('Download canceled by user (any already completed downloads were saved)');
            } else {
                ProgressTracker.error();
                ProgressTracker.showError('There was an error during the download: ' + error.message);
            }

            // Cleanup
            $(window).off('beforeunload');
            downloadInProgress = false;
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi+shift');
        }
    }

    /**
     * Cancel ongoing download
     */
    function cancel() {
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }
        downloadInProgress = false;
    }

    /**
     * Check if download is in progress
     * @returns {boolean}
     */
    function isDownloading() {
        return downloadInProgress;
    }

    // Public API (extend existing namespace)
    Object.assign(window.NexusLIMSDetail.Downloads, {
        initialize,
        updateDownloadSize,
        download,
        cancel,
        isDownloading
    });

})(jQuery, window);
