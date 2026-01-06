/**
 * NexusLIMS Detail Page - EMI Bundler Module
 *
 * Handles .ser/.emi file pairing logic for STEM data downloads
 */

(function(window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.Downloads = window.NexusLIMSDetail.Downloads || {};

    /**
     * Extract .emi filename from .ser filename
     * Pattern: {prefix}_{digits}.ser → {prefix}.emi
     * @param {string} serUrl - URL ending in .ser
     * @returns {string|null} Corresponding .emi URL, or null if pattern doesn't match
     */
    function getEmiUrl(serUrl) {
        const regex = /(.*)_[0-9]+\.ser$/;
        const match = regex.exec(serUrl);

        if (match === null) {
            return null;
        }

        // Replace the _{digits}.ser part with .emi
        return serUrl.replace(/_[0-9]+\.ser$/, '.emi');
    }

    /**
     * Prepare complete file list with .emi files bundled
     * @param {string[]} dataUrls - Array of data file URLs
     * @param {string[]} jsonUrls - Array of JSON metadata URLs
     * @param {string[]} paths - Array of file paths for ZIP structure
     * @returns {Array<{dataUrl: string, jsonUrl: string, emiUrl: string|null, path: string}>}
     */
    function prepareFileList(dataUrls, jsonUrls, paths) {
        if (dataUrls.length !== jsonUrls.length || dataUrls.length !== paths.length) {
            throw new Error('Array lengths must match: dataUrls, jsonUrls, and paths');
        }

        const fileList = [];

        for (let i = 0; i < dataUrls.length; i++) {
            const dataUrl = dataUrls[i];
            const jsonUrl = jsonUrls[i];
            const path = paths[i];

            // Check if this is a .ser file that needs an .emi companion
            let emiUrl = null;
            if (dataUrl.endsWith('.ser')) {
                emiUrl = getEmiUrl(dataUrl);

                // Validate .emi file exists in cache
                if (emiUrl && window.NexusLIMSDetail.Downloads.FileCache) {
                    const emiSize = window.NexusLIMSDetail.Downloads.FileCache.getSize(emiUrl);
                    if (isNaN(emiSize)) {
                        // .emi file doesn't exist or failed to fetch
                        console.warn(`EMI file not found for ${dataUrl}: ${emiUrl}`);
                        emiUrl = null;
                    }
                }
            }

            fileList.push({
                dataUrl,
                jsonUrl,
                emiUrl,
                path
            });
        }

        return fileList;
    }

    /**
     * Get array of all EMI URLs from data URLs (for cache initialization)
     * @param {string[]} dataUrls - Array of data file URLs
     * @returns {string[]} Array of .emi URLs (may contain nulls for non-.ser files)
     */
    function getEmiUrlsForCache(dataUrls) {
        return dataUrls.map(dataUrl => {
            if (dataUrl.endsWith('.ser')) {
                return getEmiUrl(dataUrl);
            }
            return null;
        });
    }

    /**
     * Deduplicate file list (for multi-signal datasets)
     * @param {Array} fileList - File list from prepareFileList()
     * @returns {Array} Deduplicated file list
     */
    function deduplicateFileList(fileList) {
        const seen = new Map();
        const deduplicated = [];

        for (const file of fileList) {
            if (!seen.has(file.dataUrl)) {
                seen.set(file.dataUrl, true);
                deduplicated.push(file);
            }
        }

        return deduplicated;
    }

    // Public API
    window.NexusLIMSDetail.Downloads.EmiBundler = {
        prepareFileList,
        getEmiUrlsForCache,
        deduplicateFileList,
        getEmiUrl  // Exported for testing/utilities
    };

})(window);
