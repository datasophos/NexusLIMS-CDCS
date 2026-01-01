/**
 * NexusLIMS Override: Disable Leave Notice
 * 
 * This file overrides the core_main_app leave notice functionality.
 * The leave notice warns users when navigating away from forms with unsaved changes.
 * This override disables that functionality for a smoother user experience.
 */

/**
 * Stub function - does nothing
 * Prevents "leaveNotice is not defined" errors when other code tries to call it
 */
function leaveNotice() {
    // Intentionally empty - disables the leave notice functionality
    return;
}
