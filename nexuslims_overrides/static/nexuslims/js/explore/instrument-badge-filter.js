/**
 * Instrument Badge Filter
 * Makes instrument badges clickable to filter search results by instrument PID
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initializeInstrumentBadgeFilter();
    });

    function initializeInstrumentBadgeFilter() {
        // Use event delegation - results container exists at page load
        const resultsContainer = document.querySelector('#results');

        if (!resultsContainer) {
            console.warn('Results container not found for instrument badge filter');
            return;
        }

        // Delegate click events with CAPTURE phase to intercept before .a-result handler
        resultsContainer.addEventListener('click', handleBadgeClick, true);

        // Keyboard accessibility
        resultsContainer.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                handleBadgeClick(e);
            }
        }, true);

        console.log('Instrument badge filter initialized');
    }

    function handleBadgeClick(e) {
        const badge = e.target.closest('.instrument-badge-clickable');

        if (!badge) {
            return; // Not a badge click
        }

        // Stop propagation to prevent .a-result click handler
        e.stopPropagation();
        e.preventDefault();

        const instrumentPid = badge.getAttribute('data-instrument-pid');

        if (!instrumentPid) {
            console.error('Badge missing data-instrument-pid attribute');
            return;
        }

        addInstrumentFilter(instrumentPid);
    }

    function addInstrumentFilter(pid) {
        const searchField = $('#id_keywords');

        if (!searchField.length) {
            console.error('Search field #id_keywords not found');
            return;
        }

        // Build the search operator tag
        const filterTag = 'instrument-pid:' + pid;

        // REPLACE existing instrument-pid filters (user preference)
        const existingTags = searchField.tagit('assignedTags');
        existingTags.forEach(function(tag) {
            if (tag.startsWith('instrument-pid:')) {
                searchField.tagit('removeTagByLabel', tag);
            }
        });

        // Check if this exact filter already exists after removal
        if (searchField.tagit('assignedTags').indexOf(filterTag) !== -1) {
            return; // Already filtered by this instrument
        }

        // Add the new tag
        searchField.tagit('createTag', filterTag);

        // Auto-submit (user preference)
        $('#form_search').submit();
    }

})();
