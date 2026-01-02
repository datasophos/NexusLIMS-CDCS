/**
 * NexusLIMS Detail Page - Download Functionality
 *
 * StreamSaver.js-based file download with progress tracking and zip support
 */

(function($, streamSaver, JSZip, window) {
    'use strict';

    var Detail = window.NexusLIMSDetail;

    // Get polyfill if needed (browser has native support so these may not be used)
    var ponyfill = window.WebStreamsPolyfill || {};
    var WebStreamsAdapter = window.WebStreamsAdapter || {
        createReadableStreamWrapper: function(Stream) { return function(s) { return s; }; }
    };

    // Store file sizes globally
    window.file_sizes = {};

    // ============================================================================
    // Progress and Messaging Functions
    // ============================================================================

    function resetMessage() {
        var $result = $("#download-result");
        if (!$result.is(':visible')) {
            $result.closest('.row').slideDown();
        }
        $result.text(" ");
    }

    function showMessage(text, type) {
        resetMessage();
        $("#download-result")
            .removeClass('alert-warning alert-success alert-info alert-danger')
            .addClass("alert alert-" + type)
            .text(text);
    }

    function showExtraMessage(text, type) {
        $("#download-extra").closest('.row').slideDown();
        $("#download-extra")
            .removeClass('alert-warning alert-success alert-info alert-danger')
            .addClass("alert alert-" + type)
            .text(text);
    }

    function hideExtraMessage() {
        $("#download-extra").closest('.row').slideUp();
    }

    function showError(text) {
        resetMessage();
        $("#download-result")
            .removeClass('alert-sucess alert-warning alert-info')
            .addClass("alert alert-danger")
            .text(text);
    }

    function updatePercent(percent) {
        $("#progress_bar").addClass('active')
            .closest('.row').slideDown()
            .find(".progress-bar")
            .attr("aria-valuenow", percent)
            .removeClass("progress-bar-warning progress-bar-success")
            .addClass("progress-bar-info")
            .css({
                width: percent + "%",
                'min-width': "5%"
            }).text(percent + '%');
    }

    function updateProgressBar(bytesDownloaded, totalToDownload) {
        let percent = (bytesDownloaded / totalToDownload * 100) | 0;
        $("#progress_bar").addClass('active')
            .closest('.row').slideDown()
            .find(".progress-bar")
            .attr("aria-valuenow", percent)
            .removeClass("progress-bar-warning progress-bar-success progress-bar-danger")
            .addClass("progress-bar-info")
            .css({
                width: percent + "%",
                'min-width': "5%"
            }).text(percent + '%');
        updateProgressMessage(bytesDownloaded, totalToDownload);
    }

    function updateProgressMessage(bytesDownloaded, totalToDownload) {
        var msg = (bytesDownloaded === '0 B') ?
            "Download is starting, please be patient..." :
            "Downloaded " + Detail.humanFileSize(bytesDownloaded) +
            ' out of ' + Detail.humanFileSize(totalToDownload) + '.';
        showMessage(msg, 'info');
    }

    function errorProgress() {
        updatePercent(100);
        $("#progress_bar")
            .removeClass('active')
            .closest('.row').slideDown()
            .find(".progress-bar")
            .removeClass('progress-bar-info progress-bar-success progress-bar-warning')
            .addClass('progress-bar-danger')
            .text('Error!');
    }

    function finishProgress() {
        updatePercent(100);
        $("#progress_bar")
            .removeClass('active')
            .closest('.row').slideDown()
            .find(".progress-bar")
            .removeClass('progress-bar-info progress-bar-danger progress-bar-warning')
            .addClass('progress-bar-success')
            .text('Finished!');
    }

    // ============================================================================
    // File Size Fetching
    // ============================================================================

    async function get_url_size(url) {
        let res = await fetch(url, { method: 'HEAD' });
        if (res.status == 200) {
            let contentlength = Number(res.headers.get('content-length'));
            return { 'url': url, 'size': contentlength };
        } else {
            console.warn(`Could not fetch file size for ${url} (file might not exist)`);
            return { 'url': url, 'size': NaN };
        }
    }

    Detail.showDownloadSize = function(data_urls, json_urls, type) {
        resetMessage();
        showMessage('Calculating download size...', 'info');

        let aux_urls = data_urls.map(Detail.getEmiName);

        var combinedObject = data_urls.map(function(e, i) {
            return [e, json_urls[i], aux_urls[i]];
        });
        var combinedArray = $.map(combinedObject, function(value, index) {
            return [value];
        });

        // Deduplicate URLs for multi-signal datasets
        var uniqueMap = new Map();
        combinedArray.forEach(function(item) {
            var data_url = item[0];
            if (!uniqueMap.has(data_url)) {
                uniqueMap.set(data_url, item);
            }
        });
        combinedArray = Array.from(uniqueMap.values());

        var total_size = 0;
        var promList = [];
        var sizeList = [];

        combinedArray.forEach(function(item, index) {
            let this_data_url = item[0];
            let this_json_url = item[1];
            let this_aux_url = item[2];

            // Check cache for data URL
            if (this_data_url in window.file_sizes) {
                promList.push(Promise.resolve());
                let this_data_size = window.file_sizes[this_data_url];
                total_size += this_data_size;
                sizeList.push({ name: this_data_url, size: this_data_size });
            } else {
                let data_prom = get_url_size(this_data_url);
                promList.push(data_prom);
                data_prom.then(res => {
                    total_size += res.size;
                    sizeList.push({ name: res.url, size: res.size });
                });
            }

            // Check cache for JSON URL
            if (this_json_url in window.file_sizes) {
                promList.push(Promise.resolve());
                let this_json_size = window.file_sizes[this_json_url];
                total_size += this_json_size;
                sizeList.push({ name: this_json_url, size: this_json_size });
            } else {
                let json_prom = get_url_size(this_json_url);
                promList.push(json_prom);
                json_prom.then(res => {
                    total_size += res.size;
                    sizeList.push({ name: res.url, size: res.size });
                });
            }

            // Handle auxiliary URLs
            if (this_aux_url) {
                if (this_aux_url in window.file_sizes) {
                    promList.push(Promise.resolve());
                    let this_aux_size = window.file_sizes[this_aux_url];
                    if (!isNaN(window.file_sizes[this_aux_url])) {
                        total_size += this_aux_size;
                        sizeList.push({ name: this_aux_url, size: this_aux_size });
                    }
                } else {
                    let aux_prom = get_url_size(this_aux_url);
                    promList.push(aux_prom);
                    aux_prom.then(res => {
                        if (res !== null) {
                            console.debug(`Adding ${res.size} for ${res.url}`);
                            if (!isNaN(res.size)) {
                                total_size += res.size;
                            }
                            sizeList.push({ name: res.url, size: res.size });
                        }
                    });
                }
            }
        });

        Promise.all(promList).then(function() {
            var human_dl_size = Detail.humanFileSize(total_size);
            window.total_size = total_size;
            window.human_dl_size = human_dl_size;
            sizeList.map(function(v, i) {
                window.file_sizes[v['name']] = v['size'];
            });

            // Update filelisting table if initial run
            if (type === 'initial' && window.filelist_dt) {
                window.filelist_dt.rows().every(function(rowIdx, tableLoop, rowLoop) {
                    var d = this.data();
                    var a = d.data_dl;
                    var url = $(a)[0].href;
                    this.cell(rowIdx, 'size:name').data(Detail.humanFileSize(window.file_sizes[url]));
                });
            }

            let msg = (type === 'initial' ?
                'Total size of all datasets: ' :
                'Total download size: ');

            showMessage(msg + human_dl_size + (
                aux_urls.toArray().some((obj) => obj !== null) ?
                ' (includes some auxillary data files not explicitly listed below).' :
                '.'), 'info');
        });
    };

    // ============================================================================
    // Download Function
    // ============================================================================

    Detail.downloadFn = function(data_urls, json_urls, paths, zip_title) {
        if (!(Detail.isChrome || Detail.isOpera || Detail.isFirefox || Detail.isEdgeChromium)) {
            alert('Due to browser limitations, downloading of files into a zip archive is only supported in up-to-date versions of Chrome, Firefox, Opera, and Edge browsers. Please either download the files individually using the buttons in the table, or download them manually from the central file server instead.');
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi');
            return;
        }

        resetMessage();
        updatePercent(0);

        let aux_urls = data_urls.map(Detail.getEmiName);
        $('#btn-cancel-row').slideDown();

        let combinedObject = data_urls.map(function(e, i) {
            return [e, json_urls[i], paths[i], aux_urls[i]];
        });
        let combinedArray = $.map(combinedObject, function(value, index) {
            return [value];
        });

        let zips = [];
        let zip_total_sizes = [];
        let indiv_dl_sizes = [];
        let zip_url_listing = [];
        let zip_path_listing = [];
        let cur_zip_idx = 0;
        let this_zip_size = 0;

        const size_limit = 4294967296; // 4.0 GiB

        var loopLength = combinedArray.length;
        var individual_files = [];

        // Allocate files to zips based on size
        for (var index = 0; index < loopLength; index += 1) {
            let item = combinedArray[index];
            let this_data_url = item[0];
            let this_json_url = item[1];
            let this_path = item[2];
            let this_aux_url = item[3];

            if (this_path.charAt(0) === '/') {
                this_path = this_path.substr(1);
            }

            let data_filename = this_data_url.replace(/.*\//g, "");
            let json_filename = this_json_url.replace(/.*\//g, "");
            let aux_filename = this_aux_url ? this_aux_url.replace(/.*\//g, "") : null;

            let full_data_path = this_path.length > 0 ? this_path + '/' + data_filename : data_filename;
            let full_json_path = this_path.length > 0 ? this_path + '/' + json_filename : json_filename;
            let full_aux_path = this_aux_url && this_path.length > 0 ? this_path + '/' + aux_filename : aux_filename;

            full_data_path = decodeURIComponent(full_data_path);
            full_json_path = decodeURIComponent(full_json_path);
            if (full_aux_path) full_aux_path = decodeURIComponent(full_aux_path);

            let this_file_size = window.file_sizes[this_data_url] + window.file_sizes[this_json_url];
            if (!isNaN(window.file_sizes[this_aux_url])) {
                this_file_size += window.file_sizes[this_aux_url];
            }

            if (this_file_size > size_limit) {
                individual_files.push(combinedArray[index][0]);
                individual_files.push(combinedArray[index][1]);
                if (full_aux_path && (!isNaN(window.file_sizes[this_aux_url]))) {
                    individual_files.push(combinedArray[index][3]);
                }
                indiv_dl_sizes.push(window.file_sizes[this_data_url]);
                indiv_dl_sizes.push(window.file_sizes[this_json_url]);
                if (!isNaN(window.file_sizes[this_aux_url])) {
                    indiv_dl_sizes.push(window.file_sizes[this_aux_url]);
                }
                loopLength -= 1;
                combinedArray.splice(index, 1);
                index -= 1;
                continue;
            }

            if (this_zip_size === 0) {
                zips.push({});
                zip_url_listing.push([]);
                zip_path_listing.push([]);
            } else {
                let new_size = this_zip_size;
                if (!zip_url_listing[cur_zip_idx].includes(this_data_url) && !isNaN(window.file_sizes[this_data_url])) {
                    new_size += window.file_sizes[this_data_url];
                }
                if (!zip_url_listing[cur_zip_idx].includes(this_json_url) && !isNaN(window.file_sizes[this_json_url])) {
                    new_size += window.file_sizes[this_json_url];
                }
                if (!isNaN(window.file_sizes[this_aux_url]) && !zip_url_listing[cur_zip_idx].includes(this_aux_url)) {
                    new_size += window.file_sizes[this_aux_url];
                }
                if (new_size > size_limit) {
                    zip_total_sizes.push(this_zip_size);
                    this_zip_size = 0;
                    cur_zip_idx += 1;
                    index--;
                    continue;
                }
            }

            full_data_path = full_data_path.replace('//', '/');
            full_json_path = full_json_path.replace('//', '/');
            if (full_aux_path) full_aux_path = full_aux_path.replace('//', '/');

            let added_data = false, added_json = false, added_aux = false;

            if (!zip_url_listing[cur_zip_idx].includes(this_data_url)) {
                zip_url_listing[cur_zip_idx].push(this_data_url);
                zip_path_listing[cur_zip_idx].push(full_data_path);
                added_data = true;
            }
            if (!zip_url_listing[cur_zip_idx].includes(this_json_url)) {
                zip_url_listing[cur_zip_idx].push(this_json_url);
                zip_path_listing[cur_zip_idx].push(full_json_path);
                added_json = true;
            }
            if (!isNaN(window.file_sizes[this_aux_url])) {
                if (!zip_url_listing[cur_zip_idx].includes(this_aux_url)) {
                    zip_url_listing[cur_zip_idx].push(this_aux_url);
                    zip_path_listing[cur_zip_idx].push(full_aux_path);
                    added_aux = true;
                }
            }

            if (added_data && !isNaN(window.file_sizes[this_data_url])) {
                console.debug('Adding', Detail.humanFileSize(window.file_sizes[this_data_url]), 'file:', full_data_path, 'to zip #:', cur_zip_idx);
                this_zip_size += window.file_sizes[this_data_url];
            }
            if (added_json && !isNaN(window.file_sizes[this_json_url])) {
                console.debug('Adding', Detail.humanFileSize(window.file_sizes[this_json_url]), 'file:', full_json_path, 'to zip #:', cur_zip_idx);
                this_zip_size += window.file_sizes[this_json_url];
            }
            if (added_aux && !isNaN(window.file_sizes[this_aux_url])) {
                console.debug('Adding', Detail.humanFileSize(window.file_sizes[this_aux_url]), 'file:', full_aux_path, 'to zip #:', cur_zip_idx);
                this_zip_size += window.file_sizes[this_aux_url];
            }
        }

        console.debug('this_zip_size is', Detail.humanFileSize(this_zip_size));
        zip_total_sizes.push(this_zip_size);

        var msg = '';
        if (zips.length > 1) {
            msg = 'Due to limitations of the .zip format, your ' + window.human_dl_size +
                ' download will be split into ' + zips.length +
                ' .zip files (each a maximum of ' +
                Detail.humanFileSize(size_limit) + ' in size). ' +
                'You can extract them all to the same folder to view all your data at once. \n';
            showExtraMessage(msg, 'warning');
        }

        var promList = [];
        var filesArr = [];
        for (var i = 0; i < zip_url_listing.length; i += 1) {
            filesArr.push([]);
            for (var j = 0; j < zip_url_listing[i].length; j += 1) {
                filesArr[i].push([zip_path_listing[i][j], zip_url_listing[i][j]]);
            }
        }
        var filesIters = filesArr.map(f => f.values());

        var bytesDownloaded = 0;
        const TransformStream = window.TransformStream || ponyfill.TransformStream;

        console.debug(`${zips.length} zips to download; ${individual_files.length} individual files to download`);

        var progressArr = [];
        for (var i = 0; i < zips.length; i++) {
            let p = new TransformStream({
                transform(chunk, ctrl) {
                    bytesDownloaded += chunk.byteLength;
                    updateProgressBar(bytesDownloaded, Detail.arrSum(zip_total_sizes) + Detail.arrSum(indiv_dl_sizes));
                    ctrl.enqueue(chunk);
                }
            });
            progressArr.push(p);
        }

        for (var i = 0; i < individual_files.length; i++) {
            let p = new TransformStream({
                transform(chunk, ctrl) {
                    bytesDownloaded += chunk.byteLength;
                    console.debug(`Downloaded ${Detail.humanFileSize(bytesDownloaded)} of the individual file data`);
                    updateProgressBar(bytesDownloaded, Detail.arrSum(zip_total_sizes) + Detail.arrSum(indiv_dl_sizes));
                    ctrl.enqueue(chunk);
                }
            });
            progressArr.push(p);
        }

        var fileStreamArr = [];
        var readableStreamArr = [];
        var abortController = new AbortController();
        var abortSignal = abortController.signal;
        var dlError = false;

        for (var i = 0; i < zips.length; i++) {
            let this_zip_title = (zips.length === 1) ? zip_title :
                zip_title.replace('.zip', '-' + (i + 1) + 'of' + zips.length + '.zip');

            console.info(`Creating writeStream with name ${this_zip_title}`);
            let ws = streamSaver.createWriteStream(this_zip_title, { size: zip_total_sizes[i] });
            fileStreamArr.push(ws);

            let files = filesIters[i];
            let z = new JSZip({
                pull(ctrl) {
                    const it = files.next();
                    if (it.done) {
                        ctrl.close();
                    } else {
                        const [name, url] = it.value;
                        return fetch(url, { signal: abortSignal })
                            .then(res => {
                                ctrl.enqueue({
                                    name,
                                    stream: () => {
                                        let r = res.body;
                                        readableStreamArr.push(r);
                                        return r;
                                    }
                                });
                            });
                    }
                }
            }).pipeThrough(progressArr[i])
                .pipeTo(fileStreamArr[i], { signal: abortSignal })
                .catch(err => {
                    if (!abortSignal.aborted) {
                        console.error(err);
                        dlError = true;
                        showError('There was an error during the download: ' + err.message);
                    }
                });
            promList.push(z);
        }

        if (individual_files.length > 0) {
            if (msg.length > 0) msg += '\n';
            msg += 'Because their individual size is larger than can be included in a .zip file, the following files (and their metadata) will not be included in the .zip and instead downloaded individually: \n';
            for (let f of individual_files) {
                if (!f.endsWith('.json')) {
                    msg += '    - ' + decodeURIComponent(f.replace(/.*\//g, "")) + '\n';
                }
            }
            showExtraMessage(msg, 'warning');
        }

        let toPonyRS = WebStreamsAdapter.createReadableStreamWrapper(ponyfill.ReadableStream);
        individual_files = [...new Set(individual_files)];

        const files_in_zips = new Set();
        for (let zip_urls of zip_url_listing) {
            for (let url of zip_urls) {
                files_in_zips.add(url);
            }
        }
        individual_files = individual_files.filter(url => !files_in_zips.has(url));

        for (var i = 0; i < individual_files.length; i++) {
            let url = individual_files[i];
            let filename = decodeURIComponent(url.replace(/.*\//g, ""));
            console.warn(`Writing to ${filename}`);
            let fileStream = streamSaver.createWriteStream(filename, { size: window.file_sizes[url] });
            let writer = fileStream.getWriter();
            console.warn("ran getWriter()");
            writer.releaseLock();
            let this_prog = progressArr[i + zips.length];
            let p = fetch(url, { signal: abortSignal })
                .then(res => {
                    let rs = res.body;
                    rs = window.ReadableStream.prototype.pipeTo ? rs : toPonyRS(rs);
                    readableStreamArr.push(rs);
                    return rs.pipeThrough(this_prog)
                        .pipeTo(fileStream, { signal: abortSignal })
                        .catch(err => {
                            if (!abortSignal.aborted) {
                                dlError = true;
                                showError('There was an error during the download: ' + err.message);
                            }
                        });
                });
            promList.push(p);
            fileStreamArr.push(fileStream);
        }

        $(window).bind('beforeunload', function() {
            return 'The download has not finished, are you sure you want to leave the page?';
        });

        const cancel_downloads = function() {
            abortController.abort();
        };

        window.onunload = cancel_downloads;
        $('#btn-cancel-dl').click(cancel_downloads);

        Promise.all(promList).then(function() {
            if (abortSignal.aborted) {
                showMessage("Download canceled by user (any already completed downloads were saved)", 'warning');
            } else if (dlError) {
                errorProgress();
            } else {
                finishProgress();
                showMessage("Finished downloading all files!", 'success');
            }
            hideExtraMessage();
            $(window).unbind('beforeunload');
            $('#btn-cancel-row').slideUp();
            $('#progressbar-row').slideUp();
            $('button.dl-btns').removeClass('disabled');
            if (window.filelist_dt) window.filelist_dt.select.style('multi');
        });
    };

    // ============================================================================
    // XML Download
    // ============================================================================

    const prepDownloadXML = async function() {
        if (window.location.href.includes('/pid/')) {
            try {
                let response = await fetch(window.location.href, { headers: { 'Accept': 'application/json' } });
                let res = await response.json();
                return res.id;
            } catch (err) {
                alert(`There was an error trying to download the record XML: ${err}`);
                console.error(err);
            }
        } else {
            let id = new URLSearchParams(window.location.search).get('id');
            return Promise.resolve(id);
        }
    };

    Detail.downloadXML = function() {
        let id = prepDownloadXML();
        id.then(i => {
            let xml_url = `/rest/data/download/${i}/`;
            fetch(xml_url)
                .then(resp => resp.text())
                .then(text => new Blob([Detail.formatXml(text)], { type: 'text/xml' }))
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = $('#xmlName').text();
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                });
        });
    };

})(jQuery, streamSaver, JSZip, window);
