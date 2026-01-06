/**
 * NexusLIMS Detail Page - Stream Writer Module
 *
 * Abstracts download mechanism with progressive enhancement:
 * File System Access API (Chrome/Edge) → StreamSaver (Firefox/Safari)
 */

(function(window) {
    'use strict';

    // Log script loading
    console.info('Loading NexusLIMS StreamWriter module...');

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
     * native backpressure doesn't work properly (e.g., Firefox + StreamSaver).
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

        // Throttling settings - default to 30 MB/s for StreamSaver to prevent memory buildup
        // This is conservative but safe; can be increased if testing shows stability
        const targetSpeedMBps = options.targetSpeedMBps ?? 30;
        const targetBytesPerMs = targetSpeedMBps * 1024 * 1024 / 1000;

        // Diagnostic counters
        let totalBytesWritten = 0;
        let chunkCount = 0;
        let throttleWaitCount = 0;
        let totalThrottleWaitMs = 0;
        const startTime = performance.now();

        console.info(`Stream throttling: ${targetSpeedMBps > 0 ? targetSpeedMBps + ' MB/s' : 'disabled'}`);

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

                // Manual throttling: Calculate how far ahead we are vs target speed
                // This prevents memory buildup when native backpressure doesn't work
                if (targetSpeedMBps > 0) {
                    const elapsed = performance.now() - startTime;
                    const expectedBytes = elapsed * targetBytesPerMs;
                    const aheadBy = totalBytesWritten - expectedBytes;

                    if (aheadBy > 0) {
                        // We're ahead of schedule - wait to let disk catch up
                        const waitMs = aheadBy / targetBytesPerMs;
                        if (waitMs > 10) {  // Only wait if significant
                            throttleWaitCount++;
                            totalThrottleWaitMs += waitMs;
                            await new Promise(resolve => setTimeout(resolve, waitMs));
                        }
                    }
                }

                // Periodic logging every 100MB
                if (totalBytesWritten % (100 * 1024 * 1024) < chunkSize) {
                    const elapsed = (performance.now() - startTime) / 1000;
                    const speed = (totalBytesWritten / 1024 / 1024 / elapsed).toFixed(1);
                    console.info(`Stream progress: ${(totalBytesWritten / 1024 / 1024 / 1024).toFixed(2)} GiB, ${chunkCount} chunks, ${speed} MB/s actual, throttle waits: ${throttleWaitCount}`);
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
            console.error(`Stream error after ${(totalBytesWritten / 1024 / 1024 / 1024).toFixed(2)} GiB in ${elapsed.toFixed(1)}s, ${chunkCount} chunks`);
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
     * Check if StreamSaver is available
     * @returns {boolean}
     */
    function supportsStreamSaver() {
        return typeof streamSaver !== 'undefined';
    }

    /**
     * Check if browser supports transferable streams (important for backpressure)
     * This affects whether StreamSaver can properly handle backpressure
     * @returns {boolean}
     */
    function supportsTransferableStreams() {
        try {
            const { readable } = new TransformStream();
            const mc = new MessageChannel();
            mc.port1.postMessage(readable, [readable]);
            mc.port1.close();
            mc.port2.close();
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Check if we're running in Firefox
     * @returns {boolean}
     */
    function isFirefox() {
        return navigator.userAgent.toLowerCase().includes('firefox');
    }

    /**
     * Check if we're running in Safari
     * @returns {boolean}
     */
    function isSafari() {
        const ua = navigator.userAgent.toLowerCase();
        return ua.includes('safari') && !ua.includes('chrome') && !ua.includes('chromium');
    }

    /**
     * Get the maximum safe download size for StreamSaver
     * Firefox has issues with large files due to Service Worker buffering
     * @returns {number} Max size in bytes (0 = no limit)
     */
    function getMaxStreamSaverSize() {
        if (isFirefox()) {
            // Firefox StreamSaver fails around 800MB-1GB due to Service Worker buffering
            return 700 * 1024 * 1024;  // 700 MB to be safe
        }
        return 0;  // No limit for other browsers
    }

    /**
     * Custom Service Worker Writer with pull-based backpressure
     * This is more reliable than StreamSaver for large files in Firefox
     */
    class ServiceWorkerWriter {
        constructor(filename, size) {
            this.filename = filename;
            this.size = size;
            this.downloadId = Math.random().toString(36).slice(2);
            this.port = null;
            this.reader = null;
            this.aborted = false;
            this.chunkResolve = null;
        }

        static swRegistration = null;
        static swReady = null;

        static async ensureServiceWorker() {
            if (ServiceWorkerWriter.swReady) {
                return ServiceWorkerWriter.swReady;
            }

            ServiceWorkerWriter.swReady = (async () => {
                if (!('serviceWorker' in navigator)) {
                    throw new Error('Service Workers not supported');
                }

                // Register our custom service worker
                // The scope must be within or below the SW script's directory
                const swUrl = '/static/nexuslims/js/detail/downloads/download-sw.js';
                const swScope = '/static/nexuslims/js/detail/downloads/';

                try {
                    console.info('Registering service worker:', swUrl, 'scope:', swScope);

                    // Check if service worker is already registered and active
                    const existingRegistration = await navigator.serviceWorker.getRegistration(swScope);
                    if (existingRegistration && existingRegistration.active) {
                        console.info('Using existing SW registration');
                        ServiceWorkerWriter.swRegistration = existingRegistration;
                        return existingRegistration;
                    }

                    ServiceWorkerWriter.swRegistration = await navigator.serviceWorker.register(swUrl, {
                        scope: swScope
                    });

                    console.info('SW registered, state:', ServiceWorkerWriter.swRegistration.active?.state,
                                 'installing:', !!ServiceWorkerWriter.swRegistration.installing,
                                 'waiting:', !!ServiceWorkerWriter.swRegistration.waiting);

                    // Wait for the service worker to be active
                    const waitForActive = () => new Promise((resolve) => {
                        const sw = ServiceWorkerWriter.swRegistration.installing ||
                                   ServiceWorkerWriter.swRegistration.waiting ||
                                   ServiceWorkerWriter.swRegistration.active;

                        if (sw?.state === 'activated' || sw?.state === 'active') {
                            console.info('SW already active');
                            resolve();
                            return;
                        }

                        if (!sw) {
                            console.info('No SW found, resolving anyway');
                            resolve();
                            return;
                        }

                        console.info('Waiting for SW to activate, current state:', sw.state);
                        sw.addEventListener('statechange', function handler(e) {
                            console.info('SW state changed:', e.target.state);
                            if (e.target.state === 'activated') {
                                sw.removeEventListener('statechange', handler);
                                resolve();
                            }
                        });
                    });

                    await waitForActive();
                    console.info('SW is now active');

                    // Get the active worker
                    const activeSW = ServiceWorkerWriter.swRegistration.active;
                    if (!activeSW) {
                        throw new Error('Service worker not active after waiting');
                    }

                    console.info('Service worker ready');
                    return ServiceWorkerWriter.swRegistration;
                } catch (error) {
                    console.error('Failed to register download service worker:', error);
                    throw error;
                }
            })();

            return ServiceWorkerWriter.swReady;
        }

        async write(readableStream, progressCallback, abortSignal) {
            try {
                // Ensure service worker is registered
                await ServiceWorkerWriter.ensureServiceWorker();

                // Setup MessageChannel for communication
                const channel = new MessageChannel();
                this.port = channel.port1;

                // Get the active service worker from our registration
                const registration = await ServiceWorkerWriter.ensureServiceWorker();
                const sw = registration.active;

                console.info('Using SW:', sw ? 'found' : 'not found', 'controller:', !!navigator.serviceWorker.controller);

                if (!sw) {
                    throw new Error('No active service worker - try refreshing the page');
                }

                // Safari-specific: Ensure the service worker is controlling the current page
                if (isSafari() && !navigator.serviceWorker.controller) {
                    console.info('Safari detected - waiting for SW to control current page');
                    await new Promise(resolve => {
                        const checkController = setInterval(() => {
                            if (navigator.serviceWorker.controller) {
                                clearInterval(checkController);
                                resolve();
                            }
                        }, 100);
                        // Timeout after 5 seconds
                        setTimeout(() => {
                            clearInterval(checkController);
                            console.warn('Safari: Timeout waiting for SW control');
                            resolve();
                        }, 5000);
                    });
                }

                // Initialize download in service worker
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject(new Error('Service worker init timeout')), 5000);

                    this.port.onmessage = (event) => {
                        if (event.data.type === 'READY') {
                            clearTimeout(timeout);
                            resolve();
                        }
                    };

                    sw.postMessage({
                        type: 'INIT_DOWNLOAD',
                        downloadId: this.downloadId,
                        filename: this.filename,
                        size: this.size
                    }, [channel.port2]);
                });

                console.info(`Download initialized: ${this.downloadId}`);

                // Setup chunk request handler (pull-based backpressure)
                this.reader = readableStream.getReader();
                let totalBytes = 0;
                let chunkCount = 0;
                const startTime = performance.now();

                this.port.onmessage = async (event) => {
                    const { type, reason } = event.data;

                    console.info('Main thread received from SW:', type);

                    if (type === 'NEED_CHUNK') {
                        // Service worker is ready for next chunk - this is the backpressure!
                        console.info('SW requesting chunk, reading from stream...');

                        if (this.aborted) {
                            this.port.postMessage({ type: 'ABORT', downloadId: this.downloadId });
                            return;
                        }

                        try {
                            const { done, value } = await this.reader.read();
                            console.info('Read from stream:', done ? 'done' : `${value?.byteLength} bytes`);

                            if (done) {
                                console.info('Stream complete, sending DONE');
                                this.port.postMessage({ type: 'DONE', downloadId: this.downloadId });
                                if (this.chunkResolve) this.chunkResolve();
                            } else {
                                chunkCount++;
                                totalBytes += value.byteLength;

                                if (progressCallback) {
                                    progressCallback(value.byteLength);
                                }

                                console.info(`Sending chunk ${chunkCount}: ${value.byteLength} bytes`);
                                this.port.postMessage({
                                    type: 'CHUNK',
                                    downloadId: this.downloadId,
                                    chunk: value
                                });

                                // Log progress every 100MB
                                if (totalBytes % (100 * 1024 * 1024) < value.byteLength) {
                                    const elapsed = (performance.now() - startTime) / 1000;
                                    const speed = (totalBytes / 1024 / 1024 / elapsed).toFixed(1);
                                    console.info(`SW Download: ${(totalBytes / 1024 / 1024 / 1024).toFixed(2)} GiB, ${chunkCount} chunks, ${speed} MB/s`);
                                }
                            }
                        } catch (error) {
                            console.error('Error reading chunk:', error);
                            this.port.postMessage({ type: 'ABORT', downloadId: this.downloadId });
                            if (this.chunkResolve) this.chunkResolve(error);
                        }
                    } else if (type === 'CANCELED') {
                        console.info('Download canceled by service worker:', reason);
                        this.aborted = true;
                        if (this.chunkResolve) this.chunkResolve(new Error('Download canceled'));
                    }
                };

                // Trigger the download using an iframe that's controlled by our service worker
                const downloadUrl = `/static/nexuslims/js/detail/downloads/dl/${this.downloadId}/${encodeURIComponent(this.filename)}`;
                const frameUrl = '/static/nexuslims/js/detail/downloads/download-frame.html';

                // Create iframe that loads our helper page (which IS in the SW scope)
                const iframe = document.createElement('iframe');
                iframe.hidden = true;
                iframe.src = frameUrl;
                document.body.appendChild(iframe);

                // Wait for frame to be ready (including SW control), then trigger download
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject(new Error('Download frame timeout')), 15000);

                    const messageHandler = (event) => {
                        if (event.source !== iframe.contentWindow) return;

                        if (event.data.type === 'FRAME_READY') {
                            clearTimeout(timeout);
                            window.removeEventListener('message', messageHandler);

                            console.info('Download frame ready, SW controlled:', event.data.controlled);

                            if (!event.data.controlled) {
                                console.warn('Frame is not controlled by SW - fetch may not be intercepted');
                            }

                            // Tell the frame to navigate to the download URL
                            iframe.contentWindow.postMessage({
                                type: 'TRIGGER_DOWNLOAD',
                                downloadUrl: downloadUrl
                            }, '*');

                            resolve();
                        }
                    };

                    window.addEventListener('message', messageHandler);
                });

                console.info('Download triggered via iframe');

                // Wait for download to complete
                await new Promise((resolve, reject) => {
                    this.chunkResolve = (error) => {
                        if (error) reject(error);
                        else resolve();
                    };

                    if (abortSignal) {
                        abortSignal.addEventListener('abort', () => {
                            this.aborted = true;
                            this.port.postMessage({ type: 'ABORT', downloadId: this.downloadId });
                            reject(new DOMException('Aborted', 'AbortError'));
                        });
                    }
                });

                // Cleanup
                setTimeout(() => iframe.remove(), 1000);

                const elapsed = (performance.now() - startTime) / 1000;
                console.info(`Download complete: ${(totalBytes / 1024 / 1024 / 1024).toFixed(2)} GiB in ${elapsed.toFixed(1)}s`);

            } catch (error) {
                if (error.name === 'AbortError') {
                    console.info('Download canceled by user');
                    throw error;
                } else {
                    console.error('ServiceWorkerWriter error:', error);
                    throw new Error('Failed to save file: ' + error.message);
                }
            }
        }
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
                    console.info('Download canceled by user');
                    throw error;
                } else {
                    console.error('File System Access API error:', error);
                    throw new Error('Failed to save file: ' + error.message);
                }
            }
        }
    }

    /**
     * StreamSaver Writer (fallback)
     *
     * Note: StreamSaver has backpressure issues without transferable streams.
     * We mitigate this by:
     * 1. Using a small highWaterMark to limit internal buffering
     * 2. Checking writer.ready in pipeWithProgress before each write
     */
    class StreamSaverWriter {
        constructor(filename, size) {
            this.filename = filename;
            this.size = size;
            this.fileStream = null;
        }

        async write(readableStream, progressCallback, abortSignal) {
            try {
                // Use extremely small queue sizes to minimize internal buffering
                // This forces more frequent backpressure signals
                // CountQueuingStrategy with highWaterMark=1 means only 1 chunk can be queued
                this.fileStream = streamSaver.createWriteStream(this.filename, {
                    size: this.size,
                    writableStrategy: new CountQueuingStrategy({ highWaterMark: 1 }),
                    readableStrategy: new CountQueuingStrategy({ highWaterMark: 1 })
                });

                console.info('StreamSaver stream created with minimal buffering (highWaterMark=1)');

                // For Safari, apply conservative throttling for large files
                const throttlingOptions = isSafari() && this.size > 500 * 1024 * 1024 ? { 
                    targetSpeedMBps: 10  // Conservative 10 MB/s for large files in Safari
                } : { 
                    targetSpeedMBps: 0  // No throttling for other cases
                };

                if (isSafari() && this.size > 500 * 1024 * 1024) {
                    console.warn('Safari: File too large for StreamSaver, applying additional throttling');
                }

                // Use manual piping
                await pipeWithProgress(readableStream, this.fileStream, progressCallback, abortSignal, throttlingOptions);

            } catch (error) {
                if (error.name === 'AbortError') {
                    console.info('Download canceled by user');
                    throw error;
                } else {
                    console.error('StreamSaver error:', error);
                    throw new Error('Failed to save file: ' + error.message);
                }
            }
        }
    }



    /**
     * Create a stream writer using the best available method
     * @param {string} filename - Name of file to save
     * @param {number} size - Expected file size (used by StreamSaver)
     * @returns {FileSystemAccessWriter|ServiceWorkerWriter|StreamSaverWriter}
     * @throws {Error} If no supported download method is available
     */
    async function create(filename, size) {
        try {
            console.info('StreamWriter.create() called with:', { filename, size });
            console.info('Browser detection:', {
                supportsFileSystemAccess: supportsFileSystemAccess(),
                isFirefox: isFirefox(),
                isSafari: isSafari(),
                supportsStreamSaver: supportsStreamSaver(),
                hasServiceWorker: 'serviceWorker' in navigator
            });
            
            if (supportsFileSystemAccess()) {
                console.info('Using File System Access API for download');
                return new FileSystemAccessWriter(filename);
            } else if (isFirefox() && 'serviceWorker' in navigator) {
                // Use our custom service worker for Firefox (better backpressure than StreamSaver)
                console.info('Using custom Service Worker for download (Firefox)');
                return new ServiceWorkerWriter(filename, size);
            } else if (isSafari()) {
                // Safari: Use StreamSaver if available
                console.warn('Safari detected - using StreamSaver for download');
                
                if (supportsStreamSaver()) {
                    console.info('Using StreamSaver for download (Safari)');
                    return new StreamSaverWriter(filename, size);
                } else {
                    console.error('StreamSaver not available for Safari downloads');
                    throw new Error('StreamSaver not available for Safari downloads. Please ensure StreamSaver.js is loaded.');
                }
            } else if (supportsStreamSaver()) {
                console.info('Using StreamSaver for download');
                return new StreamSaverWriter(filename, size);
            } else {
                console.error('No supported download method available');
                throw new Error(
                    'Browser does not support streaming downloads. ' +
                    'Please use a modern browser (Chrome, Edge, Firefox, or Safari).'
                );
            }
        } catch (error) {
            console.error('StreamWriter.create() failed:', error);
            throw error; // Re-throw to ensure the error is propagated
        }
    }

    /**
     * Get the download method being used
     * @returns {string} 'fsa' | 'streamsaver' | 'none'
     */
    function getDownloadMethod() {
        if (supportsFileSystemAccess()) {
            return 'fsa';
        } else if (supportsStreamSaver()) {
            return 'streamsaver';
        } else {
            return 'none';
        }
    }



    // Public API
    window.NexusLIMSDetail.Downloads.StreamWriter = {
        create,
        supportsFileSystemAccess,
        supportsStreamSaver,
        supportsTransferableStreams,
        getDownloadMethod,
        isFirefox,
        isSafari,
        getMaxStreamSaverSize
    };

    // Log initialization
    console.info('NexusLIMSDetail.Downloads.StreamWriter initialized with methods:', Object.keys(window.NexusLIMSDetail.Downloads.StreamWriter));

    // Add defensive access
    if (typeof window.NexusLIMSDetail === 'undefined') {
        window.NexusLIMSDetail = {};
    }
    if (typeof window.NexusLIMSDetail.Downloads === 'undefined') {
        window.NexusLIMSDetail.Downloads = {};
    }

    // Ensure the StreamWriter is accessible via simpler path for compatibility
    window.StreamWriter = window.NexusLIMSDetail.Downloads.StreamWriter;

})(window);
