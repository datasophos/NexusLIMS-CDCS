/**
 * NexusLIMS Detail Page - Stream Writer Module
 *
 * Provides File System Access API download functionality only.
 * Falls back to error with clear warning if FSA is not supported.
 */

(function(window) {
    'use strict';

    // Create namespace with defensive checks
    if (typeof window.NexusLIMSDetail === 'undefined') {
        console.warn('NexusLIMSDetail not defined, creating...');
        window.NexusLIMSDetail = {};
    }
    if (typeof window.NexusLIMSDetail.Downloads === 'undefined') {
        console.warn('NexusLIMSDetail.Downloads not defined, creating...');
        window.NexusLIMSDetail.Downloads = {};
    }

    /**
     * Pipe a readable stream to a writable stream with progress tracking,
     * backpressure handling, and manual throttling for browsers where
     * native backpressure doesn't work properly.
     *
     * @param {ReadableStream} readable - Source stream
     * @param {WritableStream} writable - Destination stream
     * @param {Function} progressCallback - Progress callback
     * @param {AbortSignal} abortSignal - Cancellation signal
     * @param {Object} options - Throttling options
     * @param {number} options.targetSpeedMBps - Target speed in MB/s (0 = no throttling)
     */
    async function pipeWithProgress(readable, writable, progressCallback, abortSignal, options = {}) {
        const reader = readable.getReader();
        const writer = writable.getWriter();


        // Diagnostic counters
        let totalBytesWritten = 0;
        let chunkCount = 0;
        let throttleWaitCount = 0;
        let totalThrottleWaitMs = 0;
        const startTime = performance.now();

        try {
            while (true) {
                // Check for abort before reading
                if (abortSignal && abortSignal.aborted) {
                    throw new DOMException('Aborted', 'AbortError');
                }

                // Wait for writer to be ready (native backpressure)
                await writer.ready;

                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                chunkCount++;
                const chunkSize = value ? value.byteLength : 0;

                // Track progress
                if (progressCallback && value) {
                    progressCallback(chunkSize);
                }

                // Write chunk
                await writer.write(value);
                totalBytesWritten += chunkSize;


                // Periodic logging every 100MB
                if (totalBytesWritten % (100 * 1024 * 1024) < chunkSize) {
                    const elapsed = (performance.now() - startTime) / 1000;
                    const speed = (totalBytesWritten / 1024 / 1024 / elapsed).toFixed(1);
                    console.debug(`Stream progress: ${(totalBytesWritten / 1024 / 1024 / 1024).toFixed(2)} GiB, ${chunkCount} chunks, ${speed} MB/s actual, throttle waits: ${throttleWaitCount}`);
                }
            }

            // Close the writer to finalize the file
            await writer.ready;
            await writer.close();

            // Final stats
            const elapsed = (performance.now() - startTime) / 1000;
            const avgSpeed = (totalBytesWritten / 1024 / 1024 / elapsed).toFixed(1);
            console.info(`Stream complete: ${(totalBytesWritten / 1024 / 1024 / 1024).toFixed(2)} GiB in ${elapsed.toFixed(1)}s (${avgSpeed} MB/s), ${chunkCount} chunks, throttle waits: ${throttleWaitCount} (${(totalThrottleWaitMs/1000).toFixed(1)}s total)`);

        } catch (error) {
            const elapsed = (performance.now() - startTime) / 1000;
            if (error.name !== 'AbortError') {
              console.error(`Stream error after ${(totalBytesWritten / 1024 / 1024 / 1024).toFixed(2)} GiB in ${elapsed.toFixed(1)}s, ${chunkCount} chunks`);
            }
            // Clean up on error
            try {
                reader.releaseLock();
            } catch (e) {
                // Ignore release errors
            }
            try {
                await writer.abort(error);
            } catch (e) {
                // Ignore abort errors
            }
            throw error;
        }

        // Release locks on success
        reader.releaseLock();
        writer.releaseLock();
    }

    /**
     * Check if File System Access API is supported
     * @returns {boolean}
     */
    function supportsFileSystemAccess() {
        return 'showSaveFilePicker' in window && window.isSecureContext;
    }

    /**
     * File System Access API Writer
     */
    class FileSystemAccessWriter {
        constructor(filename) {
            this.filename = filename;
            this.handle = null;
        }

        async write(readableStream, progressCallback, abortSignal) {
            try {
                // Show native save dialog
                this.handle = await window.showSaveFilePicker({
                    suggestedName: this.filename,
                    types: [{
                        description: 'ZIP Archive',
                        accept: { 'application/zip': ['.zip'] }
                    }]
                });

                const writable = await this.handle.createWritable();

                // Use manual piping - File System Access API has proper backpressure, so no throttling needed
                await pipeWithProgress(readableStream, writable, progressCallback, abortSignal, {
                    targetSpeedMBps: 0  // Disable throttling for FSA - native backpressure works
                });

            } catch (error) {
                if (error.name === 'AbortError') {
                    // console.warn('Download canceled by user');
                    throw error;
                } else {
                    console.error('File System Access API error:', error);
                    throw new Error('Failed to save file: ' + error.message);
                }
            }
        }
    }

    /**
     * Create a stream writer using File System Access API
     * @param {string} filename - Name of file to save
     * @param {number} size - Expected file size (used by StreamSaver)
     * @returns {FileSystemAccessWriter}
     * @throws {Error} If File System Access API is not supported
     */
    async function create(filename, size) {
        try {
            console.debug('StreamWriter.create(): Called with:', { filename, size });
            console.debug('StreamWriter.create(): Browser detection:', {
                supportsFileSystemAccess: supportsFileSystemAccess()
            });

            if (supportsFileSystemAccess()) {
                console.debug('Using File System Access API for download');
                return new FileSystemAccessWriter(filename);
            } else {
                // File System Access API is not supported - show clear warning
                const errorMessage = 'File System Access API is not supported in this browser. ' +
                    'Please use Chrome, Edge, or other modern browsers that support this feature.';
                console.warn('WARNING: ' + errorMessage);
                console.warn('Browser does not support File System Access API');
                console.warn('This feature requires Chrome, Edge, or other modern browsers.');

                throw new Error(errorMessage);
            }
        } catch (error) {
            console.error('StreamWriter.create() failed:', error);
            console.error('Stack trace:', error.stack);
            throw error; // Re-throw to ensure the error is propagated
        }
    }

    /**
     * Get the download method being used
     * @returns {string} 'fsa' | 'individual' | 'none'
     */
    function getDownloadMethod() {
        if (supportsFileSystemAccess()) {
            return 'fsa';
        } else {
            return 'individual';
        }
    }



    // Public API
    window.NexusLIMSDetail.Downloads.StreamWriter = {
        create,
        supportsFileSystemAccess,
        getDownloadMethod
    };

    // Ensure the StreamWriter is accessible via simpler path for compatibility
    window.StreamWriter = window.NexusLIMSDetail.Downloads.StreamWriter;

})(window);
