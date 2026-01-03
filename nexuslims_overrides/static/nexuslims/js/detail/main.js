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
            // Make nav-table rows clickable
            $('#nav-table tbody tr').click(function() {
                window.location = $(this).find('a').attr('href');
                return false;
            });

            // Helper function to inject page info into nav
            function injectNavPageInfo() {
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

            // Navigation table in sidebar
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
                    setTimeout(injectNavPageInfo, 0);
                },
                drawCallback: function() {
                    setTimeout(injectNavPageInfo, 0);
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
                                    injectNavPageInfo();
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

            // Metadata tables
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
                    },
                    drawCallback: function() {
                        $('.dt-paging-button.next', this.api().table().container())
                            .on('click', Detail.activate_metadata_tooltips());
                        $('.dt-paging-button.previous', this.api().table().container())
                            .on('click', Detail.activate_metadata_tooltips());
                    }
                });
            });

            // Activity tables
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

                // Move pagination to custom container for layout purposes
                // DataTables 2.x uses .dt-layout-row and .dt-layout-end for pagination
                // var new_container = $(this).closest('.aa-content-row').next('.dt_paginate_container');
                // var to_move = $(this).closest('.table-row').next('.pager-row').find('.pager-col');
                // var dt_paging = $(this).closest('.dt-container').find('.dt-layout-row .dt-layout-end');

                // console.log('AA Table pagination move debug:');
                // console.log('  to_move:', to_move, 'length:', to_move.length);
                // console.log('  new_container:', new_container, 'length:', new_container.length);
                // console.log('  dt_paging:', dt_paging, 'length:', dt_paging.length);
                // console.log('  dt-container:', $(this).closest('.dt-container'));
                // console.log('    ')
                // console.log('    ')
                // console.log('    ')

                // if (new_container.length && dt_paging.length) {
                //     console.log('  -> Moving pagination to custom container');
                //     new_container.append(dt_paging);
                // } else {
                //     console.log('  -> Skipping pagination move (container or paging not found)');
                // }
            });
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

        window.filelist_dt = new DataTable('table#filelist-table', {
            ordering: false,
            dom: "<'row'<'col-sm-6'f><'col-sm-6'p>><'row'<'#button-col.col-sm-12 text-center'B>><'row'<'col-sm-12 w-100't>><'#filelist_info_row.row'<'col-sm-12'i>>",
            buttons: [
                {
                    extend: 'selectAll',
                    className: 'btn-select-all dl-btns',
                    text: "<i class='fas fa-check-square menu-fa'/> <span class='filelist-btn'>Select all</span>"
                },
                {
                    extend: 'selectNone',
                    className: 'btn-select-none dl-btns',
                    text: "<i class='far fa-square menu-fa'/> <span class='filelist-btn''>Select none</span>"
                },
                {
                    text: "<i class='fa fa-archive menu-fa'/> <span class='filelist-btn''>Download all as .zip</span>",
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
                        'data-toggle': 'tooltip',
                        'data-placement': 'top',
                        'data-html': true,
                        'title': 'Warning! This may take a significant amount of time depending on the number of files'
                    }
                },
                {
                    extend: 'selected',
                    text: "<i class='far fa-file-archive menu-fa'/> <span class='filelist-btn'>Download selected as .zip</span>",
                    attr: {
                        'data-toggle': 'tooltip',
                        'data-placement': 'top',
                        'data-html': true,
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

        // Get all file sizes initially
        Detail.showDownloadSize(
            window.filelist_dt.rows().data().map(x => $(x.data_dl).attr('href')),
            window.filelist_dt.rows().data().map(x => $(x.json_dl).attr('href')),
            'initial'
        );

        // Check for .ser files
        let haveSers = window.filelist_dt.rows().data().map(x =>
            $(x.data_dl).attr('href')).toArray().some(x => x.endsWith('.ser'));

        // Event listeners for download size calculation
        window.filelist_dt.on('select', function(e, dt, items) {
            var data_urls = dt.rows({ selected: true }).data().map(x => $(x.data_dl).attr('href'));
            var json_urls = dt.rows({ selected: true }).data().map(x => $(x.json_dl).attr('href'));
            Detail.showDownloadSize(data_urls, json_urls, 'select');
        });
        window.filelist_dt.on('deselect', function(e, dt, items) {
            var data_urls = dt.rows({ selected: true }).data().map(x => $(x.data_dl).attr('href'));
            var json_urls = dt.rows({ selected: true }).data().map(x => $(x.json_dl).attr('href'));
            Detail.showDownloadSize(data_urls, json_urls, 'select');
        });

        // Export buttons - Note: Secondary button group creation disabled in DataTables 2.x
        // The copy/csv/excel/print buttons for file list are not critical for core functionality
        // and can be re-enabled if needed by updating to proper DataTables 2.x Buttons API

        // TODO: Re-implement secondary button group using DataTables 2.x buttons.add() API
        // See: https://datatables.net/reference/api/buttons.add()

        // Move progress/result rows
        $('#progressbar-row').detach().insertAfter($('#second-btn-group').closest('.row'));
        $('#dl-result-row').detach().insertAfter($('#progressbar-row'));
        $('#dl-extra-row').detach().insertBefore($('#dl-result-row'));
        $('#btn-cancel-row').detach().insertBefore($('#progressbar-row'));

        // Hide by default
        $('#progressbar-row').hide();
        $('#dl-result-row').hide();
        $('#dl-extra-row').hide();
        $('#btn-cancel-row').hide();

        if (haveSers) {
            let msg = 'At least one .ser file was detected in this record. While not listed in this table, any associated .emi metadata file will be added to the downloaded .zip archive and download size estimate.';
            $('#download-extra').closest('.row').slideDown();
            $('#download-extra')
                .removeClass('alert-warning alert-success alert-info alert-danger')
                .addClass("alert alert-warning")
                .text(msg);
        }

        // ====================================================================
        // Event Handlers
        // ====================================================================

        $("#btn-xml-dl").on('click', Detail.downloadXML);
        $('a#menu-tutorial').on('click', () => Detail.create_detail_tour());

        // Replace placeholder images
        const image_data = $("#placeholder-preview-src").text();
        $('img.preview-placeholder').attr("src", image_data).removeClass('preview-placeholder');

        // Simple display hover controllers
        if (simpleDisplay) {
            $("a.simple-filelist-preview").mouseover(function() {
                $("a.simple-filelist-preview img").css("display", "none");
                $(this).find("img").css("display", "inline-block");
            });
            $("a.simple-filelist-preview").mouseout(function() {
                $("a.simple-filelist-preview img").css("display", "none");
            });
        }

        // Make sidebar visible after loading
        if (!simpleDisplay) {
            $('.sidebar').first().css('visibility', 'visible');
        }

        // Initialize all Bootstrap 5 tooltips on the page
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Fade out loading screen
        $('#loading').fadeOut('slow');
    });

})(jQuery, window);
