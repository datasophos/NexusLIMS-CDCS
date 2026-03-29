/**
 * NexusLIMS Tours - Consolidated Tutorial System
 *
 * Shepherd.js guided tours for NexusLIMS pages.
 * Controlled by NX_ENABLE_TUTORIALS Django setting.
 *
 * Tours available:
 * - Homepage tour: Introduction to NexusLIMS
 * - Explore page tour: Guide through record browsing and search
 * - Detail page tour: Guide through record detail features
 */

(function($, window) {
    'use strict';

    // Create namespace
    window.NexusLIMSTours = window.NexusLIMSTours || {};

    // ========================================================================
    // Configuration
    // ========================================================================

    /**
     * Check if tutorials are enabled via Django setting
     * The setting is passed via data attribute on the page-wrapper element
     */
    function tutorialsEnabled() {
        var enabled = $('#page-wrapper').data('tutorials-enabled');
        // If not set, default to true
        return enabled !== false && enabled !== 'false';
    }

    /**
     * Check if Shepherd.js is available
     */
    function shepherdAvailable() {
        return typeof Shepherd !== 'undefined' && typeof Shepherd.Tour === 'function';
    }

    // ========================================================================
    // Common Tour Utilities
    // ========================================================================

    /**
     * Standard scroll handler for tour steps
     */
    function topScrollHandler(element, offset) {
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
    }

    /**
     * Scroll navPanel to make element visible
     * This is used for mobile view when highlighting elements in the navPanel
     */
    function scrollNavPanelToElement(element) {
        if (!element || !$('#navPanel').length) {
            return Promise.resolve();
        }

        var $navPanel = $('#navPanel');
        var $element = $(element);

        // Check if element is within navPanel
        if (!$element.closest('#navPanel').length) {
            return Promise.resolve();
        }

        // Get positions relative to navPanel
        var navPanelTop = $navPanel.offset().top;
        var navPanelHeight = $navPanel.height();
        var elementTop = $element.offset().top;
        var elementHeight = $element.height();

        // Calculate if element is visible in navPanel
        var elementTopRelativeToNavPanel = elementTop - navPanelTop;
        var elementBottomRelativeToNavPanel = elementTopRelativeToNavPanel + elementHeight;

        // If element is below visible area, scroll to make it visible
        if (elementBottomRelativeToNavPanel > navPanelHeight) {
            var scrollPosition = elementBottomRelativeToNavPanel - navPanelHeight + 20; // +20 for padding

            return new Promise(function(resolve) {
                $navPanel.animate({
                    scrollTop: scrollPosition
                }, {
                    duration: 300,
                    complete: resolve
                });
            });
        }

        return Promise.resolve();
    }

    /**
     * Create step number indicator for tour footer
     * This is called on each step 'show' event to insert the step counter
     * Uses setTimeout to ensure DOM is ready after step renders
     */
    function createStepNumberIndicator(tour) {
        return function() {
            setTimeout(function() {
                // Remove any existing step indicator first
                $('.shepherd-step-number').remove();
                // Insert new step indicator before the last button (Next or End)
                var stepNum = tour.steps.indexOf(tour.currentStep) + 1;
                var totalSteps = tour.steps.length;
                var lastButton = $('.shepherd-footer button:last');
                if (lastButton.length > 0) {
                    $("<span class='shepherd-step-number' style='font-size: small'>" + stepNum + "/" + totalSteps + "</span>")
                        .insertBefore(lastButton);
                }
            }, 0);
        };
    }

    /**
     * Create standard tour buttons
     */
    function createButtons(tour) {
        return {
            end: {
                text: 'End',
                classes: 'btn btn-danger',
                action: tour.next,
                label: 'End'
            },
            next: {
                text: 'Next <i class="fa fa-arrow-right menu-fa"></i>',
                classes: 'btn btn-primary',
                action: tour.next,
                label: 'Next'
            },
            back: function(enabled) {
                return {
                    text: '<i class="fa fa-arrow-left menu-fa"></i> Back',
                    classes: 'btn btn-default',
                    disabled: !enabled,
                    action: tour.back,
                    label: 'Back'
                };
            }
        };
    }

    // ========================================================================
    // Homepage Tour
    // ========================================================================

    /**
     * Check if we're in mobile view (navPanel visible instead of #nav)
     * The breakpoint is 991px (Bootstrap lg - 1)
     */
    function isMobileView() {
        return window.innerWidth <= 991;
    }

    // MutationObserver to keep navPanel open during tour
    var navPanelObserver = null;

    /**
     * Start observing body class changes to keep navPanel open during tour
     */
    function startNavPanelObserver() {
        if (navPanelObserver) return; // Already observing

        navPanelObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') {
                    var body = document.body;
                    // If tour wants panel open but it was closed, re-open it
                    if (body.classList.contains('tour-navpanel-open') &&
                        !body.classList.contains('navPanel-visible')) {
                        body.classList.add('navPanel-visible');
                    }
                }
            });
        });

        navPanelObserver.observe(document.body, { attributes: true });
    }

    /**
     * Stop observing body class changes
     */
    function stopNavPanelObserver() {
        if (navPanelObserver) {
            navPanelObserver.disconnect();
            navPanelObserver = null;
        }
    }

    /**
     * Open the mobile navigation panel and keep it open during the tour
     * by using a MutationObserver to re-add the class if removed
     */
    function openNavPanel() {
        // Start observer to keep panel open
        startNavPanelObserver();

        // Add class to indicate tour wants panel open
        $('body').addClass('tour-navpanel-open');

        if (!$('body').hasClass('navPanel-visible')) {
            $('body').addClass('navPanel-visible');
        }

        // Return a promise that resolves after animation
        return new Promise(function(resolve) {
            setTimeout(resolve, 350);
        });
    }

    /**
     * Close the mobile navigation panel and stop observer
     */
    function closeNavPanel() {
        stopNavPanelObserver();
        $('body').removeClass('navPanel-visible tour-navpanel-open');
    }

    /**
     * Keep the navPanel open - used to maintain state between tour steps
     */
    function keepNavPanelOpen() {
        if ($('body').hasClass('tour-navpanel-open') && !$('body').hasClass('navPanel-visible')) {
            $('body').addClass('navPanel-visible');
        }
        return Promise.resolve();
    }

    function createHomepageTour() {
        if (!shepherdAvailable()) {
            console.warn('Shepherd.js not available for homepage tour');
            return null;
        }

        // Close navPanel if open when tour starts (mobile)
        if ($('body').hasClass('navPanel-visible')) {
            $('body').removeClass('navPanel-visible');
        }

        var Detail = window.NexusLIMSDetail;

        if (!Detail) {
            console.warn('NexusLIMSDetail namespace not available');
            return null;
        }

        // Close sidebar if open when tour starts
        if (Detail && Detail.closeSidebar && $('.sidebar').hasClass('side-expanded')) {
            Detail.closeSidebar();
        }

        var tour = new Shepherd.Tour({
            useModalOverlay: true,
            keyboardNavigation: true,
            defaultStepOptions: {
                modalOverlayOpeningPadding: 15,
                scrollTo: true,
                scrollToHandler: topScrollHandler,
                canClickTarget: false,
                popperOptions: {
                    modifiers: [
                        { name: 'offset', options: { offset: [0, 15] } },
                        { name: 'arrow', options: { padding: 5 } }
                    ]
                }
            }
        });

        // Add step number indicator after tour is created
        tour.on('show', createStepNumberIndicator(tour));

        var buttons = createButtons(tour);

        // Capture scroll position at start of tour for restoration later
        var cur_pos = $(document).scrollTop();

        // Check viewport at tour creation time
        var mobile = isMobileView();

        tour.addStep({
            id: 'welcome',
            title: 'Welcome to NexusLIMS!',
            text: 'This tutorial will guide you through the main features of NexusLIMS. Use the arrow keys or click the buttons to navigate.',
            buttons: [buttons.back(false), buttons.next]
        });

        if (mobile) {
            // Mobile-specific steps
            tour.addStep({
                id: 'mobile-menu-toggle',
                title: 'Navigation Menu',
                text: 'On smaller screens, the navigation is accessed through this menu button. Let\'s open it to explore the menu options.',
                attachTo: {
                    element: '#titleBar .toggle',
                    on: 'bottom'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'browse-link',
                title: 'Browse Records',
                text: 'Click here to browse and search all experimental records in the system. You can filter by keywords, instruments, dates, and more.',
                beforeShowPromise: function() {
                    return openNavPanel().then(function() {
                        // Find the browse link and scroll to it if needed
                        var browseLink = $('#navPanel a[href*="explore/keyword"]')[0];
                        return scrollNavPanelToElement(browseLink);
                    });
                },
                attachTo: {
                    element: '#navPanel a[href*="explore/keyword"]',
                    on: 'right'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-tutorial',
                title: 'Context-aware Tutorials',
                text: 'This link runs <em>this</em> tutorial, but will load a customized introduction on the other pages within the application. If you are uncertain about a certain page\'s content, click this link to take a guided tour.',
                beforeShowPromise: function() {
                    return keepNavPanelOpen().then(function() {
                        // Find the Tutorial link in navPanel
                        var tutorialLink = $('#navPanel .link').filter(function() {
                            return $(this).text().trim() === 'Tutorial';
                        })[0];

                        // Scroll navPanel to make the element visible
                        return scrollNavPanelToElement(tutorialLink);
                    });
                },
                attachTo: {
                    element: function() {
                        // Find the Tutorial link in navPanel
                        return $('#navPanel .link').filter(function() {
                            return $(this).text().trim() === 'Tutorial';
                        })[0];
                    },
                    on: 'right'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-help-links',
                title: 'Help Resources',
                text: 'The Help section contains links to documentation and API references.',
                beforeShowPromise: function() {
                    return keepNavPanelOpen().then(function() {
                        // Find the last documentation link in navPanel
                        var helpLink = $('#navPanel .link').last();

                        // Scroll navPanel to make the element visible
                        return scrollNavPanelToElement(helpLink);
                    });
                },
                attachTo: {
                    element: function() {
                        // Find the Documentation link in navPanel (it's nested under Help)
                        return $('#navPanel .link').filter(function() {
                            return $(this).text().trim().indexOf('Documentation') !== -1 &&
                                   $(this).text().trim().indexOf('API') === -1;
                        })[0];
                    },
                    on: 'right'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-browse-records-tile',
                title: 'Browse Records',
                text: 'You can also access the record browser through the link on the homepage',
                beforeShowPromise: function() {
                    closeNavPanel();
                    return Promise.resolve();
                },
                attachTo: {
                    element: '#app_search',
                    on: 'top'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'get-started',
                title: 'Get Started!',
                text: 'That\'s it! Click the "Browse and Search Records" link to explore experimental data, or close this tutorial to continue exploring the homepage.',
                buttons: [buttons.back(true), buttons.end]
            });
        } else {
            // Desktop-specific steps
            tour.addStep({
                id: 'browse-link',
                title: 'Browse Records',
                text: 'Click here to browse and search all experimental records in the system. You can filter by keywords, instruments, dates, and more.',
                attachTo: {
                    element: '#nav a[href*="explore/keyword"]',
                    on: 'bottom'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-browse-records-tile',
                title: 'Browse Records',
                text: 'You can also access the record browser through the link below',
                attachTo: {
                    element: '#app_search',
                    on: 'top'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-tutorial',
                title: 'Context-aware Tutorials',
                text: 'This link runs <em>this</em> tutorial, but will load a customized introduction on the other pages within the application. If you are uncertain about a certain page\'s content, click this link to take a guided tour.',
                attachTo: {
                    element: '#menu-tutorial',
                    on: 'bottom'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-help',
                title: 'Help Menu',
                text: 'Click here to open the help menu, which contains additional resources',
                attachTo: {
                    element: '#dropdownHelp',
                    on: 'bottom'
                },
                buttons: [buttons.back(true), buttons.next]
            });

            // Helper function to open/close Help dropdown using Bootstrap API
            function openHelpDropdown() {
                var dropdownEl = document.getElementById('dropdownHelp');
                if (dropdownEl) {
                    var dropdown = bootstrap.Dropdown.getOrCreateInstance(dropdownEl);
                    dropdown.show();
                }
            }

            function closeHelpDropdown() {
                var dropdownEl = document.getElementById('dropdownHelp');
                if (dropdownEl) {
                    var dropdown = bootstrap.Dropdown.getInstance(dropdownEl);
                    if (dropdown) {
                        dropdown.hide();
                    }
                }
            }

            tour.addStep({
                id: 'tut-nx-doc',
                title: 'Detailed Documentation',
                text: 'Click here to be brought to the NexusLIMS documentation page, which contains detailed information about how experiment information is collected, how records are created, etc.',
                beforeShowPromise: () => {
                    openHelpDropdown();
                    return Promise.resolve();
                },
                attachTo: {
                    element: $('#dropdownHelp + ul.dropdown-menu > li > a:contains("Documentation")')[0],
                    on: 'left'
                },
                canClickTarget: false,
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-api-doc',
                title: 'API Documentation',
                text: 'Click here to be brought to the NexusLIMS CDCS API documentation page, which describes how to programmatically access the information in the NexusLIMS database',
                attachTo: {
                    element: $('#dropdownHelp + ul.dropdown-menu > li > a:contains("API Documentation")')[0],
                    on: 'left'
                },
                canClickTarget: false,
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'get-started',
                title: 'Get Started!',
                text: 'That\'s it! Click the "Browse and Search Records" link to explore experimental data, or close this tutorial to continue exploring the homepage.',
                beforeShowPromise: () => {
                    closeHelpDropdown();
                    return Promise.resolve();
                },
                buttons: [buttons.back(true), buttons.end]
            });

            // Cleanup: close dropdown when tour ends (desktop only)
            tour.on('complete', closeHelpDropdown);
            tour.on('cancel', closeHelpDropdown);
        }

        // Cleanup: close navPanel when tour ends (mobile)
        if (mobile) {
            tour.on('complete', closeNavPanel);
            tour.on('cancel', closeNavPanel);
        }

        // Cleanup on exit - scroll back to starting position and blur tutorial link
        var cleanupOnExit = function() {
            // Shepherd only removes the modal overlay from the DOM on `complete`, not on
            // `cancel`. The overlay's SVG path keeps pointer-events:all while
            // shepherd-modal-is-visible is set, blocking scroll and clicks after cancel.
            var overlay = document.querySelector('.shepherd-modal-overlay-container');
            if (overlay) { overlay.remove(); }

            // Remove focus outline from tutorial link
            $('#menu-tutorial, nav a, #navPanel a').filter(function() {
                return $(this).text().trim() === 'Tutorial';
            }).addClass('tour-completed');

            if ($(document).scrollTop() !== cur_pos) {
                $('html, body').animate({ scrollTop: cur_pos }, { duration: 500 });
            }
        };

        tour.on('complete', cleanupOnExit);
        tour.on('cancel', cleanupOnExit);

        // Allow clicking overlay to cancel
        tour.on('show', function() {
            setTimeout(function() {
                $('.shepherd-modal-overlay-container').on('click', function() {
                    tour.cancel();
                });
            }, 100);
        });

        return tour;
    }

    // ========================================================================
    // Explore Page Tour
    // ========================================================================

    function createExploreTour() {
        if (!shepherdAvailable()) {
            console.warn('Shepherd.js not available for explore tour');
            return null;
        }

        // Close navPanel if open when tour starts (mobile)
        if ($('body').hasClass('navPanel-visible')) {
            $('body').removeClass('navPanel-visible');
        }

        var tour = new Shepherd.Tour({
            useModalOverlay: true,
            keyboardNavigation: true,
            defaultStepOptions: {
                modalOverlayOpeningPadding: 15,
                scrollTo: true,
                scrollToHandler: topScrollHandler,
                canClickTarget: false,
                popperOptions: {
                    modifiers: [
                        { name: 'offset', options: { offset: [0, 15] } },
                        { name: 'arrow', options: { padding: 5 } }
                    ]
                }
            }
        });

        // Add step number indicator after tour is created
        tour.on('show', createStepNumberIndicator(tour));

        var buttons = createButtons(tour);

        // Welcome step
        tour.addStep({
            id: 'tut-welcome',
            title: 'This is the record explorer page',
            text: 'The <em>explore</em> page allows you to browse and search through the records contained in the NexusLIMS repository. Click <em>Next</em> for a brief tour of the features of this page. You can also use the keyboard arrow keys to navigate through the tutorial.',
            buttons: [buttons.back(false), buttons.next]
        });

        // Search bar step
        tour.addStep({
            id: 'tut-search-field',
            title: 'The search bar',
            text: 'Use the search box to do a full-text search on all the records (can search by username, date, instrument, etc.). Leave the box empty to return all results from the database.',
            attachTo: {
                element: '#search-field',
                on: 'bottom'
            },
            buttons: [buttons.back(true), buttons.next]
        });

        // Example record step - only if records exist
        if ($('.a-result').length > 0) {
            tour.addStep({
                id: 'tut-example-record',
                title: 'An example record listing',
                text: 'Each listing in the results area represents one record in the database and provides some basic summary information about the record\'s contents. Click anywhere on the listing to view the record details.',
                attachTo: {
                    element: $('.a-result').first()[0],
                    on: 'bottom'
                },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next]
            });
        }

        // Instrument badge filter step - only if badges exist
        if ($('.instrument-badge-clickable').length > 0) {
            tour.addStep({
                id: 'tut-instrument-badge',
                title: 'Filter by Instrument',
                text: 'Click on an instrument badge to quickly filter results by that specific instrument. The badge will add a filter tag to the search bar and automatically refresh the results.',
                attachTo: {
                    element: $('.instrument-badge-clickable').first()[0],
                    on: 'bottom'
                },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 10,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        }

        // Sorting button step
        var sortButton = $('[id^="result-button-filter"]').first();
        if (sortButton.length > 0) {
            tour.addStep({
                id: 'tut-result-button-filter',
                title: 'Record sorting',
                text: 'By default, the records are sorted with the most recently added records first. Use this sort button to change the sorting order.',
                attachTo: {
                    element: sortButton[0],
                    on: 'bottom'
                },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 10,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        }

        // Share query step
        tour.addStep({
            id: 'tut-share-query',
            title: 'Sharing Queries',
            text: 'You can get a persistent link to a particular set of search results (e.g., to share with colleagues) by clicking this button.',
            attachTo: {
                element: '#persistent-query',
                on: 'bottom'
            },
            buttons: [buttons.back(true), buttons.next]
        });

        // Export step
        tour.addStep({
            id: 'tut-export-record',
            title: 'Exporting Records',
            text: 'If you wish to download one (or more) records as JSON or XML, you can select each record\'s checkbox and then click this Download button to save the records to your computer.',
            attachTo: {
                element: '.export-button',
                on: 'bottom'
            },
            buttons: [buttons.back(true), buttons.end]
        });

        // Pagination step - only if pagination exists
        if ($('.pagination-container').length > 0) {
            tour.addStep({
                id: 'tut-pagination-container',
                title: 'Browsing many records',
                text: 'If your search returns more items than fit on one page, use the paging controls at the bottom to browse through the records.',
                attachTo: {
                    element: '.pagination-container',
                    on: 'top'
                },
                buttons: [buttons.back(true), buttons.end]
            });
        } else {
            // Change the last step's next button to end
            var steps = tour.steps;
            if (steps.length > 0) {
                var lastStep = steps[steps.length - 1];
                lastStep.options.buttons = [buttons.back(true), buttons.end];
            }
        }

        // Cleanup on exit - scroll back to starting position and blur tutorial link
        var cur_pos = $(document).scrollTop();
        var cleanupOnExit = function() {
            // Shepherd only removes the modal overlay from the DOM on `complete`, not on
            // `cancel`. The overlay's SVG path keeps pointer-events:all while
            // shepherd-modal-is-visible is set, blocking scroll and clicks after cancel.
            var overlay = document.querySelector('.shepherd-modal-overlay-container');
            if (overlay) { overlay.remove(); }

            // Remove focus outline from tutorial link
            $('#menu-tutorial, nav a, #navPanel a').filter(function() {
                return $(this).text().trim() === 'Tutorial';
            }).addClass('tour-completed');

            if ($(document).scrollTop() !== cur_pos) {
                $('html, body').animate({ scrollTop: cur_pos }, { duration: 500 });
            }
        };

        tour.on('complete', cleanupOnExit);
        tour.on('cancel', cleanupOnExit);

        // Allow clicking overlay to cancel
        tour.on('show', function() {
            setTimeout(function() {
                $('.shepherd-modal-overlay-container').on('click', function() {
                    tour.cancel();
                });
            }, 100);
        });

        return tour;
    }

    // ========================================================================
    // Detail Page Tour
    // ========================================================================

    function createDetailTour() {
        if (!shepherdAvailable()) {
            console.warn('Shepherd.js not available for detail tour');
            return null;
        }

        // Get reference to Detail namespace for modal functions
        var Detail = window.NexusLIMSDetail;
        if (!Detail) {
            console.warn('NexusLIMSDetail namespace not available');
            return null;
        }

        // Check if any modals are visible, close them and remember to reopen at the end
        var already_open_modal = false;
        $('.modal').each(function(index, val) {
            var vis = $(val).css('visibility');
            var disp = $(val).css('display');
            if (vis === 'visible' && disp !== 'none' &&
                (val.id !== 'download-modal' && val.id !== 'file-preview-modal')) {
                Detail.closeModal(val.id);
                already_open_modal = val.id;
            }
        });

        // Disable scrolling during the tour (matches the page's existing scroll management)
        $('body').addClass('scrollDisabled');

        // Close navPanel if open when tour starts (mobile)
        if ($('body').hasClass('navPanel-visible')) {
            $('body').removeClass('navPanel-visible');
        }

        var weClosedSidebar = false;
        // Close sidebar if open when tour starts
        if (Detail && Detail.closeSidebar && $('.sidebar').hasClass('side-expanded')) {
            Detail.closeSidebar();
            weClosedSidebar = true;
        }

        // is this a simple record display?
        var simpleDisplay = $('#simpleDisplay').text() === 'true';

        var tour = new Shepherd.Tour({
            useModalOverlay: true,
            keyboardNavigation: false,
            defaultStepOptions: {
                modalOverlayOpeningPadding: 25,
                scrollTo: true,
                scrollToHandler: topScrollHandler,
                canClickTarget: false
            }
        });

        // Add step number indicator after tour is created
        tour.on('show', createStepNumberIndicator(tour));

        var buttons = createButtons(tour);

        // Check if the annotate button is present (NX_ENABLE_ANNOTATOR + write access)
        var annotateRecordVisible = $('#annotate-record-btn').length > 0;

        // Add tour steps
        if (!simpleDisplay) {
          tour.addStep({
              id: 'tut-welcome',
              title: 'This is the record detail page',
              text: 'The <em>detail</em> page shows all the details of a record generated from an Experiment. Click <em>Next</em> for a tour of the features of this record. You can also use the keyboard arrow keys to navigate through the tutorial.',
              buttons: [buttons.back(false), buttons.next]
          });
        } else {
          tour.addStep({
              id: 'tut-welcome',
              title: 'This is the simple record detail page',
              text: 'The <em>simple</em> detail page shows all the details of a record generated from an Experiment. This reduced-detail view is shown for records that contain a large number of datasets to keep the page performant. Click <em>Next</em> for a tour of the features of this record. You can also use the keyboard arrow keys to navigate through the tutorial.',
              buttons: [buttons.back(false), buttons.next]
          });
        }


        tour.addStep({
            id: 'tut-record-header',
            title: 'The record header',
            text: 'The top of the record contains basic information, such as the title of the experiment (taken from the calendar reservation), the instrument that was used, the number and types of files contained within, the user, date, and experimental motivation. This utility of this section relies heavily on the quality of data inputted into the reservation form.',
            attachTo: { element: '#record-header', on: 'bottom' },
            buttons: [buttons.back(true), buttons.next],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        tour.addStep({
            id: 'tut-session_info_column',
            title: 'Session summary information',
            text: 'The session summary section contains further details about the experiment, such as the precise date and time (from the calendar), the sample information and ID, and any sample description.',
            attachTo: { element: '#session_info_column', on: 'bottom' },
            scrollTo: false,
            buttons: [buttons.back(true), buttons.next],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        tour.addStep({
            id: 'tut-img_gallery',
            title: 'Image gallery',
            text: "The gallery shows a preview image of each dataset contained within the experiment's record. These can be browsed using the mouse buttons, or via the left and right arrow keys on the keyboard.",
            attachTo: { element: '#img_gallery', on: 'left' },
            scrollTo: false,
            buttons: [buttons.back(true), buttons.next],
            popperOptions: {
                modifiers: [{ name: 'offset', options: { offset: [0, 25] } }]
            }
        });

        // Activity-specific steps (only for non-simple display)
        if (!simpleDisplay) {
            tour.addStep({
                id: 'tut-aa',
                title: 'Acquisition activities',
                text: 'The remainder of the record contains details about the various "activities" that were detected in the records (determined via file creation times). Click <em>Next</em> for further details about the contents of each activity.',
                attachTo: { element: $('.aa_header_row')[0], on: 'left' },
                buttons: [buttons.back(true), buttons.next],
                scrollToHandler: function(element) { topScrollHandler(element, -1 * $(element).height() + 75); }
            });

            tour.addStep({
                id: 'tut-setup-params',
                title: 'Setup parameters',
                text: 'The setup parameters button will show you the metadata extracted from the raw files that is common to all the datasets contained in this activity. Clicking here will open a dialog box showing the setup parameters for this activity',
                attachTo: { element: $('.aa_header_row .param-button')[0], on: 'bottom' },
                buttons: [buttons.back(true), buttons.next],
                scrollTo: false,
                canClickTarget: false,
                modalOverlayOpeningPadding: 15,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 15] } }]
                }
            });

            tour.addStep({
                id: 'tut-aa-gallery',
                title: 'Activity image gallery',
                text: "Another preview of the datasets in this activity is shown here. Mouse over a dataset in the accompanying table to view its preview",
                attachTo: { element: $('.aa_header_row .aa-img-col')[0], on: 'bottom' },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next]
            });

            tour.addStep({
                id: 'tut-aa-table',
                title: 'Activity dataset table',
                text: "The activity details table lists each dataset contained in this activty with some basic information such as the dataset's name, its creation time, the type of data contained, and its role.",
                attachTo: { element: $('.aa_header_row .aa-table-col')[0], on: 'bottom' },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next]
            });

            if (annotateRecordVisible) {
                var firstDescEditIcon = $('.aa_header_row .aa-table tbody tr:first-child .nx-desc-edit')[0];
                if (firstDescEditIcon) {
                    tour.addStep({
                        id: 'tut-aa-inline-edit',
                        title: 'Inline description editing',
                        text: "Hover over any row in a dataset table to reveal the <i class='fa fa-pencil-alt' style='color:#adb5bd;font-size:0.8em;'></i> pencil icon next to the description field. Click it to open a quick-edit popup where you can type a description for that dataset and save with <kbd>Ctrl+Enter</kbd> (or <kbd>Cmd+Enter</kbd> on Mac).",
                        attachTo: { element: firstDescEditIcon, on: 'left' },
                        scrollTo: false,
                        buttons: [buttons.back(true), buttons.next],
                        modalOverlayOpeningPadding: 8,
                        floatingUIOptions: {
                            middleware: [FloatingUIDOM.offset({ mainAxis: 15 })]
                        },
                        beforeShowPromise: function() {
                            return new Promise(function(resolve) {
                                $(firstDescEditIcon).css('display', 'inline');
                                resolve();
                            });
                        },
                        when: {
                            hide: function() {
                                $(firstDescEditIcon).css('display', '');
                            }
                        }
                    });
                }
            }

            tour.addStep({
                id: 'tut-aa-meta',
                title: 'Metadata viewer/downloader',
                text: "The metadata column allows you to view the metadata unique to this dataset using the left button, or you can download the entire extracted metadata using the button on the right in JSON format.",
                attachTo: { element: $('.aa_header_row .aa-table-col .aa-meta-col')[0], on: 'left' },
                buttons: [buttons.back(true), buttons.next],
                scrollTo: false,
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });

            tour.addStep({
                id: 'tut-aa-dl',
                title: 'Individual file downloader',
                text: "The final column provides a link to download this single file in its native format (Note: there is a bulk file downloader at the top of the record)",
                attachTo: { element: $('.aa_header_row .aa-table-col .aa-dl-col')[0], on: 'left' },
                buttons: [buttons.back(true), buttons.next],
                scrollTo: false,
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });

            // Sidebar step
            var sidebar_vis = $('.sidebar').length > 0 && $('.sidebar').position()['left'] === 0 && !weClosedSidebar;
            var sidebar_text = "The sidebar provides an easy way to navigate through the different activities in the record, and also provides a button to return to the top of the page.";
            if (!sidebar_vis) {
                sidebar_text += " If the window is too narrow, the sidebar is hidden from view. Clicking this button will show it.";
            }

            tour.addStep({
                id: 'tut-sidebar',
                title: 'Record navigation sidebar',
                text: sidebar_text,
                attachTo: {
                    element: sidebar_vis ? $('.sidebar')[0] : $('#btn-sidebar')[0],
                    on: 'right'
                },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 15
            });

            tour.addStep({
                id: 'tut-filelisting',
                title: 'Record file listing and downloader',
                text: "The <i class='fa fa-cloud-download menu-fa'></i> <em>Download files</em> button provides an overview of all the dataset files in this record, and provides a means to download all (or a selected number of) files as a .zip archive. This dialogue also allows you to export a list of files into a variety of formats.",
                attachTo: { element: '#btn-filelisting', on: 'bottom' },
                scrollTo: true,
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        } else {
          tour.addStep({
              id: 'tut-file-listing',
              title: 'Dataset Listing',
              text: "The dataset listing is an interactive table of all the datasets in this record. You can use the search box to filter on the dataset names. Hovering your mouse over the preview button in each row will show you the image preview (click to open in a new tab/download). The metadata (in JSON) format or the dataset itself can be downloaded by clicking on the associated buttons in each row.",
              attachTo: { element: '#dataset-listing-header', on: 'right' },
              scrollTo: true,
              scrollToHandler: topScrollHandler,
              buttons: [buttons.back(true), buttons.next],
              modalOverlayOpeningPadding: 5,
          });
        }

        // Check if edit record button is visible to determine if we should add the edit step
        var editRecordVisible = $('#btn-edit-record').is(':visible');
        var hasStepsAfterDl = editRecordVisible || annotateRecordVisible;

        tour.addStep({
            id: 'tut-record-dl',
            title: 'Record downloader',
            text: "The <i class='fas fa-download menu-fa'></i> <em>Download Record</em> button lets you download the metadata record (not the actual datafiles) in either <i class='far fa-file-excel menu-fa'></i> <strong>XML</strong> or <i class='far fa-file-code menu-fa'></i> <strong>JSON</strong> format for additional analysis, if desired.",
            attachTo: { element: '#btn-download-record-group', on: 'bottom' },
            scrollTo: true,
            buttons: [buttons.back(true), hasStepsAfterDl ? buttons.next : buttons.end],
            modalOverlayOpeningPadding: 5,
        });

        // Only add edit record step if the button is visible
        if (editRecordVisible) {
            tour.addStep({
                id: 'tut-edit-record',
                title: 'Record editor',
                text: "The <i class='fa fa-file-text menu-fa'></i> <em>Edit this record</em> button will allow you (if logged in and you have ownership of this record) to edit the metadata information contained within. Currently, this process is a bit cumbersome, but an improvement to the interface is on the NexusLIMS team's roadmap.",
                attachTo: { element: '#btn-edit-record', on: 'bottom' },
                scrollTo: false,
                buttons: [buttons.back(true), annotateRecordVisible ? buttons.next : buttons.end],
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });
        }

        // Only add annotate record steps if the button is present (NX_ENABLE_ANNOTATOR + write access)
        if (annotateRecordVisible) {
            tour.addStep({
                id: 'tut-annotate-record',
                title: 'Annotate Record',
                text: "The <i class='fa fa-pencil menu-fa'></i> <em>Annotate Record</em> button opens a side panel where you can attach plain-language descriptions to each dataset captured during the experiment. Descriptions appear alongside the data in the gallery and activity tables, making it easier for collaborators to understand what was acquired. From this panel, you can also open the full-page annotator, or edit descriptions inline by hovering over a row in any dataset table.",
                attachTo: { element: '#annotate-record-btn', on: 'bottom' },
                scrollTo: true,
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 5,
                popperOptions: {
                    modifiers: [{ name: 'offset', options: { offset: [0, 10] } }]
                }
            });

            tour.addStep({
                id: 'tut-annotate-panel',
                title: 'Annotation side panel',
                text: "Datasets are listed here grouped by activity. Each card shows the dataset filename and a text box for its description; type directly in the boxes and click <strong>Save Annotations</strong> when done. Datasets with a green color already have descriptions. Use the <i class='fa fa-expand'></i> button in the panel header to open the full-page annotator, which also allows you to reassign datasets across activities.",
                attachTo: { element: '#annotate-offcanvas', on: 'left' },
                scrollTo: false,
                buttons: [buttons.back(true), buttons.end],
                modalOverlayOpeningPadding: 0,
                floatingUIOptions: {
                    middleware: [FloatingUIDOM.offset({ mainAxis: 12 })]
                },
                beforeShowPromise: function() {
                    return new Promise(function(resolve) {
                        var offcanvasEl = document.getElementById('annotate-offcanvas');
                        // If the panel is already visible, resolve immediately
                        if (offcanvasEl.classList.contains('show')) {
                            resolve();
                            return;
                        }
                        offcanvasEl.addEventListener('shown.bs.offcanvas', function onShown() {
                            offcanvasEl.removeEventListener('shown.bs.offcanvas', onShown);
                            resolve();
                        });
                        bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl).show();
                    });
                },
                when: {
                    hide: function() {
                        var offcanvasEl = document.getElementById('annotate-offcanvas');
                        var bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
                        if (bsOffcanvas) { bsOffcanvas.hide(); }
                    }
                }
            });
        }

        // Cleanup on exit
        var cur_pos = $(document).scrollTop();

        function clean_up_on_exit(modal_to_open) {
            // Shepherd only removes the modal overlay on `complete`, not `cancel` — the
            // overlay SVG path keeps pointer-events:all and blocks interaction after cancel.
            var overlay = document.querySelector('.shepherd-modal-overlay-container');
            if (overlay) { overlay.remove(); }

            // Re-enable scrolling using the page's existing scroll management mechanism
            $('body').removeClass('scrollDisabled');

            // Close the annotate offcanvas if it was opened during the tour
            if (annotateRecordVisible) {
                var offcanvasEl = document.getElementById('annotate-offcanvas');
                var bsOffcanvas = offcanvasEl && bootstrap.Offcanvas.getInstance(offcanvasEl);
                if (bsOffcanvas) { bsOffcanvas.hide(); }
            }

            // Remove focus outline from tutorial link
            $('#menu-tutorial, nav a, #navPanel a').filter(function() {
                return $(this).text().trim() === 'Tutorial';
            }).addClass('tour-completed');

            if ($(document).scrollTop() === cur_pos) {
                if (modal_to_open) {
                    Detail.openModal(modal_to_open);
                }
            } else {
                $('html, body').animate({
                    scrollTop: cur_pos
                }, {
                    duration: 500,
                    complete: modal_to_open ? function() {
                        Detail.openModal(modal_to_open);
                    } : null
                });
            }
        }

        tour.on('complete', function() { clean_up_on_exit(already_open_modal); });
        tour.on('cancel', function() { clean_up_on_exit(already_open_modal); });
        tour.on('hide', function() { clean_up_on_exit(already_open_modal); });

        // Allow clicking overlay to cancel
        tour.on('show', function() {
            setTimeout(function() {
                $('.shepherd-modal-overlay-container').on('click', function() {
                    tour.cancel();
                });
            }, 100);
        });

        return tour;
    }

    // ========================================================================
    // Annotator Tour
    // ========================================================================

    function createAnnotatorTour() {
        if (!shepherdAvailable()) {
            console.log('Shepherd.js not available');
            return null;
        }

        var tour = new Shepherd.Tour({
            useModalOverlay: true,
            defaultStepOptions: {
                cancelIcon: { enabled: true },
                classes: 'shepherd-theme-arrows',
                scrollTo: false
            }
        });

        var buttons = createButtons(tour);
        tour.on('show', createStepNumberIndicator(tour));

        tour.addStep({
            id: 'tut-ann-welcome',
            title: 'Full-page Annotator',
            text: 'This page lets you add plain-language descriptions to every dataset in the record and, when the record has more than one activity, reassign datasets between activities. Changes are not saved until you click <strong>Save Annotations</strong>.',
            // attachTo: { element: 'h4.mb-0', on: 'bottom' },
            buttons: [buttons.back(false), buttons.next],
            modalOverlayOpeningPadding: 5,
            floatingUIOptions: { middleware: [FloatingUIDOM.offset({ mainAxis: 10 })] }
        });

        var firstCard = document.querySelector('.annotate-card');
        if (firstCard) {
            tour.addStep({
                id: 'tut-ann-card',
                title: 'Dataset cards',
                text: "Each card represents one dataset. The filename appears at the top and the text box below is where you type your description. The left border changes color as you work: <span style='color:#198754;font-weight:600;'>green</span> means the dataset has a description and the current value matches what is currently saved in the record, <span style='color:#e67e00;font-weight:600;'>orange</span> means you have unsaved changes, and gray means no description has been added yet.",
                attachTo: { element: firstCard, on: 'bottom' },
                scrollTo: true,
                scrollToHandler: function(el) {
                    var top = el.getBoundingClientRect().top + window.pageYOffset - 120;
                    window.scrollTo({ top: top, behavior: 'smooth' });
                },
                buttons: [buttons.back(true), buttons.next],
                modalOverlayOpeningPadding: 6,
                floatingUIOptions: { middleware: [FloatingUIDOM.offset({ mainAxis: 12 })] }
            });

            var firstCb = document.querySelector('.nx-select-cb-label');
            if (firstCb) {
                tour.addStep({
                    id: 'tut-ann-batch',
                    title: 'Selecting and batch-moving',
                    text: "The checkbox in the top-left corner of each card lets you select one or more datasets at once. Once a card is selected, a toolbar appears at the bottom of the page with a <strong>Move to Activity</strong> dropdown for batch reassignment. You can also drag and drop any individual card directly into a different activity section to move it. Changes are not saved until you click \"Save\".",
                    attachTo: { element: firstCb, on: 'right' },
                    scrollTo: true,
                    scrollToHandler: function(el) {
                        var top = el.getBoundingClientRect().top + window.pageYOffset - 120;
                        window.scrollTo({ top: top, behavior: 'smooth' });
                    },
                    buttons: [buttons.back(true), buttons.next],
                    modalOverlayOpeningPadding: 4,
                    floatingUIOptions: { middleware: [FloatingUIDOM.offset({ mainAxis: 12 })] },
                    beforeShowPromise: function() {
                        return new Promise(function(resolve) {
                            $(firstCb).css('opacity', '1');
                            resolve();
                        });
                    },
                    when: {
                        hide: function() {
                            $(firstCb).css('opacity', '');
                        }
                    }
                });
            }
        }

        tour.addStep({
            id: 'tut-ann-save',
            title: 'Saving your work',
            text: "Click <strong>Save Annotations</strong> when you're done — this saves both descriptions and any pending dataset moves in a single request. You can also press <kbd>Ctrl+Enter</kbd> (or <kbd>Cmd+Enter</kbd> on Mac) to save from the keyboard.",
            attachTo: { element: '#annotate-save-btn', on: 'top' },
            scrollTo: true,
            buttons: [buttons.back(true), buttons.end],
            modalOverlayOpeningPadding: 5,
            floatingUIOptions: { middleware: [FloatingUIDOM.offset({ mainAxis: 12 })] }
        });

        function clean_up_on_exit() {
            var overlay = document.querySelector('.shepherd-modal-overlay-container');
            if (overlay) { overlay.remove(); }

            $('#menu-tutorial, nav a, #navPanel a').filter(function() {
                return $(this).text().trim() === 'Tutorial';
            }).addClass('tour-completed');
        }

        tour.on('complete', clean_up_on_exit);
        tour.on('cancel', clean_up_on_exit);
        tour.on('hide', clean_up_on_exit);

        tour.on('show', function() {
            setTimeout(function() {
                $('.shepherd-modal-overlay-container').on('click', function() {
                    tour.cancel();
                });
            }, 100);
        });

        return tour;
    }

    // ========================================================================
    // Public API
    // ========================================================================

    /**
     * Start the homepage tour
     */
    NexusLIMSTours.startHomepageTour = function() {
        if (!tutorialsEnabled()) {
            console.log('Tutorials are disabled');
            return;
        }
        var tour = createHomepageTour();
        if (tour) {
            tour.start();
        }
    };

    /**
     * Start the explore page tour
     */
    NexusLIMSTours.startExploreTour = function() {
        if (!tutorialsEnabled()) {
            console.log('Tutorials are disabled');
            return;
        }
        var tour = createExploreTour();
        if (tour) {
            tour.start();
        }
    };

    /**
     * Start the annotator page tour
     */
    NexusLIMSTours.startAnnotatorTour = function() {
        if (!tutorialsEnabled()) {
            console.log('Tutorials are disabled');
            return;
        }
        var tour = createAnnotatorTour();
        if (tour) {
            tour.start();
        }
    };

    /**
     * Start the detail page tour
     */
    NexusLIMSTours.startDetailTour = function() {
        if (!tutorialsEnabled()) {
            console.log('Tutorials are disabled');
            return;
        }
        var tour = createDetailTour();
        if (tour) {
            tour.start();
        }
    };

    /**
     * Start appropriate tour based on current page
     */
    NexusLIMSTours.startTour = function() {
        if (!tutorialsEnabled()) {
            console.log('Tutorials are disabled');
            return;
        }

        // Determine which page we're on
        if ($('#annotate-page-form').length > 0) {
            // We're on the full-page annotator
            NexusLIMSTours.startAnnotatorTour();
        } else if ($('#simpleDisplay').length > 0) {
            // We're on a detail page
            NexusLIMSTours.startDetailTour();
        } else if ($('#form_search').length > 0 || window.location.pathname.indexOf('/explore/keyword') !== -1) {
            // We're on the explore page
            NexusLIMSTours.startExploreTour();
        } else if ($('#homepage-tutorial').length > 0 || window.location.pathname === '/') {
            // We're on the homepage
            NexusLIMSTours.startHomepageTour();
        } else {
            console.log('No tour available for this page');
        }
    };

    // ========================================================================
    // Auto-initialization
    // ========================================================================

    $(document).ready(function() {
        if (!tutorialsEnabled()) {
            return;
        }

        // Attach click handlers to all tutorial links
        // Homepage tutorial link
        $('#homepage-tutorial').on('click', function(e) {
            e.preventDefault();
            NexusLIMSTours.startHomepageTour();
        });

        // Navbar tutorial link (find by text since it doesn't have a unique ID)
        $('nav#nav a, #navPanel a').filter(function() {
            return $(this).text().trim() === 'Tutorial';
        }).on('click', function(e) {
            e.preventDefault();
            NexusLIMSTours.startTour();
        });

        // Also expose for backward compatibility with NexusLIMSDetail
        if (window.NexusLIMSDetail) {
            window.NexusLIMSDetail.create_detail_tour = NexusLIMSTours.startDetailTour;
        }
    });

})(jQuery, window);
