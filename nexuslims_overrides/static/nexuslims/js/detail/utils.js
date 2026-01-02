/**
 * NexusLIMS Detail Page - Utility Functions
 *
 * Browser detection, path manipulation, array operations, and file size formatting
 */

(function(window) {
    'use strict';

    // Create namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};

    // ============================================================================
    // Browser Detection
    // ============================================================================

    // Opera 8.0+
    window.NexusLIMSDetail.isOpera = (!!window.opr && !!opr.addons) || !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
    // Firefox 1.0+
    window.NexusLIMSDetail.isFirefox = typeof InstallTrigger !== 'undefined';
    // Safari 3.0+
    window.NexusLIMSDetail.isSafari = /constructor/i.test(window.HTMLElement) || (function (p) { return p.toString() === "[object SafariRemoteNotification]"; })(!window['safari'] || (typeof safari !== 'undefined' && safari.pushNotification));
    // Internet Explorer 6-11
    window.NexusLIMSDetail.isIE = /*@cc_on!@*/false || !!document.documentMode;
    // Edge 20+
    window.NexusLIMSDetail.isEdge = !window.NexusLIMSDetail.isIE && !!window.StyleMedia;
    // Chrome 1 - 79
    window.NexusLIMSDetail.isChrome = !!window.chrome;
    // Edge (based on chromium)
    window.NexusLIMSDetail.isEdgeChromium = window.NexusLIMSDetail.isChrome && (navigator.userAgent.indexOf("Edg") != -1);
    // Blink engine
    window.NexusLIMSDetail.isBlink = (window.NexusLIMSDetail.isChrome || window.NexusLIMSDetail.isOpera) && !!window.CSS;

    // ============================================================================
    // Path Manipulation Functions
    // ============================================================================

    // From https://www.rosettacode.org/wiki/Find_common_directory_path#JavaScript
    const splitStrings = (a, sep = '/') => a.map(i => i.split(sep));
    const elAt = i => a => a[i];
    const rotate = a => a[0].map((e, i) => a.map(elAt(i)));
    const allElementsEqual = arr => arr.every(e => e === arr[0]);

    window.NexusLIMSDetail.commonPath = function(input, sep = '/') {
        return rotate(splitStrings(input, sep)).filter(allElementsEqual).map(elAt(0)).join(sep);
    };

    window.NexusLIMSDetail.addEndingSlash = function(str) {
        if (!(str.charAt(str.length - 1) === '/')) {
            return str + '/';
        } else {
            return str;
        }
    };

    // ============================================================================
    // Array Operations
    // ============================================================================

    window.NexusLIMSDetail.arrSum = arr => arr.reduce((a, b) => a + b, 0);
    window.NexusLIMSDetail.arrAvg = arr => window.NexusLIMSDetail.arrSum(arr) / arr.length;

    // ============================================================================
    // File Size Formatting
    // ============================================================================

    // From https://stackoverflow.com/a/14919494/1435788
    window.NexusLIMSDetail.humanFileSize = function(bytes, si) {
        var thresh = si ? 1000 : 1024;
        if (Math.abs(bytes) < thresh) {
            return bytes + ' B';
        }
        var units = si
            ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
            : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
        var u = -1;
        do {
            bytes /= thresh;
            ++u;
        } while (Math.abs(bytes) >= thresh && u < units.length - 1);
        return bytes.toFixed(1) + ' ' + units[u];
    };

    // ============================================================================
    // Clipboard Functions
    // ============================================================================

    window.NexusLIMSDetail.copyToClipboard = function(element) {
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($(element).text()).select();
        document.execCommand("copy");
        $temp.remove();
    };

    window.NexusLIMSDetail.copy_and_change_tt = function() {
        window.NexusLIMSDetail.copyToClipboard('#pid-to-copy');
        let new_title = "Copied PID to clipboard!";
        $('#btn-copy-pid').attr('data-original-title', new_title);
        $('#btn-copy-pid').tooltip('update');
        $('#btn-copy-pid').tooltip('show');
    };

    // ============================================================================
    // File Name Helpers
    // ============================================================================

    // Extract .emi filename from .ser filename
    window.NexusLIMSDetail.getEmiName = function(serName) {
        let re = /(.*)_[0-9]+\.ser/;
        let match = re.exec(serName);
        if (match == null) {
            return null;
        } else {
            return match[1] + '.emi';
        }
    };

    // ============================================================================
    // XML Formatting
    // ============================================================================

    // From https://stackoverflow.com/a/49458964/1435788
    window.NexusLIMSDetail.formatXml = function(xml, tab) {
        var formatted = '', indent = '';
        tab = tab || '\t';
        xml.split(/>\s*</).forEach(function(node) {
            if (node.match(/^\/\w/)) indent = indent.substring(tab.length);
            formatted += indent + '<' + node + '>\r\n';
            if (node.match(/^<?\w[^>]*[^\/]$/)) indent += tab;
        });
        formatted = formatted.split('  ').join(' ');
        return formatted.substring(1, formatted.length - 3);
    };

})(window);
