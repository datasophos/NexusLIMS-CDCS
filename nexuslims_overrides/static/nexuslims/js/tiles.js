/**
 * NexusLIMS Tile Hover Effects (jQuery version)
 */

// Wait for jQuery to be available
(function() {
    function initTiles() {
        if (typeof jQuery === 'undefined') {
            // jQuery not loaded yet, wait and try again
            setTimeout(initTiles, 100);
            return;
        }

        // jQuery is loaded, proceed
        jQuery(document).ready(function($) {
            // Make entire tile clickable
            $(document).on('click', '.tile', function(){
                var link = $(this).find('a').first().attr('href');
                if (link) {
                    window.location.href = link;
                }
            });
        });
    }

    // Start trying to initialize
    initTiles();
})();
