/**
 * NexusLIMS Detail Page - ZIP Builder Module
 *
 * Creates ZIP archives using client-zip with streaming and Zip64 support
 */

(function(window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.Downloads = window.NexusLIMSDetail.Downloads || {};

    /**
     * Build ZIP file structure from file list
     * @param {Array} fileList - Array from EmiBundler.prepareFileList()
     * @returns {Array<{url: string, path: string}>} Flattened file array for ZIP
     */
    function buildZipFileArray(fileList) {
        const zipFiles = [];
        const seenUrls = new Set();

        fileList.forEach(file => {
            const { dataUrl, jsonUrl, emiUrl, path } = file;

            // Clean up path (remove leading slash)
            let cleanPath = path.charAt(0) === '/' ? path.substr(1) : path;

            // Get filenames
            const dataFilename = dataUrl.replace(/.*\//g, '');
            const jsonFilename = jsonUrl.replace(/.*\//g, '');

            // Build full paths
            let fullDataPath = cleanPath.length > 0 ? cleanPath + '/' + dataFilename : dataFilename;
            let fullJsonPath = cleanPath.length > 0 ? cleanPath + '/' + jsonFilename : jsonFilename;

            // Decode URI components
            fullDataPath = decodeURIComponent(fullDataPath).replace('//', '/');
            fullJsonPath = decodeURIComponent(fullJsonPath).replace('//', '/');

            // Add data file if not already seen (deduplication for multi-signal datasets)
            if (!seenUrls.has(dataUrl)) {
                zipFiles.push({ url: dataUrl, path: fullDataPath });
                seenUrls.add(dataUrl);
            }

            // Add JSON metadata if not already seen
            if (!seenUrls.has(jsonUrl)) {
                zipFiles.push({ url: jsonUrl, path: fullJsonPath });
                seenUrls.add(jsonUrl);
            }

            // Add EMI file if exists and not already seen
            if (emiUrl && !seenUrls.has(emiUrl)) {
                const emiFilename = emiUrl.replace(/.*\//g, '');
                let fullEmiPath = cleanPath.length > 0 ? cleanPath + '/' + emiFilename : emiFilename;
                fullEmiPath = decodeURIComponent(fullEmiPath).replace('//', '/');

                // Verify EMI file exists in cache
                const FileCache = window.NexusLIMSDetail.Downloads.FileCache;
                if (FileCache && !isNaN(FileCache.getSize(emiUrl))) {
                    zipFiles.push({ url: emiUrl, path: fullEmiPath });
                    seenUrls.add(emiUrl);
                    console.debug('Adding EMI file:', fullEmiPath);
                }
            }
        });

        return zipFiles;
    }

    /**
     * Create async generator for file iteration
     * @param {Array<{url: string, path: string}>} files - Files to include in ZIP
     * @param {AbortSignal} abortSignal - Signal for cancellation
     */
    async function* fileIterator(files, abortSignal) {
        let filesFetched = 0;

        for (const { url, path } of files) {
            filesFetched++;
            console.debug(`Fetching for ZIP (${filesFetched}/${files.length}): ${path}`);

            try {
                const response = await fetch(url, { signal: abortSignal });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                // Pass response.body directly to client-zip - no wrapping
                yield {
                    name: path,
                    lastModified: new Date(),
                    input: response.body
                };
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.info('File fetch aborted:', path);
                    throw error;
                } else {
                    console.error('Failed to fetch file:', path, error);
                    throw new Error(`Failed to fetch ${path}: ${error.message}`);
                }
            }
        }

        console.info(`All ${filesFetched} files yielded to ZIP stream`);
    }

    /**
     * Create ZIP stream from file list
     * @param {Array} fileList - File list from EmiBundler.prepareFileList()
     * @param {AbortSignal} abortSignal - Signal for cancellation
     * @returns {ReadableStream} ZIP archive stream
     */
    function createZipStream(fileList, abortSignal) {
        // Build flat array of files for ZIP
        const zipFiles = buildZipFileArray(fileList);

        console.info(`Creating ZIP with ${zipFiles.length} files`);

        // Use client-zip to create streaming ZIP
        // Note: downloadZip is exposed globally by client-zip-loader.js ES module
        if (typeof downloadZip === 'undefined') {
            throw new Error('client-zip library not loaded. Please ensure client-zip-loader.js is included as a module before this script.');
        }

        try {
            // downloadZip returns a Response object, we need to extract the stream
            const zipResponse = downloadZip(fileIterator(zipFiles, abortSignal));

            // Get the ReadableStream from the Response body
            if (!zipResponse || !zipResponse.body) {
                throw new Error('downloadZip did not return a valid Response with a body stream');
            }

            return zipResponse.body;
        } catch (error) {
            console.error('Error creating ZIP stream:', error);
            throw error;
        }
    }

    // Public API
    window.NexusLIMSDetail.Downloads.ZipBuilder = {
        createZipStream,
        buildZipFileArray  // Exported for testing
    };

})(window);
