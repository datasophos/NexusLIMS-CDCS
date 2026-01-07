/**
 * NexusLIMS Detail Page - Main Initialization
 *
 * Document ready handler, DataTables initialization, and page orchestration
 */

(function($, window) {
    'use strict';

    var Detail = window.NexusLIMSDetail;

    $(document).ready(function() {

        // Check if we're on a detail page
        if ($('#simpleDisplay').length === 0) {
            return;
        }

        var simpleDisplay = $('#simpleDisplay').text() == 'true';

        // ====================================================================
        // Navigation and Activity Tables (DataTables)
        // ====================================================================

        if (!simpleDisplay) {
            // Initialize navigation and metadata tables
            Detail.DataTables.initializeNavigationAndMetadata();
        }

        // ====================================================================
        // File List Processing
        // ====================================================================

        $('div#filelist-modal').each(function() {
            var paths = $('td.filepath').map(function() {
                return $(this).text();
            }).get();
            var rootPath = Detail.commonPath(paths, '/');
            $('td.filepath > code > a').each(function() {
                var curText = $(this).text();
                var newText = curText.replace(rootPath, '');
                if (newText.length == 0) {
                    newText = '/';
                }
                newText = Detail.addEndingSlash(newText);
                $(this).attr("href", $(this).attr("href") + rootPath + newText);
                $(this).text(decodeURIComponent(newText));
            });

            rootPath = Detail.addEndingSlash(rootPath);
            $('code#filelist-rootpath > a').each(function() {
                $(this).text(decodeURIComponent(rootPath));
                $(this).attr("href", $(this).attr("href") + rootPath);
            });

            window.rootPath = rootPath;
        });

        // ====================================================================
        // Record Info
        // ====================================================================

        var d = new Date($('span.list-record-date').text());
        var ye = new Intl.DateTimeFormat('en', { year: 'numeric' }).format(d);
        var mo = new Intl.DateTimeFormat('en', { month: '2-digit' }).format(d);
        var da = new Intl.DateTimeFormat('en', { day: '2-digit' }).format(d);
        var record_title = $('span#xmlName').text();
        var zip_title = record_title.endsWith('.xml') ? record_title.replace('.xml', '.zip') : record_title + '.zip';
        var record_header = 'NexusLIMS Experiment: ' + $('span.list-record-title').text() + '\n' +
            'Instrument: ' + $('span#instr-badge').text() + '\n' +
            'Experimenter: ' + $('span.list-record-experimenter').text() + '\n' +
            'Date: ' + $('span.list-record-date').text();

        // ====================================================================
        // File List DataTable
        // ====================================================================

        Detail.DataTables.initializeFileList(zip_title);

        // ====================================================================
        // Event Handlers
        // ====================================================================

        $("#btn-xml-dl").on('click', () => Detail.Downloads.downloadRecord("XML"));
        $("#btn-json-dl").on('click', () => Detail.Downloads.downloadRecord("JSON"));
        $('a#menu-tutorial').on('click', () => Detail.create_detail_tour());

        // Replace placeholder images
        const image_data = $("#placeholder-preview-src").text();
        $('img.preview-placeholder').attr("src", image_data).removeClass('preview-placeholder');

        // Simple display hover controllers
        if (simpleDisplay) {
            // Initialize simple file list table as DataTable
            Detail.DataTables.initializeSimpleFileListTable();

            $("a.simple-filelist-preview").mouseover(function() {
                $("a.simple-filelist-preview img").css("display", "none");
                $(this).find("img").css("display", "inline-block");
            });
            $("a.simple-filelist-preview").mouseout(function() {
                $("a.simple-filelist-preview img").css("display", "none");
            });
        }

        // Setup dynamic header positioning for all tables
        Detail.DataTables.setupDynamicHeader();

        // Make sidebar visible after loading
        if (!simpleDisplay) {
            $('.sidebar').first().css('visibility', 'visible');
        }

        // Initialize all Bootstrap 5 tooltips on the page
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Check edit permissions and hide button if user doesn't have access
        Detail.checkEditPermissions();

        // Fade out loading screen
        $('#loading').fadeOut('slow');
    });

})(jQuery, window);
