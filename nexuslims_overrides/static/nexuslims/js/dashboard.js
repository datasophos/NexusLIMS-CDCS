/**
 * NexusLIMS Dashboard JavaScript
 *
 * Handles dynamic dropdown menu height calculation to prevent overflow beyond footer
 */

(function() {
    'use strict';

    $(document).ready(function() {
        // console.log('[Dashboard] Script loaded');

        // Find dropdown toggles (buttons with data-bs-toggle="dropdown")
        const $dropdownToggles = $('.my-dashboard-content [data-bs-toggle="dropdown"]');
        // console.log('[Dashboard] Found', $dropdownToggles.length, 'dropdown toggles');

        // Dynamically limit dropdown menu height based on available space
        $dropdownToggles.on('show.bs.dropdown', function() {
            // console.log('[Dashboard] Dropdown opening...');

            const $toggle = $(this);
            // The menu is a sibling of the button
            const $menu = $toggle.siblings('.dropdown-menu');

            // console.log('[Dashboard] Toggle element:', $toggle[0]);
            // console.log('[Dashboard] Menu element:', $menu[0]);
            // console.log('[Dashboard] Menu siblings:', $toggle.siblings());

            // Reset any previous max-height
            $menu.css('max-height', '');

            // Small delay to ensure dropdown is positioned
            setTimeout(function() {
                // Get positions
                const toggleBottom = $toggle.offset().top + $toggle.outerHeight();
                const windowHeight = $(window).height();

                // console.log('[Dashboard] Toggle bottom position:', toggleBottom);
                // console.log('[Dashboard] Window height:', windowHeight);

                // Find footer position (if it exists)
                const $footer = $('#footer');
                const footerTop = $footer.length ? $footer.offset().top : windowHeight;

                // console.log('[Dashboard] Footer found:', $footer.length > 0);
                // console.log('[Dashboard] Footer top position:', footerTop);

                // Calculate available space (use the smaller of footer position or window height)
                const maxBottom = Math.min(footerTop, windowHeight);
                const availableSpace = maxBottom - toggleBottom - 20; // 20px padding from bottom

                // console.log('[Dashboard] Max bottom:', maxBottom);
                // console.log('[Dashboard] Available space:', availableSpace);

                // Only apply max-height if space is limited
                if (availableSpace < 500) { // Only constrain if less than 500px available
                    // Calculate minimum height from rem (2.5rem)
                    const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
                    const minHeightPx = 4 * rootFontSize;
                    const newMaxHeight = Math.max(availableSpace, minHeightPx);
                    // console.log('[Dashboard] Applying max-height:', newMaxHeight + 'px');

                    $menu.css({
                        'max-height': newMaxHeight + 'px',
                        'overflow-y': 'auto',
                        'overflow-x': 'hidden'
                    });
                } else {
                    // console.log('[Dashboard] Plenty of space, no constraint needed');
                }
            }, 10);
        });

        // Clean up when dropdown closes
        $dropdownToggles.on('hidden.bs.dropdown', function() {
            const $toggle = $(this);
            const $menu = $toggle.siblings('.dropdown-menu');
            // console.log('[Dashboard] Dropdown closed, cleaning up');
            $menu.css('max-height', '');
        });
    });

})();
