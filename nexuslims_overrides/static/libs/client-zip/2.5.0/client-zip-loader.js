/**
 * Client-Zip ES Module Loader
 *
 * Loads client-zip as an ES module and exposes downloadZip to the global scope
 */

import { downloadZip } from './index.js';

// Expose to window for non-module scripts
window.downloadZip = downloadZip;

// console.info('client-zip loaded and available as window.downloadZip');
