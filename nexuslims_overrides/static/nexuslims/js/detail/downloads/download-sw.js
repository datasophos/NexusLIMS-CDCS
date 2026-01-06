/**
 * NexusLIMS Download Service Worker
 *
 * Handles streaming ZIP downloads with proper backpressure.
 * Unlike StreamSaver, this implements pull-based flow control where
 * the service worker requests chunks when ready, preventing memory buildup.
 */

// Use a path within our scope (same directory as this SW file)
const DOWNLOAD_URL_PREFIX = '/static/nexuslims/js/detail/downloads/dl/';
const activeDownloads = new Map();

// Browser detection for service worker - simplified synchronous version
function isSafari() {
    try {
        // Try to detect Safari based on common patterns
        // This is a heuristic approach since we can't access navigator.userAgent directly
        const userAgent = self.navigator?.userAgent || '';
        const ua = userAgent.toLowerCase();
        
        const isSafariBrowser = ua.includes('safari') && !ua.includes('chrome') && !ua.includes('chromium');
        console.log(`[DownloadSW] Browser detection - UserAgent: ${userAgent}`);
        console.log(`[DownloadSW] Browser detection - Is Safari: ${isSafariBrowser}`);
        
        return isSafariBrowser;
    } catch (e) {
        // If we can't determine, default to more conservative chunk size
        console.error(`[DownloadSW] Browser detection failed: ${e.message}, defaulting to Safari mode`);
        return true; // Be safe and use smaller chunks
    }
}

self.addEventListener('install', (event) => {
    console.log('[DownloadSW] Installing...');
    event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
    console.log('[DownloadSW] Activated, claiming clients...');
    event.waitUntil(self.clients.claim().then(() => {
        console.log('[DownloadSW] Clients claimed');
    }));
});

self.addEventListener('message', (event) => {
    const { type, downloadId, chunk, done, filename, size, clientId } = event.data;
    const port = event.ports[0];

    console.log('[DownloadSW] Message received:', type, downloadId || '');

    // Handle skip waiting
    if (type === 'SKIP_WAITING') {
        console.log('[DownloadSW] Skip waiting requested');
        self.skipWaiting();
        return;
    }

    switch (type) {
        case 'INIT_DOWNLOAD':
            // Initialize a new download session
            const download = {
                filename: filename,
                size: size,
                port: port,
                chunks: [],
                controller: null,
                resolveChunk: null,
                done: false
            };
            activeDownloads.set(downloadId, download);

            // Listen for messages on the port (CHUNK, DONE, ABORT)
            port.onmessage = (portEvent) => {
                const data = portEvent.data;
                console.log(`[DownloadSW] Port message received: ${data.type} for ${data.downloadId}`);

                if (data.type === 'CHUNK') {
                    const dl = activeDownloads.get(data.downloadId);
                    if (dl && dl.resolveChunk) {
                        console.log(`[DownloadSW] Resolving chunk: ${data.chunk.byteLength} bytes`);
                        dl.resolveChunk(data.chunk);
                        dl.resolveChunk = null;
                    } else if (dl) {
                        console.log(`[DownloadSW] Queuing chunk: ${data.chunk.byteLength} bytes`);
                        dl.chunks.push(data.chunk);
                    }
                } else if (data.type === 'DONE') {
                    const dl = activeDownloads.get(data.downloadId);
                    if (dl) {
                        console.log(`[DownloadSW] Download marked done: ${data.downloadId}`);
                        dl.done = true;
                        if (dl.resolveChunk) {
                            dl.resolveChunk(null);
                            dl.resolveChunk = null;
                        }
                    }
                } else if (data.type === 'ABORT') {
                    const dl = activeDownloads.get(data.downloadId);
                    if (dl && dl.controller) {
                        dl.controller.error(new Error('Download aborted'));
                    }
                    activeDownloads.delete(data.downloadId);
                    console.log(`[DownloadSW] Download aborted: ${data.downloadId}`);
                }
            };

            // Acknowledge initialization
            port.postMessage({ type: 'READY', downloadId });
            console.log(`[DownloadSW] Download initialized: ${downloadId} (${filename})`);
            break;

        case 'CHUNK':
            // Receive a chunk from main thread
            const dl = activeDownloads.get(downloadId);
            if (dl && dl.resolveChunk) {
                // Service worker is waiting for this chunk - deliver immediately
                dl.resolveChunk(chunk);
                dl.resolveChunk = null;
            } else if (dl) {
                // Queue chunk (shouldn't happen with proper flow control)
                dl.chunks.push(chunk);
            }
            break;

        case 'DONE':
            // Download complete
            const dlDone = activeDownloads.get(downloadId);
            if (dlDone) {
                dlDone.done = true;
                if (dlDone.resolveChunk) {
                    dlDone.resolveChunk(null);  // Signal end of stream
                    dlDone.resolveChunk = null;
                }
            }
            console.log(`[DownloadSW] Download complete signal: ${downloadId}`);
            break;

        case 'ABORT':
            // Download aborted
            const dlAbort = activeDownloads.get(downloadId);
            if (dlAbort && dlAbort.controller) {
                dlAbort.controller.error(new Error('Download aborted'));
            }
            activeDownloads.delete(downloadId);
            console.log(`[DownloadSW] Download aborted: ${downloadId}`);
            break;
    }
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    console.log('[DownloadSW] Fetch intercepted:', url.pathname);

    // Only intercept our download URLs
    if (!url.pathname.startsWith(DOWNLOAD_URL_PREFIX)) {
        console.log('[DownloadSW] Not our URL, passing through');
        return;
    }

    // Extract download ID from URL
    const downloadId = url.pathname.slice(DOWNLOAD_URL_PREFIX.length).split('/')[0];
    const download = activeDownloads.get(downloadId);

    if (!download) {
        console.error(`[DownloadSW] Unknown download: ${downloadId}`);
        event.respondWith(new Response('Download not found', { status: 404 }));
        return;
    }

    console.log(`[DownloadSW] Intercepting download: ${downloadId}`);

    try {
        // Create a ReadableStream that pulls chunks on demand
        console.log(`[DownloadSW] Creating stream for: ${downloadId}`);

        const stream = new ReadableStream({
            start(controller) {
                console.log(`[DownloadSW] Stream started: ${downloadId}`);
                download.controller = controller;
            },

            async pull(controller) {
                try {
                    console.log(`[DownloadSW] Pull called for: ${downloadId}, queued: ${download.chunks.length}, done: ${download.done}`);

                    // Check if we have queued chunks
                    if (download.chunks.length > 0) {
                        const chunk = download.chunks.shift();
                        console.log(`[DownloadSW] Enqueuing queued chunk: ${chunk.byteLength} bytes`);
                        controller.enqueue(chunk);
                        return;
                    }

                    // Check if download is done
                    if (download.done) {
                        controller.close();
                        activeDownloads.delete(downloadId);
                        console.log(`[DownloadSW] Stream closed: ${downloadId}`);
                        return;
                    }

                    // Request next chunk from main thread (PULL-based backpressure!)
                    console.log(`[DownloadSW] Requesting chunk from main thread: ${downloadId}`);
                    download.port.postMessage({ type: 'NEED_CHUNK', downloadId });

                    // Wait for chunk to arrive
                    const chunk = await new Promise((resolve) => {
                        download.resolveChunk = resolve;
                    });

                    if (chunk === null) {
                        // End of stream
                        controller.close();
                        activeDownloads.delete(downloadId);
                        console.log(`[DownloadSW] Stream closed (null chunk): ${downloadId}`);
                    } else {
                        // Check chunk size and split if too large
                        // Use much smaller chunks for Safari to prevent memory issues
                        const MAX_CHUNK_SIZE = isSafari() ? 5 * 1024 * 1024 : 50 * 1024 * 1024; // 5MB for Safari, 50MB for others
                        
                        if (chunk.byteLength > MAX_CHUNK_SIZE) {
                            console.warn(`[DownloadSW] Chunk too large (${chunk.byteLength} bytes), splitting into smaller chunks`);
                            console.info(`[DownloadSW] Using ${MAX_CHUNK_SIZE / 1024 / 1024}MB max chunk size`);
                            
                            // Split large chunk into smaller pieces
                            const chunkCount = Math.ceil(chunk.byteLength / MAX_CHUNK_SIZE);
                            console.log(`[DownloadSW] Splitting into ${chunkCount} chunks of ~${MAX_CHUNK_SIZE} bytes each`);
                            
                            // Process chunks one at a time with delays to prevent memory buildup
                            for (let i = 0; i < chunkCount; i++) {
                                const start = i * MAX_CHUNK_SIZE;
                                const end = Math.min(start + MAX_CHUNK_SIZE, chunk.byteLength);
                                const smallChunk = chunk.slice(start, end);
                                
                                console.log(`[DownloadSW] Enqueuing chunk part ${i+1}/${chunkCount}: ${smallChunk.byteLength} bytes`);
                                controller.enqueue(smallChunk);
                                
                                // For Safari, add a delay between chunks to allow memory cleanup
                                if (isSafari() && i < chunkCount - 1) {
                                    console.log(`[DownloadSW] Safari: Adding delay before next chunk to prevent memory issues`);
                                    await new Promise(resolve => setTimeout(resolve, 200)); // 200ms delay
                                }
                                
                                // Release reference to the chunk to help garbage collection
                                let tempSmallChunk = smallChunk;
                                tempSmallChunk = null;
                                
                                // Force garbage collection in Safari by yielding execution every 5 chunks
                                if (isSafari() && i > 0 && i % 5 === 0) {
                                    console.log(`[DownloadSW] Safari: Forcing garbage collection after ${i} chunks`);
                                    await new Promise(resolve => setTimeout(resolve, 0));
                                }
                            }
                        } else {
                            console.log(`[DownloadSW] Enqueuing chunk: ${chunk.byteLength} bytes`);
                            controller.enqueue(chunk);
                        }
                        
                        // Help with garbage collection - use a local variable we can control
                        let tempChunk = chunk;
                        tempChunk = null;
                    }
                } catch (error) {
                    console.error(`[DownloadSW] Error in pull handler: ${error.message}`, error);
                    controller.error(error);
                    activeDownloads.delete(downloadId);
                }
            },

            cancel(reason) {
                console.log(`[DownloadSW] Stream canceled: ${downloadId}`, reason);
                download.port.postMessage({ type: 'CANCELED', downloadId, reason: String(reason) });
                activeDownloads.delete(downloadId);
            }
        });

        // Respond with the stream
        const headers = new Headers({
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': `attachment; filename="${encodeURIComponent(download.filename)}"`,
        });

        if (download.size) {
            headers.set('Content-Length', String(download.size));
        }

        console.log(`[DownloadSW] Responding with stream: ${downloadId}`);
        event.respondWith(new Response(stream, { headers }));
        console.log(`[DownloadSW] Response sent: ${downloadId}`);

    } catch (error) {
        console.error(`[DownloadSW] Error creating response: ${downloadId}`, error);
        event.respondWith(new Response(`Error: ${error.message}`, { status: 500 }));
    }
});