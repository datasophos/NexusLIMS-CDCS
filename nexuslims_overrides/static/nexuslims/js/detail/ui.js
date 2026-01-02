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
        scrollDisabled = false,
        scrollTop;

    function scrollDisable() {
        if (scrollDisabled) {
            return;
        }
        scrollTop = $(window).scrollTop();
        $body.addClass('scrollDisabled').css({
            top: -1 * scrollTop
        });
        scrollDisabled = true;
    }

    function scrollEnable() {
        if (!scrollDisabled) {
            return;
        }
        $body.removeClass('scrollDisabled');
        $(window).scrollTop(scrollTop);
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

    window.onscroll = function() { showButtonOnScroll() };

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

    Detail.activate_metadata_tooltips = function() {
        // Bootstrap 5: Initialize metadata tooltips
        var metadataTooltipElements = document.querySelectorAll('table.meta-table [data-bs-toggle="tooltip"]');
        metadataTooltipElements.forEach(function(el) {
            new bootstrap.Tooltip(el, { trigger: 'hover' });
        });
    };

    Detail.activate_modal_tooltips = function(id) {
        // Bootstrap 5: Dispose old tooltips and create new ones
        var modalTooltipElements = document.querySelectorAll(`#${id} [data-bs-toggle="tooltip"]`);
        modalTooltipElements.forEach(function(el) {
            var tooltip = bootstrap.Tooltip.getInstance(el);
            if (tooltip) {
                tooltip.dispose();
            }
            new bootstrap.Tooltip(el, {
                trigger: 'hover',
                container: `#${id}`
            });
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
