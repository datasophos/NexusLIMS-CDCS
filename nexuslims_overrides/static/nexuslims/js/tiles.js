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
            var yellow = '#f5c636';
            var black = '#333';
            var blue = '#11659c';
            
            // Use event delegation on document to handle dynamically loaded tiles
            $(document).on('mouseenter', '.tile', function() {
                $(this).css({'cursor': 'pointer',
                             'background-color': '#efefef'});
                $('.icon', this).css({'background-color': yellow,
                                'color': black,
                                'transition': 'all 0.3s ease-in-out'});
                $('.text h3', this).css({'color': blue});
            });
            
            $(document).on('mouseleave', '.tile', function() {
                // on mouseout, reset the background colour
                $('.icon', this).css({'background-color': '#11659c',
                                'color': '#fff'});
                $('.text h3', this).css({'color': black});
                $(this).css({'cursor': 'inherit',
                             'background-color': 'inherit'});
            });
            
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
