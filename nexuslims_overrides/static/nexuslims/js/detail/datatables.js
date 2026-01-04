/**
 * NexusLIMS Detail Page - DataTables Initialization
 *
 * Handles initialization and configuration of DataTables on the detail page
 */

(function($, window) {
    'use strict';

    var Detail = window.NexusLIMSDetail;

    /**
     * Initialize the file list DataTable
     * @param {string} zip_title - The title for the zip file download
     * @returns {DataTable} The initialized DataTable instance
     */
    function initializeFileListTable(zip_title) {
        window.filelist_dt = new DataTable('table#filelist-table', {
            ordering: false,
            layout: {
                topStart: 'search',
                topEnd: 'paging',
                top2Start: 'buttons',
                bottomStart: 'info',
                bottomEnd: null
            },
            buttons: [
                {
                    extend: 'selectAll',
                    className: 'btn-select-all dl-btns',
                    text: "<i class='fas fa-check-square menu-fa'/> <span class='filelist-btn'>Select all</span>"
                },
                {
                    extend: 'selectNone',
                    className: 'btn-select-none dl-btns',
                    text: "<i class='far fa-square menu-fa'/> <span class='filelist-btn'>Select none</span>"
                },
                {
                    text: "<i class='fa fa-archive menu-fa'/> <span class='filelist-btn'>Download all as .zip</span>",
                    className: 'btn-dl-all dl-btns',
                    action: function(e, dt, node, config) {
                        var data_urls = dt.rows().data().map(x => $(x.data_dl).attr('href'));
                        var json_urls = dt.rows().data().map(x => $(x.json_dl).attr('href'));
                        var paths = dt.rows().data().map(x => $(x.path).text());
                        $('button.dl-btns').addClass('disabled');
                        window.filelist_dt.select.style('api');
                        Detail.downloadFn(data_urls, json_urls, paths, zip_title);
                    },
                    attr: {
                        'data-bs-toggle': 'tooltip',
                        'data-bs-placement': 'top',
                        'data-bs-html': true,
                        'title': 'Warning! This may take a significant amount of time depending on the number of files',
                        'onclick': 'blur()'
                    }
                },
                {
                    extend: 'selected',
                    text: "<i class='far fa-file-archive menu-fa'/> <span class='filelist-btn'>Download selected as .zip</span>",
                    attr: {
                        'data-bs-toggle': 'tooltip',
                        'data-bs-placement': 'top',
                        'data-bs-html': true,
                        'title': 'Warning! This may take a significant amount of time depending on the number of files'
                    },
                    className: 'btn-dl-selected dl-btns',
                    action: function(e, dt, node, config) {
                        var data_urls = dt.rows({ selected: true }).data().map(x => $(x.data_dl).attr('href'));
                        var json_urls = dt.rows({ selected: true }).data().map(x => $(x.json_dl).attr('href'));
                        var paths = dt.rows({ selected: true }).data().map(x => $(x.path).text());
                        $('button.dl-btns').addClass('disabled');
                        window.filelist_dt.select.style('api');
                        Detail.downloadFn(data_urls, json_urls, paths, zip_title);
                    }
                },
                {
                    extend: 'copyHtml5',
                    text: "<i class='far fa-copy menu-fa'/> <span class='filelist-btn'>Copy</span>",
                    exportOptions: {
                        columns: [1, 2, 3, 4]  // Export only visible columns (name, path, size, type)
                    }
                },
                {
                    extend: 'csvHtml5',
                    text: "<i class='fas fa-file-csv menu-fa'/> <span class='filelist-btn'>CSV</span>",
                    exportOptions: {
                        columns: [1, 2, 3, 4]
                    }
                },
                {
                    extend: 'excelHtml5',
                    text: "<i class='far fa-file-excel menu-fa'/> <span class='filelist-btn'>Excel</span>",
                    exportOptions: {
                        columns: [1, 2, 3, 4]
                    }
                },
                {
                    extend: 'print',
                    text: "<i class='fas fa-print menu-fa'/> <span class='filelist-btn'>Print</span>",
                    exportOptions: {
                        columns: [1, 2, 3, 4]
                    }
                }
            ],
            select: {
                style: 'multi',
            },
            columnDefs: [
                { data: 'checkbox', orderable: false, width: '1em', className: 'select-checkbox', targets: 0, "defaultContent": "" },
                { data: 'name', name: 'name', targets: 1 },
                { data: 'path', name: 'path', targets: 2 },
                { data: 'size', name: 'size', width: '4em', targets: 3 },
                { data: 'type', name: 'type', targets: 4 },
                { data: 'json_dl', name: 'json_dl', width: '3em', targets: 5 },
                { data: 'data_dl', name: 'data_dl', width: '3em', targets: 6 },
            ],
            language: {
                info: "Showing _START_ to _END_ of _TOTAL_ datasets",
                paginate: {
                    previous: "<i class='fa fa-angle-double-left'></i>",
                    next: "<i class='fa fa-angle-double-right'></i>"
                },
                select: {
                    rows: {
                        0: "",
                        _: "%d datasets selected",
                        1: "1 dataset selected"
                    }
                },
            },
        });

        return window.filelist_dt;
    }

    /**
     * Split buttons into two rows and add styling
     */
    function splitButtonRows() {
        const buttonContainer = $('#filelist-table_wrapper .dt-buttons');
        const allButtons = buttonContainer.find('button');
        const exportButtons = allButtons.slice(4);  // Get buttons 5-8 (Copy, CSV, Excel, Print)

        // Create a new row for export buttons
        const exportRow = $('<div class="dt-layout-row"><div class="dt-layout-cell"><div class="dt-buttons btn-group"></div></div></div>');
        exportButtons.detach().appendTo(exportRow.find('.dt-buttons'));
        buttonContainer.closest('.dt-layout-row').after(exportRow);

        // add styling classes
        buttonContainer.closest('.dt-layout-row').addClass('dl-btn-row');
        exportRow.addClass('export-btn-row');
    }

    /**
     * Move progress/result rows to after the export button row and before the table
     */
    function moveProgressRows() {
        const tableRow = $('#filelist-table_wrapper .dt-layout-row.dt-layout-table').first();
        if (tableRow.length > 0) {
            $('#btn-cancel-row').detach().insertBefore(tableRow);
            $('#progressbar-row').detach().insertBefore(tableRow);
            $('#dl-extra-row').detach().insertBefore(tableRow);
            $('#dl-result-row').detach().insertBefore(tableRow);
        }

        // Hide by default
        $('#progressbar-row').hide();
        $('#dl-result-row').hide();
        $('#dl-extra-row').hide();
        $('#btn-cancel-row').hide();
    }

    /**
     * Setup event listeners for download size calculation
     * @param {DataTable} dt - The DataTable instance
     */
    function setupDownloadSizeListeners(dt) {
        dt.on('select', function(e, dt, items) {
            var data_urls = dt.rows({ selected: true }).data().map(x => $(x.data_dl).attr('href'));
            var json_urls = dt.rows({ selected: true }).data().map(x => $(x.json_dl).attr('href'));
            Detail.showDownloadSize(data_urls, json_urls, 'select');
        });

        dt.on('deselect', function(e, dt, items) {
            var data_urls = dt.rows({ selected: true }).data().map(x => $(x.data_dl).attr('href'));
            var json_urls = dt.rows({ selected: true }).data().map(x => $(x.json_dl).attr('href'));
            Detail.showDownloadSize(data_urls, json_urls, 'select');
        });
    }

    /**
     * Check for .ser files and display warning if found
     * @param {DataTable} dt - The DataTable instance
     */
    function checkForSerFiles(dt) {
        let haveSers = dt.rows().data().map(x =>
            $(x.data_dl).attr('href')).toArray().some(x => x.endsWith('.ser'));

        if (haveSers) {
            let msg = 'At least one .ser file was detected in this record. While not listed in this table, any associated .emi metadata file will be added to the downloaded .zip archive and download size estimate.';
            $('#download-extra').closest('.row').slideDown();
            $('#download-extra')
                .removeClass('alert-warning alert-success alert-info alert-danger')
                .addClass("alert alert-warning")
                .text(msg);
        }
    }

    /**
     * Main initialization function for file list DataTable
     * @param {string} zip_title - The title for the zip file download
     */
    function initializeFileList(zip_title) {
        // Initialize the DataTable
        var dt = initializeFileListTable(zip_title);

        // Split buttons into two rows
        splitButtonRows();

        // Get all file sizes initially
        Detail.showDownloadSize(
            dt.rows().data().map(x => $(x.data_dl).attr('href')),
            dt.rows().data().map(x => $(x.json_dl).attr('href')),
            'initial'
        );

        // Setup event listeners
        setupDownloadSizeListeners(dt);

        // Move progress rows to correct position
        moveProgressRows();

        // Check for .ser files
        checkForSerFiles(dt);
    }

    /**
     * Helper function to inject page info into navigation table
     * @param {DataTable} navTable - The navigation DataTable instance
     */
    function injectNavPageInfo(navTable) {
        var $nav = $('#nav-table_wrapper .dt-paging nav');
        var $nextBtn = $nav.find('button[data-dt-idx="next"]');
        var $existingSpan = $nav.find('.nav-page-info');

        if ($nextBtn.length) {
            var info = navTable.page.info();
            var text = 'Page ' + (info.page + 1) + ' of ' + info.pages;

            if ($existingSpan.length) {
                // Update existing
                $existingSpan.text(text);
            } else {
                // Create new
                var $span = $('<span>', {
                    'class': 'nav-page-info',
                    'text': text
                });
                $nextBtn.before($span);
            }
        }
    }

    /**
     * Initialize the navigation table in the sidebar
     * @returns {DataTable} The initialized navigation table
     */
    function initializeNavigationTable() {
        var navTable = new DataTable('#nav-table', {
            destroy: true,
            pagingType: "simple",
            info: false,  // Disable built-in info - we'll create our own
            ordering: false,
            processing: false,
            searching: false,
            lengthChange: false,
            pageLength: 5,
            language: {
                paginate: {
                    previous: "<i class='fa fa-angle-double-left'></i>",
                    next: "<i class='fa fa-angle-double-right'></i>"
                }
            },
            responsive: false,
            altEditor: false,
            layout: {
                topStart: null,
                topEnd: 'paging',
                bottomStart: null,
                bottomEnd: null
            },
            initComplete: function() {
                setTimeout(function() { injectNavPageInfo(navTable); }, 0);
            },
            drawCallback: function() {
                setTimeout(function() { injectNavPageInfo(navTable); }, 0);
            }
        });

        // Watch for nav changes and immediately re-inject page info
        if (window.MutationObserver) {
            var isInjecting = false;
            var navObserver = new MutationObserver(function(mutations) {
                if (isInjecting) return; // Prevent infinite loop

                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        var $nav = $(mutation.target);
                        if ($nav.is('nav[aria-label="pagination"]')) {
                            var hasButtons = $nav.find('button[data-dt-idx]').length > 0;
                            var hasInfo = $nav.find('.nav-page-info').length > 0;

                            if (hasButtons && !hasInfo) {
                                isInjecting = true;
                                injectNavPageInfo(navTable);
                                isInjecting = false;
                            }
                        }
                    }
                });
            });

            // Observe the entire table wrapper to catch nav creation/updates
            setTimeout(function() {
                var $wrapper = $('#nav-table_wrapper');
                if ($wrapper.length) {
                    navObserver.observe($wrapper[0], { childList: true, subtree: true });
                }
            }, 100);
        }

        // Make nav-table rows clickable (use delegation to work after pagination)
        $('#nav-table').on('click', 'tbody tr', function() {
            window.location = $(this).find('a').attr('href');
            return false;
        });

        return navTable;
    }

    /**
     * Initialize metadata tables
     */
    function initializeMetadataTables() {
        $('.meta-table').each(function() {
            new DataTable(this, {
                destroy: true,
                pagingType: "simple_numbers",
                info: false,
                ordering: false,
                processing: true,
                searching: true,
                lengthChange: false,
                pageLength: 10,
                language: {
                    paginate: {
                        previous: "<i class='fa fa-angle-double-left'></i>",
                        next: "<i class='fa fa-angle-double-right'></i>"
                    }
                },
                responsive: true,
                layout: {
                    topStart: 'search',
                    topEnd: 'paging',
                    bottomStart: null,
                    bottomEnd: null
                }
            });
        });
    }

    /**
     * Initialize activity tables with image preview
     */
    function initializeActivityTables() {
        $('.aa-table').each(function() {
            var this_table = new DataTable(this, {
                destroy: true,
                pagingType: "simple_numbers",
                info: false,
                ordering: false,
                processing: true,
                searching: true,
                lengthChange: false,
                pageLength: 5,
                language: {
                    paginate: {
                        previous: "<i class='fa fa-angle-double-left'></i>",
                        next: "<i class='fa fa-angle-double-right'></i>"
                    }
                },
                // Column width definitions:
                // 0: Dataset Name (flexible, takes remaining space)
                // 1: Creation Time (fixed width for timestamp)
                // 2: Type (compact)
                // 3: Role (compact)
                // 4: Format (compact, conditional column)
                // 5/4: Meta (two icon buttons: modal + JSON download)
                // 6/5: D/L (single icon button: file download)
                columnDefs: [
                    { "width": "38%", "targets": 0 },  // Dataset Name - main content
                    { "width": "20%", "targets": 1 },  // Creation Time
                    { "width": "10%", "targets": 2 },  // Type
                    { "width": "12%", "targets": 3 },  // Role
                    // { "width": "15%", "targets": -2, "className": "text-center" },  // Meta (2 buttons)
                    // { "width": "8%", "targets": -1, "className": "text-center" }   // D/L (1 button)
                ],
                responsive: true,
                layout: {
                    topStart: null,
                    topEnd: null,
                    bottomStart: null,
                    bottomEnd: 'paging'
                }
            });

            // Image preview on row hover
            $(this).on('mouseenter', '> tbody > tr', function() {
                var this_rows_img = $(this).first().attr('img-id');
                var img_to_show = $('#' + this_rows_img);
                var img_to_hide = img_to_show.siblings('.aa-img.visible');
                img_to_hide.addClass('hidden').removeClass('visible');
                img_to_show.addClass('visible').removeClass('hidden');
            });
        });
    }

    /**
     * Initialize all navigation and metadata tables (non-simple display mode)
     */
    function initializeNavigationAndMetadata() {
        initializeNavigationTable();
        initializeMetadataTables();
        initializeActivityTables();
    }

    // Export to global namespace
    window.NexusLIMSDetail = window.NexusLIMSDetail || {};
    window.NexusLIMSDetail.DataTables = {
        initializeFileList: initializeFileList,
        initializeNavigationAndMetadata: initializeNavigationAndMetadata
    };

})(jQuery, window);
