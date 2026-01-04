/**
 * NexusLIMS Detail Page - UI Handlers
 *
 * Modals, accordions, scroll management, tooltips, keyboard handlers, and image gallery
 */

(function($, window) {
    'use strict';

    var Detail = window.NexusLIMSDetail;

    // ============================================================================
    // Scroll Management
    // ============================================================================

    var $body = $('body'),
        scrollDisabled = false;

    function scrollDisable() {
        if (scrollDisabled) {
            return;
        }
        $body.addClass('scrollDisabled');
        scrollDisabled = true;
    }

    function scrollEnable() {
        if (!scrollDisabled) {
            return;
        }
        $body.removeClass('scrollDisabled');
        scrollDisabled = false;
    }

    Detail.toTop = function() {
        document.body.scrollTop = document.documentElement.scrollTop = 0;
    };

    function showButtonOnScroll() {
        var header_pos = $('.list-record-experimenter').first().position()['top'];
        if (document.body.scrollTop > header_pos || document.documentElement.scrollTop > header_pos) {
            document.getElementById("to-top-btn").style.visibility = "visible";
            document.getElementById("to-top-btn").style.opacity = 1;
            if ($('#simpleDisplay').text() == 'true') {
                document.getElementById("to-top-btn").style.top = header_pos + 'px'
            }
        } else {
            document.getElementById("to-top-btn").style.visibility = "hidden";
            document.getElementById("to-top-btn").style.opacity = 0;
        }
    }

    var navElement = document.getElementById('nav');
    var titleBarElement = document.getElementById('titleBar');
    var sidebarElement = document.querySelector('.sidebar');
    var titlebarHeightPx = 80; // var(--titlebar-height) + var(--spacing-lg) (the initial padding)

    function updateSidebarPosition() {
        if (!navElement || !sidebarElement || !titleBarElement) {
            return;
        }

        // Use titleBar on narrow screens, nav on wide screens
        var topBar = window.innerWidth < 992 ? titleBarElement : navElement;
        var topBarRect = topBar.getBoundingClientRect();

        // Sidebar should follow the top bar's bottom edge, but not go above 0
        var sidebarTop = Math.max(0, topBarRect.bottom);

        // Don't use transition on top - let it follow scroll smoothly
        sidebarElement.style.top = sidebarTop + 'px';

        // No padding adjustment needed - the top position already handles positioning
        sidebarElement.style.paddingTop = '';
    }

    // Listen to scroll on both window and body (body is the actual scrollable element)
    var scrollHandler = function() {
        showButtonOnScroll();
        updateSidebarPosition();

        // Update sidebar height to account for dynamic top position
        // Get the actual computed top value, not just the inline style
        var computedStyle = window.getComputedStyle(sidebarElement);
        var sidebarTop = parseFloat(computedStyle.top);
        var sidebarHeight = window.innerHeight - sidebarTop;
        sidebarElement.style.height = sidebarHeight + 'px';
    };

    window.addEventListener('scroll', scrollHandler);
    document.body.addEventListener('scroll', scrollHandler);

    // ============================================================================
    // Modal Handlers
    // ============================================================================

    Detail.openModal = function(name) {
        var modal = document.getElementById(name);
        modal.style.opacity = 1;
        modal.style.visibility = "visible";

        scrollDisable();

        window.onclick = function(event) {
            if (event.target == modal) {
                Detail.closeModal(name);
            }
        };
    };

    Detail.closeModal = function(name) {
        var modal = document.getElementById(name);
        modal.style.opacity = 0;
        modal.style.visibility = "hidden";

        scrollEnable();
    };

    function getScrollbarWidth() {
        const outer = document.createElement('div');
        outer.style.visibility = 'hidden';
        outer.style.overflow = 'scroll';
        outer.style.msOverflowStyle = 'scrollbar';
        document.body.appendChild(outer);

        const inner = document.createElement('div');
        outer.appendChild(inner);

        const scrollbarWidth = (outer.offsetWidth - inner.offsetWidth);
        outer.parentNode.removeChild(outer);

        return scrollbarWidth;
    }

    // ============================================================================
    // Sidebar Handlers
    // ============================================================================

    function openSidebar() {
        var sidebar = $('.sidebar');
        sidebar.addClass('side-expanded');
        updateSidebarButtonIcon();
        updateSidebarButtonTooltip();
    }

    function closeSidebar() {
        var sidebar = $('.sidebar');
        sidebar.removeClass('side-expanded');
        updateSidebarButtonIcon();
        updateSidebarButtonTooltip();
    }

    function updateSidebarButtonIcon() {
        var icon = $('#btn-sidebar i');
        var sidebar = $('.sidebar');
        if (sidebar.hasClass('side-expanded')) {
            icon.removeClass('fa-chevron-right').addClass('fa-chevron-left');
        } else {
            icon.removeClass('fa-chevron-left').addClass('fa-chevron-right');
        }
    }

    function updateSidebarButtonTooltip() {
        var sidebar = $('.sidebar');
        var btn = document.getElementById('btn-sidebar');
        if (btn && btn.getAttribute('data-bs-toggle') === 'tooltip') {
            var tooltip = bootstrap.Tooltip.getInstance(btn);
            if (tooltip) {
                var newTitle = sidebar.hasClass('side-expanded') 
                    ? 'Click to close sidebar' 
                    : 'Click to explore record contents';
                
                // Update the data-bs-title attribute (Bootstrap reads from this)
                btn.setAttribute('data-bs-title', newTitle);
                
                // Update the tooltip's internal title property
                tooltip._config.title = newTitle;
            }
        }
    }

    function setSidebarTooltipTop() {
        var tip = $('.btn-sidebar-tooltip');
        var btn = $('#btn-sidebar');
        tip.css('top', parseInt(btn.css('top'), 10) + btn.height()/2 - tip.height()/2);
    }

    // Initialize sidebar handlers
    $(document).ready(function() {
        // Move sidebar button into titleBar immediately after the toggle button
        var sidebarBtn = $('#btn-sidebar');
        var toggleBtn = $('#titleBar .toggle');
        if (sidebarBtn.length && toggleBtn.length) {
            sidebarBtn.detach().insertAfter(toggleBtn);
        }

        // Add click handler to sidebar button
        $("#btn-sidebar").on('click', function(e) {
            e.stopPropagation(); // Prevent document click handler from firing
            var sidebar = $('.sidebar');
            if (sidebar.hasClass('side-expanded')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        // Custom tooltip template for sidebar button
        var sidebarBtn = $('#btn-sidebar[data-bs-toggle="tooltip"]')[0];
        if (sidebarBtn) {
            new bootstrap.Tooltip(sidebarBtn, {
                template: '<div class="tooltip btn-sidebar-tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
            });
        }

        $("#btn-sidebar").on('hover', setSidebarTooltipTop);

        // Add listener to close sidebar when clicking outside
        $(document).on("click", function(e) {
            var target = $(e.target);
            
            // Don't close if clicking the sidebar button
            if (target.closest('#btn-sidebar').length) {
                return;
            }
            
            // Don't close if clicking a pagination button inside nav-table (sidebar's table)
            var pagingButton = target.closest('.dt-paging-button');
            if (pagingButton.length) {
                if (pagingButton.attr('aria-controls') === 'nav-table') {
                    return;
                }
            }
            
            // Don't close if clicking inside the sidebar (including all child elements)
            if (target.closest('.sidebar').length) {
                return;
            }
            
            // Click is outside - close the sidebar if it's expanded
            var sidebar = $(".sidebar");
            if (sidebar.hasClass('side-expanded')) {
                closeSidebar();
            }
        });
    });

    // ============================================================================
    // Accordion Handlers
    // ============================================================================

    function closePanel(acc) {
        var panel = acc.next();
        acc.removeClass("active-accordion");
        panel.css('maxHeight', 0);
    }

    function openPanel(acc) {
        var panel = acc.next();
        acc.addClass("active-accordion");
        panel.css('maxHeight', panel.prop('scrollHeight') + "px");
    }

    function togglePanel(acc) {
        if (acc.hasClass("active-accordion")) {
            closePanel(acc);
        } else {
            openPanel(acc);
        }
    }

    Detail.closeAccords = function() {
        $('button[id*=idm]').each(function() {
            Detail.toggleAA($(this).prop('id'), false, true);
        });
    };

    Detail.openAccords = function() {
        $('button[id*=idm]').each(function() {
            Detail.toggleAA($(this).prop('id'), true, false);
        });
    };

    Detail.toggleAA = function(btn_id, force_open, force_close) {
        force_open = force_open || false;
        force_close = force_close || false;

        var collapse_str = "<i class='fa fa-minus-square-o'></i> Collapse Activity";
        var expand_str = "<i class='fa fa-plus-square-o'></i> Expand Activity";

        var btn = $('#' + btn_id);
        var action_is_expand = btn.text().includes('Expand');

        if (force_close) {
            action_is_expand = false;
        }

        var acc = btn.parents().eq(2).nextUntil('.container-fluid').filter('.accordion');

        acc.each(function(index) {
            var panel = $(this).next();
            if (action_is_expand || force_open) {
                openPanel($(this));
                btn.html(collapse_str);
                btn.addClass('btn-danger');
                btn.removeClass('btn-success');
            } else if (!(action_is_expand) || force_close) {
                closePanel($(this));
                btn.html(expand_str);
                btn.addClass('btn-success');
                btn.removeClass('btn-danger');
            }
        });
    };

    // Initialize accordion handlers
    $(document).ready(function() {
        var acc = document.getElementsByClassName("accordion");
        for (var i = 0; i < acc.length; i++) {
            acc[i].addEventListener("click", function() {
                togglePanel($(this));
            });
        }
    });

    // ============================================================================
    // Image Gallery
    // ============================================================================

    var slideIndex = 1;

    function showSlides(n) {
        var i;
        var slides = document.getElementsByClassName("slide");
        if (slides.length === 0) {
            var gallery = document.getElementById('img_gallery');
            if (gallery) gallery.remove();
        } else {
            if (n > slides.length) { slideIndex = 1 }
            if (n < 1) { slideIndex = slides.length }
            for (i = 0; i < slides.length; i++) {
                slides[i].style.display = "none";
            }
            slides[slideIndex - 1].style.display = "block";
        }
    }

    Detail.plusSlide = function(n) {
        showSlides(slideIndex += n);
    };

    function currentSlide(n) {
        showSlides(slideIndex = n);
    }

    function addSlide(source) {
        var slide = document.createElement("div");
        slide.class = "slide";
        var image = document.createElement("img");
        image.src = source;
        var text = document.createElement("div");
        text.class = "text";
        text.innerHTML = source;

        slide.innerHTML = image + source;
        document.getElementById("img_gallery").appendChild(slide);
    }

    // Initialize gallery
    $(document).ready(function() {
        showSlides(slideIndex);
    });

    // ============================================================================
    // Tooltip Management
    // ============================================================================

    Detail.disable_gallery_tooltips = function() {
        // Bootstrap 5: Disable gallery tooltips
        var galleryTooltipElements = document.querySelectorAll('#img_gallery a.gal-nav[data-bs-toggle="tooltip"]');
        galleryTooltipElements.forEach(function(el) {
            var tooltip = bootstrap.Tooltip.getInstance(el);
            if (tooltip) {
                tooltip.disable();
            }
        });
    };

    // ============================================================================
    // Keyboard Handlers
    // ============================================================================

    document.onkeydown = function(evt) {
        evt = evt || window.event;
        var isLeft = (evt.keyCode === 37);
        var isRight = (evt.keyCode === 39);
        var isEscape = (evt.keyCode === 27);

        if (isLeft) {
            if (Shepherd.activeTour) {
                Shepherd.activeTour.back();
            } else {
                Detail.plusSlide(-1);
            }
        }
        if (isRight) {
            if (Shepherd.activeTour) {
                Shepherd.activeTour.next();
            } else {
                Detail.plusSlide(1);
            }
        }
        if (isEscape) {
            var modals = document.getElementsByClassName("modal");
            for (var i = 0; i < modals.length; i++) {
                Detail.closeModal(modals[i].id);
            }
        }
    };

    // Prevent buttons from getting focus on click
    $(document).ready(function() {
        $('button').on('mousedown', function(event) {
            event.preventDefault();
        });
    });

})(jQuery, window);
