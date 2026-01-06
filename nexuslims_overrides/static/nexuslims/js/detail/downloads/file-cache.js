/**
 * NexusLIMS Detail Page - File Cache Module
 *
 * Manages HEAD requests and file size caching for download size estimation
 */

(function(window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.Downloads = window.NexusLIMSDetail.Downloads || {};

    // Private state
    const fileSizeCache = new Map();
    let isInitialized = false;

    /**
     * Fetch file size using HEAD request
     * @param {string} url - The URL to check
     * @returns {Promise<{url: string, size: number}>} URL and size (NaN if failed)
     */
    async function fetchFileSize(url) {
        try {
            const response = await fetch(url, { method: 'HEAD' });
            if (response.status === 200) {
                const contentLength = response.headers.get('content-length');
                const size = contentLength ? Number(contentLength) : NaN;
                return { url, size };
            } else {
                console.warn(`Could not fetch file size for ${url} (status: ${response.status})`);
                return { url, size: NaN };
            }
        } catch (error) {
            console.warn(`Error fetching file size for ${url}:`, error.message);
            return { url, size: NaN };
        }
    }

    /**
     * Initialize the file cache with HEAD requests for all files
     * @param {string[]} dataUrls - Array of data file URLs
     * @param {string[]} jsonUrls - Array of JSON metadata URLs
     * @param {string[]} emiUrls - Array of EMI file URLs (may contain nulls)
     * @returns {Promise<void>}
     */
    async function initialize(dataUrls, jsonUrls, emiUrls = []) {
        // Combine all unique URLs
        const allUrls = [...new Set([...dataUrls, ...jsonUrls, ...emiUrls.filter(url => url !== null)])];

        // Batch fetch all file sizes
        const promises = allUrls.map(url => fetchFileSize(url));
        const results = await Promise.all(promises);

        // Populate cache
        results.forEach(({ url, size }) => {
            fileSizeCache.set(url, size);
        });

        isInitialized = true;

        console.info(`File cache initialized with ${fileSizeCache.size} files`);
    }

    /**
     * Get cached file size
     * @param {string} url - The URL to look up
     * @returns {number} File size in bytes (NaN if not found or failed)
     */
    function getSize(url) {
        return fileSizeCache.get(url) || NaN;
    }

    /**
     * Calculate total size for an array of URLs
     * @param {string[]} urls - Array of URLs to sum
     * @returns {number} Total size in bytes (excludes NaN values)
     */
    function getTotalSize(urls) {
        return urls.reduce((total, url) => {
            const size = getSize(url);
            return total + (isNaN(size) ? 0 : size);
        }, 0);
    }

    /**
     * Check if cache has been initialized
     * @returns {boolean}
     */
    function checkInitialized() {
        return isInitialized;
    }

    /**
     * Get all cached entries (for debugging)
     * @returns {Map<string, number>}
     */
    function getAllEntries() {
        return new Map(fileSizeCache);
    }

    /**
     * Clear the cache
     */
    function clear() {
        fileSizeCache.clear();
        isInitialized = false;
    }

    // Public API
    window.NexusLIMSDetail.Downloads.FileCache = {
        initialize,
        getSize,
        getTotalSize,
        isInitialized: checkInitialized,
        getAllEntries,
        clear
    };

})(window);
