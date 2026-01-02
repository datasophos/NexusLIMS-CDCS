/**
 * NexusLIMS Detail Page - Guided Tour
 *
 * Shepherd.js tutorial system for guiding users through the detail page features
 */

(function($, Shepherd, window) {
    'use strict';

    var Detail = window.NexusLIMSDetail;

    Detail.create_detail_tour = function() {

        // Check if any modals are visible, close them and remember to reopen at the end
        var already_open_modal = false;
        $('.modal').each(function(index, val) {
            if ($(val).css('visibility') === 'visible') {
                Detail.closeModal(val.id);
                already_open_modal = val.id;
            }
        });

        var topScrollHandler = function(element, offset) {
            if (!offset) {
                offset = 75;
            }
            if (element) {
                var $element = $(element);
                var topOfElement = $element.offset().top;
                var heightOfElement = $element.height() + offset;
                $('html, body').animate({
                    scrollTop: topOfElement - heightOfElement
                }, {
                    duration: 500
                });
            }
        };

        var detail_tour = new Shepherd.Tour({
            useModalOverlay: true,
            keyboardNavigation: false,
            defaultStepOptions: {
                when: {
                    show() {
                        showStepNumber()
                    }
                },
                modalOverlayOpeningPadding: 25,
                scrollTo: true,
                scrollToHandler: topScrollHandler,
                canClickTarget: false,
            }
        });

        var showStepNumber = () => {
            $("<span style='font-size: small'></span>")
                .insertBefore('.shepherd-footer .btn-primary')
                .html(`${detail_tour.steps.indexOf(detail_tour.currentStep) + 1}/${detail_tour.steps.length}`);
        };

        var end_button = {
            text: 'End',
            classes: 'btn btn-danger',
            action: detail_tour.next,
            label: 'End'
        };

        var next_button = {
            text: 'Next <i class="fa fa-arrow-right menu-fa"></i>',
            classes: 'btn btn-primary',
            action: detail_tour.next,
            label: 'Next'
        };

        var back_button = (enabled) => {
            return {
                text: '<i class="fa fa-arrow-left menu-fa"></i> Back',
                classes: 'btn btn-default',
                disabled: (!enabled),
                action: detail_tour.back,
                label: 'Back'
            };
        };

        // Add tour steps
        detail_tour.addStep({
            id: 'tut-welcome',
            title: 'This is the record detail page',
            text: 'The <em>detail</em> page shows all the details of a record generated from an Experiment on one of the Nexus Facility instruments. Click <em>Next</em> for a tour of the features of this record. You can also use the keyboard arrow keys to navigate through the tutorial.',
            buttons: [back_button(false), next_button],
        });

        detail_tour.addStep({
            id: 'tut-record-header',
            title: 'The record header',
            text: 'The top of the record contains basic information, such as the title of the experiment (taken from the calendar reservation), the instrument that was used, the number and types of files contained within, the user, date, and experimental motivation. This utility of this section relies heavily on the quality of data inputted into the reservation form.',
            attachTo: { element: '#record-header', on: 'bottom' },
            buttons: [back_button(true), next_button],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        detail_tour.addStep({
            id: 'tut-session_info_column',
            title: 'Session summary information',
            text: 'The session summary section contains further details about the experiment, such as the precise date and time (from the calendar), the sample information and ID, and any sample description.',
            attachTo: { element: '#session_info_column', on: 'bottom' },
            scrollTo: false,
            buttons: [back_button(true), next_button],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        detail_tour.addStep({
            id: 'tut-img_gallery',
            title: 'Image gallery',
            text: "The gallery shows a preview image of each dataset contained within the experiment's record. These can be browsed using the mouse buttons, or via the left and right arrow keys on the keyboard.",
            attachTo: { element: '#img_gallery', on: 'left' },
            scrollTo: false,
            buttons: [back_button(true), next_button],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        if ($('#simpleDisplay').text() == 'false') {
            detail_tour.addStep({
                id: 'tut-aa',
                title: 'Acquisition activities',
                text: 'The remainder of the record contains details about the various "activities" that were detected in the records (determined via file creation times). Click <em>Next</em> for further details about the contents of each activity.',
                attachTo: { element: $('.aa_header_row')[0], on: 'left' },
                buttons: [back_button(true), next_button],
                scrollToHandler: (element) => { topScrollHandler(element, -1 * $(element).height() + 75) },
            });

            detail_tour.addStep({
                id: 'tut-setup-params',
                title: 'Setup parameters',
                text: 'The setup parameters button will show you the metadata extracted from the raw files that is common to all the datasets contained in this activity. Clicking here will open a dialog box showing the setup parameters for this activity',
                attachTo: { element: $('.aa_header_row .param-button')[0], on: 'bottom' },
                buttons: [back_button(true), next_button],
                scrollTo: false,
                canClickTarget: false,
                modalOverlayOpeningPadding: 15,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 15] } }]
                }
            });

            detail_tour.addStep({
                id: 'tut-aa-gallery',
                title: 'Activity image gallery',
                text: "Another preview of the datasets in this activity is shown here. Mouse over a dataset in the accompanying table to view its preview",
                attachTo: { element: $('.aa_header_row .aa-img-col')[0], on: 'bottom' },
                scrollTo: false,
                buttons: [back_button(true), next_button]
            });

            detail_tour.addStep({
                id: 'tut-aa-table',
                title: 'Activity dataset table',
                text: "The activity details table lists each dataset contained in this activty with some basic information such as the dataset's name, its creation time, the type of data contained, and its role.",
                attachTo: { element: $('.aa_header_row .aa-table-col')[0], on: 'bottom' },
                scrollTo: false,
                buttons: [back_button(true), next_button]
            });

            detail_tour.addStep({
                id: 'tut-aa-meta',
                title: 'Metadata viewer/downloader',
                text: "The metadata column allows you to view the metadata unique to this dataset using the left button, or you can download the entire extracted metadata using the button on the right in JSON format.",
                attachTo: { element: $('.aa_header_row .aa-table-col .aa-meta-col')[0], on: 'left' },
                buttons: [back_button(true), next_button],
                scrollTo: false,
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });

            detail_tour.addStep({
                id: 'tut-aa-dl',
                title: 'Individual file downloader',
                text: "The final column provides a link to download this single file in its native format (Note: there is a bulk file downloader at the top of the record)",
                attachTo: { element: $('.aa_header_row .aa-table-col .aa-dl-col')[0], on: 'left' },
                buttons: [back_button(true), next_button],
                scrollTo: false,
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        }

        if ($('#simpleDisplay').text() == 'false') {
            var sidebar_vis = $('.sidebar').position()['left'] === 0;
            var sidebar_text = "The sidebar provides an easy way to navigate through the different activities in the record, and also provides a button to return to the top of the page.";
            if (!sidebar_vis) {
                sidebar_text += " If the window is too narrow, the sidebar is hidden from view. Clicking this button will show it.";
            }

            detail_tour.addStep({
                id: 'tut-sidebar',
                title: 'Record navigation sidebar',
                text: sidebar_text,
                attachTo: {
                    element: sidebar_vis ? $('.sidebar')[0] : $('#btn-sidebar')[0],
                    on: 'right'
                },
                scrollTo: false,
                buttons: [back_button(true), next_button]
            });

            detail_tour.addStep({
                id: 'tut-filelisting',
                title: 'Record file listing and downloader',
                text: "The <i class='fa fa-cloud-download menu-fa'></i> <em>Download files</em> button provides an overview of all the dataset files in this record, and provides a means to download all (or a selected number of) files as a .zip archive. This dialogue also allows you to export a list of files into a variety of formats.",
                attachTo: { element: '#btn-filelisting', on: 'bottom' },
                scrollTo: true,
                buttons: [back_button(true), next_button],
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        }

        detail_tour.addStep({
            id: 'tut-xml-dl',
            title: 'Record exporter',
            text: "The <i class='fa fa-code menu-fa'></i> <em>Download XML</em> button will download the metadata record (not the actual datafiles) in an structured format for additional analysis, if desired.",
            attachTo: { element: '#btn-xml-dl', on: 'bottom' },
            scrollTo: true,
            buttons: [back_button(true), next_button],
            modalOverlayOpeningPadding: 5,
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
            }
        });

        detail_tour.addStep({
            id: 'tut-edit-record',
            title: 'Record editor',
            text: "The <i class='fa fa-file-text menu-fa'></i> <em>Edit this record</em> button will allow you (if logged in and you have ownership of this record) to edit the metadata information contained within. Currently, this process is a bit cumbersome, but an improvement to the interface is on the NexusLIMS team's roadmap.",
            attachTo: { element: '#btn-edit-record', on: 'bottom' },
            scrollTo: false,
            buttons: [back_button(true), end_button],
            modalOverlayOpeningPadding: 5,
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
            }
        });

        let cur_pos = $(document).scrollTop();

        function clean_up_on_exit(modal_to_open) {
            if ($(document).scrollTop() === cur_pos) {
                if (modal_to_open) { Detail.openModal(modal_to_open) }
            } else {
                $('html, body').animate({
                    scrollTop: cur_pos
                }, {
                    duration: 500,
                    complete: modal_to_open ? () => { Detail.openModal(modal_to_open) } : null
                });
            }
        }

        detail_tour.on('complete', () => clean_up_on_exit(already_open_modal));
        detail_tour.on('cancel', () => clean_up_on_exit(already_open_modal));
        detail_tour.on('hide', () => clean_up_on_exit(already_open_modal));

        $('.shepherd-modal-overlay-container').on('click', () => detail_tour.cancel());
        detail_tour.start();
    };

})(jQuery, Shepherd, window);
