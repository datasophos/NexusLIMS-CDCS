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

            // Navigation table in sidebar
            var navTable = new DataTable('#nav-table', {
                destroy: true,
                pagingType: "simple",
                info: false,
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
                responsive: true,
                altEditor: false,
                layout: {
                    topStart: null,
                    topEnd: 'paging',
                    bottomStart: null,
                    bottomEnd: null
                },
                drawCallback: function() {
                    $('.dt-paging-button.next', this.api().table().container())
                        .on('click', function() {
                            var info = navTable.page.info();
                            $('.cdatatableDetails').remove();
                            $('.sidebar .dt-paging-button.next').before($('<span>', {
                                'text': ' Page ' + (info.page + 1) + ' of ' + info.pages + ' ',
                                class: 'cdatatableDetails'
                            }));
                            $('.sidebar .dt-paging').first().addClass('vertical-align');
                        });
                    $('.dt-paging-button.previous', this.api().table().container())
                        .on('click', function() {
                            var info = navTable.page.info();
                            $('.cdatatableDetails').remove();
                            $('.sidebar .dt-paging-button.next').before($('<span>', {
                                'text': 'Page ' + (info.page + 1) + ' of ' + info.pages,
                                class: 'cdatatableDetails'
                            }));
                            $('.sidebar .dt-paging').first().addClass('vertical-align');
                        });
                }
            });

            var info = navTable.page.info();
            $('.sidebar .dt-paging-button.next').before($('<span>', {
                'text': ' Page ' + (info.page + 1) + ' of ' + info.pages + ' ',
                class: 'cdatatableDetails'
            }));
            $('.sidebar .dt-paging').first().addClass('vertical-align');

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
                    columnDefs: [
                        { "width": "53%", "targets": 0 }
                    ],
                    responsive: true,
                    dom: '<"row table-row"<"col-xs-12 table-col"t>><"row pager-row"<"col-xs-12 pager-col"p>>'
                });

                // Image preview on row hover
                $(this).on('mouseenter', '> tbody > tr', function() {
                    var this_rows_img = $(this).first().attr('img-id');
                    var img_to_show = $('#' + this_rows_img);
                    var img_to_hide = img_to_show.siblings('.aa-img.visible');
                    img_to_hide.addClass('hidden').removeClass('visible');
                    img_to_show.addClass('visible').removeClass('hidden');
                });

                var new_container = $(this).closest('.aa-content-row').next('.dt_paginate_container');
                var to_move = $(this).closest('.table-row').next('.pager-row').find('.pager-col');
                new_container.append(to_move);
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
