"""E2E tests for the annotator record editor."""
import datetime

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_sample(page, name, pid="", description="", elements=()):
    """Add a sample via the modal and wait for it to appear in the list."""
    page.locator("#nx-add-sample-btn").click()
    page.locator("#nx-sample-modal").wait_for(state="visible")
    page.locator("#nx-sample-name").fill(name)
    if pid:
        page.locator("#nx-sample-pid").fill(pid)
    if description:
        page.locator("#nx-sample-description").fill(description)
    for sym in elements:
        page.locator("#nx-elements-input").fill(sym)
        page.locator("#nx-elements-input").press("Enter")
    page.locator("#nx-sample-modal-save").click()
    page.locator("#nx-sample-modal").wait_for(state="hidden")


def _add_new_activity(page):
    """Click 'Add Activity' and return the seqno of the newly added row."""
    before = page.locator(".nx-sortable-activity").count()
    page.locator("#nx-add-activity-btn").click()
    page.locator(".nx-sortable-activity").nth(before).wait_for(state="visible")
    return page.locator(".nx-sortable-activity").last.get_attribute("data-seqno")


@pytest.fixture
def annotator_page(authenticated_page, base_url, test_record_id):
    """Navigate to the annotator for the test record."""
    page = authenticated_page
    page.goto(f"{base_url}/annotate/{test_record_id}/")
    page.wait_for_load_state("networkidle")
    return page


# ===========================================================================
# General annotator behaviour
# ===========================================================================


class TestAnnotatorGeneral:
    """Smoke tests and basic interactions that apply to the annotator as a whole."""

    def test_annotator_loads(self, annotator_page):
        """Annotator page renders without error."""
        page = annotator_page
        assert page.locator("#annotate-save-btn").count() > 0
        assert page.locator("#nx-title-display").count() > 0

    def test_title_inline_edit(self, annotator_page):
        """Clicking the title edit button opens an inline input."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        assert inline_input.is_visible()

    def test_title_edit_marks_dirty(self, annotator_page):
        """Changing the title marks the title bar as dirty."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill("E2E Test Title Change")
        inline_input.press("Enter")
        assert page.locator("#nx-title-bar.nx-title-dirty").count() > 0

    def test_description_textarea_accepts_input(self, annotator_page):
        """Description textareas accept text input."""
        page = annotator_page
        textareas = page.locator(".annotate-textarea").all()
        if not textareas:
            pytest.skip("No description textareas found on this record")
        first_ta = textareas[0]
        first_ta.fill("E2E test description content")
        assert first_ta.input_value() == "E2E test description content"

    def test_add_sample(self, annotator_page):
        """Clicking 'Add Sample' opens the sample modal."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        modal = page.locator("#nx-sample-modal")
        modal.wait_for(state="visible")
        assert modal.is_visible()

    def test_save_sample_from_modal(self, annotator_page):
        """Adding a sample via the modal renders it in the sample list."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("E2E Test Sample")
        page.locator("#nx-sample-modal-save").click()
        page.locator("#nx-sample-modal").wait_for(state="hidden")
        assert page.locator("#nx-samples-list").inner_text().find("E2E Test Sample") >= 0

    def test_pending_changes_modal_on_navigation(self, annotator_page):
        """Making a change reveals #nx-view-changes-btn which opens the pending-changes modal."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill("Unsaved E2E Change")
        inline_input.press("Enter")

        view_changes_btn = page.locator("#nx-view-changes-btn")
        view_changes_btn.wait_for(state="visible")
        view_changes_btn.click()
        modal = page.locator("#nx-pending-changes-modal")
        modal.wait_for(state="visible")
        assert modal.is_visible()

    def test_save_button_submits(self, annotator_page, base_url, test_record_id):
        """Saving edits redirects to the detail page and displays the updated title."""
        page = annotator_page
        new_title = f"E2E Save Test {datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        page.locator("#nx-title-edit-btn").click()
        inline_input = page.locator("#nx-title-bar input[type='text']")
        inline_input.wait_for(state="visible")
        inline_input.fill(new_title)
        inline_input.press("Enter")

        page.locator("#annotate-save-btn").click()
        page.wait_for_load_state("networkidle")

        assert f"id={test_record_id}" in page.url
        title_el = page.locator(".list-record-title.page-header")
        assert new_title in title_el.inner_text()


# ===========================================================================
# Sample editing
# ===========================================================================


class TestSampleEditing:
    """Edit an existing sample via the sample modal."""

    def test_edit_opens_prepopulated_modal(self, annotator_page):
        """Clicking Edit on a sample row opens the modal pre-filled with its name."""
        page = annotator_page
        _add_sample(page, "Original Name")

        # Scope to the row that contains this sample so existing samples don't interfere.
        page.locator("#nx-samples-list > div").filter(has_text="Original Name").locator(
            "button:has-text('Edit')"
        ).click()
        page.locator("#nx-sample-modal").wait_for(state="visible")

        assert page.locator("#nx-sample-modal-title").inner_text() == "Edit Sample"
        assert page.locator("#nx-sample-name").input_value() == "Original Name"

    def test_edit_updates_name_in_list(self, annotator_page):
        """Saving an edited sample reflects the new name in the samples list."""
        page = annotator_page
        _add_sample(page, "Before Edit")

        page.locator("#nx-samples-list > div").filter(has_text="Before Edit").locator(
            "button:has-text('Edit')"
        ).click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("After Edit")
        page.locator("#nx-sample-modal-save").click()
        page.locator("#nx-sample-modal").wait_for(state="hidden")

        list_text = page.locator("#nx-samples-list").inner_text()
        assert "After Edit" in list_text
        assert "Before Edit" not in list_text


# ===========================================================================
# Sample deletion
# ===========================================================================


class TestSampleDeletion:
    """Delete samples, including those assigned to activities."""

    def test_delete_unassigned_sample_removes_from_list(self, annotator_page):
        """Deleting an unassigned sample removes it from the list without a dialog."""
        page = annotator_page
        _add_sample(page, "Delete Me")
        assert "Delete Me" in page.locator("#nx-samples-list").inner_text()

        # Scope to the specific sample row so existing samples don't interfere.
        page.locator("#nx-samples-list > div").filter(has_text="Delete Me").locator(
            "button[title='Delete sample']"
        ).click()
        assert "Delete Me" not in page.locator("#nx-samples-list").inner_text()

    def test_delete_assigned_sample_shows_confirm_dialog(self, annotator_page):
        """Deleting a sample that is assigned to an activity triggers a confirm dialog."""
        page = annotator_page
        if page.locator(".nx-activity-sample").count() == 0:
            pytest.skip("No activity sample dropdowns on this record")

        _add_sample(page, "Assigned Sample")
        page.locator(".nx-activity-sample").first.select_option(label="Assigned Sample")

        # page.expect_event("dialog") conflicts with synchronous window.confirm() — the
        # click never "completes" because JS is paused by the dialog.  Use page.once()
        # with an assertion flag instead, matching the pattern in the test below.
        dialog_seen = []
        page.once("dialog", lambda d: (dialog_seen.append(True), d.dismiss()))
        page.locator("#nx-samples-list > div").filter(has_text="Assigned Sample").locator(
            "button[title='Delete sample']"
        ).click()
        assert dialog_seen, "Expected a confirmation dialog but none appeared"

    def test_dismiss_confirm_keeps_sample_in_list(self, annotator_page):
        """Dismissing the confirmation dialog leaves the sample in the list."""
        page = annotator_page
        if page.locator(".nx-activity-sample").count() == 0:
            pytest.skip("No activity sample dropdowns on this record")

        _add_sample(page, "Keep Me")
        page.locator(".nx-activity-sample").first.select_option(label="Keep Me")

        def _dismiss(d):
            d.dismiss()

        page.on("dialog", _dismiss)
        page.locator("#nx-samples-list > div").filter(has_text="Keep Me").locator(
            "button[title='Delete sample']"
        ).click()
        page.locator("#nx-samples-list").wait_for()
        assert "Keep Me" in page.locator("#nx-samples-list").inner_text()


# ===========================================================================
# Sample modal validation
# ===========================================================================


class TestSampleValidation:
    """Sample modal enforces a non-empty name."""

    def test_empty_name_adds_invalid_class(self, annotator_page):
        """Saving without a name adds the is-invalid class to the name input."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("")
        page.locator("#nx-sample-modal-save").click()
        assert page.locator("#nx-sample-name.is-invalid").count() > 0

    def test_empty_name_keeps_modal_open(self, annotator_page):
        """Saving without a name does not dismiss the modal."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-sample-name").fill("")
        page.locator("#nx-sample-modal-save").click()
        assert page.locator("#nx-sample-modal").is_visible()


# ===========================================================================
# Sample persistent identifier (PID)
# ===========================================================================


class TestSamplePID:
    """PID values render as links when they look like URLs, otherwise as text."""

    def test_url_pid_renders_as_anchor(self, annotator_page):
        """An https:// PID renders as an <a> element with the correct href."""
        page = annotator_page
        _add_sample(page, "PID Sample", pid="https://doi.org/10.1234/sample")
        assert (
            page.locator("#nx-samples-list a[href='https://doi.org/10.1234/sample']").count() > 0
        )

    def test_non_url_pid_renders_as_plain_text(self, annotator_page):
        """A PID without an http scheme renders as text (no anchor element)."""
        page = annotator_page
        _add_sample(page, "Plain PID Sample", pid="ark:/99999/fk4test")
        assert "ark:/99999/fk4test" in page.locator("#nx-samples-list").inner_text()
        assert (
            page.locator("#nx-samples-list a[href='ark:/99999/fk4test']").count() == 0
        )


# ===========================================================================
# Sample element tags
# ===========================================================================


class TestSampleElements:
    """Element tag input in the sample modal."""

    def test_add_element_shows_badge_chip(self, annotator_page):
        """Typing a valid symbol and pressing Enter adds a badge in the tags container."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-elements-input").fill("Fe")
        page.locator("#nx-elements-input").press("Enter")
        assert page.locator("#nx-elements-tags .badge").count() > 0
        assert "Fe" in page.locator("#nx-elements-tags").inner_text()

    def test_remove_element_via_x_button(self, annotator_page):
        """Clicking × on an element badge removes it from the tag list."""
        page = annotator_page
        page.locator("#nx-add-sample-btn").click()
        page.locator("#nx-sample-modal").wait_for(state="visible")
        page.locator("#nx-elements-input").fill("Au")
        page.locator("#nx-elements-input").press("Enter")
        page.locator("#nx-elements-tags .badge button").first.click()
        assert "Au" not in page.locator("#nx-elements-tags").inner_text()

    def test_elements_appear_as_chips_in_sample_list(self, annotator_page):
        """Elements saved with a sample appear as code chips in the sample list."""
        page = annotator_page
        _add_sample(page, "Alloy Sample", elements=["Ni", "Cr"])
        list_text = page.locator("#nx-samples-list").inner_text()
        assert "Ni" in list_text
        assert "Cr" in list_text


# ===========================================================================
# Sample persistence (round-trip save)
# ===========================================================================


class TestSamplePersistence:
    """Sample data survives a save and page reload."""

    def test_saved_sample_appears_on_reload(self, annotator_page, base_url, test_record_id):
        """A sample added and saved is still present when the annotator reloads."""
        page = annotator_page
        unique = datetime.datetime.now().strftime("%H%M%S%f")
        name = f"Persist-{unique}"
        _add_sample(page, name)
        page.locator("#annotate-save-btn").click()
        page.wait_for_load_state("networkidle")

        page.goto(f"{base_url}/annotate/{test_record_id}/")
        page.wait_for_load_state("networkidle")
        assert name in page.locator("#nx-samples-list").inner_text()


# ===========================================================================
# Activity management
# ===========================================================================


class TestActivityManagement:
    """Add, insert, delete activities and verify label renumbering."""

    def test_add_activity_at_end(self, annotator_page):
        """Clicking 'Add Activity' appends a new sortable activity row."""
        page = annotator_page
        before = page.locator(".nx-sortable-activity").count()
        page.locator("#nx-add-activity-btn").click()
        assert page.locator(".nx-sortable-activity").count() == before + 1

    def test_insert_activity_below(self, annotator_page):
        """Clicking '+ below' on an activity inserts a new row directly after it."""
        page = annotator_page
        if page.locator(".nx-insert-activity-below").count() == 0:
            pytest.skip("No insert-below buttons on this record")
        before = page.locator(".nx-sortable-activity").count()
        page.locator(".nx-insert-activity-below").first.click()
        assert page.locator(".nx-sortable-activity").count() == before + 1

    def test_delete_empty_activity(self, annotator_page):
        """Deleting a newly added (empty) activity removes its row from the DOM."""
        page = annotator_page
        before = page.locator(".nx-sortable-activity").count()
        page.locator("#nx-add-activity-btn").click()
        page.locator(".nx-delete-activity:not([disabled])").last.click()
        assert page.locator(".nx-sortable-activity").count() == before

    def test_delete_button_disabled_when_activity_has_datasets(self, annotator_page):
        """The trash button is disabled for activities that contain datasets."""
        page = annotator_page
        all_btns = page.locator(".nx-delete-activity").all()
        nonempty = [
            b for b in all_btns
            if int(b.get_attribute("data-dataset-count") or "0") > 0
        ]
        if not nonempty:
            pytest.skip("No activities with datasets found on this record")
        for btn in nonempty:
            assert btn.is_disabled()

    def test_activity_labels_are_sequential_after_add(self, annotator_page):
        """After adding an activity, all labels read 'Activity 1', 'Activity 2', …"""
        page = annotator_page
        page.locator("#nx-add-activity-btn").click()
        labels = page.locator(".nx-activity-label").all()
        # text_content() reads raw DOM text before CSS text-transform is applied.
        for i, lbl in enumerate(labels, start=1):
            assert f"Activity {i}" in lbl.text_content()


# ===========================================================================
# Dataset checkbox selection and toolbar
# ===========================================================================


class TestDatasetSelection:
    """Checkbox selection shows the batch toolbar and maintains a count badge."""

    def test_checking_dataset_makes_toolbar_visible(self, annotator_page):
        """Checking a dataset checkbox reveals the move toolbar."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() == 0:
            pytest.skip("No dataset checkboxes on this record")
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-toolbar").wait_for(state="visible")
        assert page.locator("#nx-move-toolbar").is_visible()

    def test_selection_count_badge_updates(self, annotator_page):
        """Checking two datasets shows '2' in the selection count badge."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() < 2:
            pytest.skip("Fewer than 2 dataset checkboxes on this record")
        page.locator(".nx-select-cb").nth(0).click()
        page.locator(".nx-select-cb").nth(1).click()
        count_el = page.locator("#nx-toolbar-sel-count")
        count_el.wait_for(state="visible")
        assert "2" in count_el.inner_text()

    def test_clear_selection_unchecks_all_datasets(self, annotator_page):
        """Clicking 'Clear selection' unchecks every dataset card."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() == 0:
            pytest.skip("No dataset checkboxes on this record")
        page.locator(".nx-select-cb").first.click()
        clear_btn = page.locator("#nx-clear-selection")
        clear_btn.wait_for(state="visible")
        clear_btn.click()
        assert page.locator(".nx-select-cb:checked").count() == 0


# ===========================================================================
# Batch move via toolbar dropdown
# ===========================================================================


class TestBatchMove:
    """Select datasets and move them via the toolbar dropdown or undo controls."""

    def _select_first_and_move_to_new(self, page):
        """Helper: add a fresh empty activity, select first dataset, batch-move there."""
        if page.locator(".nx-select-cb").count() == 0:
            pytest.skip("No dataset checkboxes on this record")
        new_seqno = _add_new_activity(page)
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-dropdown-btn").wait_for(state="visible")
        page.locator("#nx-move-dropdown-btn").click()
        page.locator(f"#nx-move-dropdown [data-seqno='{new_seqno}']").click()
        return new_seqno

    def test_batch_move_places_dataset_in_target_activity(self, annotator_page):
        """After a batch move the dataset card appears in the target activity row."""
        page = annotator_page
        new_seqno = self._select_first_and_move_to_new(page)
        target_row = page.locator(f".nx-sortable-activity[data-seqno='{new_seqno}']")
        assert target_row.locator(".nx-dataset-col").count() > 0

    def test_moved_dataset_shows_moved_badge(self, annotator_page):
        """A dataset that has been moved carries a 'Moved' badge."""
        page = annotator_page
        self._select_first_and_move_to_new(page)
        assert page.locator(".nx-moved-badge").count() > 0

    def test_undo_individual_move_via_badge(self, annotator_page):
        """Clicking the 'Moved' badge returns the card to its original activity."""
        page = annotator_page
        orig_row = page.locator(".nx-sortable-activity").first
        orig_count = orig_row.locator(".nx-dataset-col").count()
        if orig_count == 0:
            pytest.skip("No datasets in first activity")

        self._select_first_and_move_to_new(page)
        badge = page.locator(".nx-moved-badge").first
        badge.wait_for(state="visible")
        badge.click()

        assert page.locator(".nx-moved-badge").count() == 0
        assert orig_row.locator(".nx-dataset-col").count() == orig_count

    def test_undo_all_moves_reverts_every_pending_move(self, annotator_page):
        """The 'Undo all moves' button removes all pending-move badges."""
        page = annotator_page
        self._select_first_and_move_to_new(page)

        undo_all = page.locator("#nx-undo-all-moves")
        undo_all.wait_for(state="visible")
        undo_all.click()

        assert page.locator(".nx-moved-badge").count() == 0


# ===========================================================================
# Shift-click range selection
# ===========================================================================


class TestShiftClickSelection:
    """Shift-clicking a second checkbox selects every card between the two."""

    def test_shift_click_selects_range(self, annotator_page):
        """Clicking the first checkbox then shift-clicking the third checks all three."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() < 3:
            pytest.skip("Need at least 3 datasets for range-selection test")
        page.locator(".nx-select-cb").first.click()
        page.locator(".nx-select-cb").nth(2).click(modifiers=["Shift"])
        assert page.locator(".nx-select-cb:checked").count() == 3


# ===========================================================================
# Move persistence (round-trip save)
# ===========================================================================


class TestMovePersistence:
    """A dataset move survives a save and is reflected in the reloaded annotator."""

    def test_save_with_pending_move_succeeds(self, annotator_page, base_url, test_record_id):
        """Saving with a pending move redirects to the detail page without an error."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() == 0:
            pytest.skip("No datasets to move on this record")

        new_seqno = _add_new_activity(page)
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-dropdown-btn").wait_for(state="visible")
        page.locator("#nx-move-dropdown-btn").click()
        page.locator(f"#nx-move-dropdown [data-seqno='{new_seqno}']").click()

        page.locator("#annotate-save-btn").click()
        page.wait_for_load_state("networkidle")

        assert f"id={test_record_id}" in page.url
        assert "error" not in page.url


# ===========================================================================
# Activity sample assignment
# ===========================================================================


class TestActivitySampleAssignment:
    """Assign a sample to an activity via the header dropdown."""

    def test_assigning_sample_marks_form_dirty(self, annotator_page):
        """Selecting a sample in an activity dropdown reveals the toolbar."""
        page = annotator_page
        if page.locator(".nx-activity-sample").count() == 0:
            pytest.skip("No activity sample dropdowns on this record")

        _add_sample(page, "Assignment Test")
        page.locator(".nx-activity-sample").first.select_option(label="Assignment Test")
        page.locator("#nx-move-toolbar").wait_for(state="visible")
        assert page.locator("#nx-move-toolbar").is_visible()

    def test_assignment_appears_in_pending_changes_modal(self, annotator_page):
        """Changing an activity's sample appears under 'Sample Assignments' in the modal."""
        page = annotator_page
        if page.locator(".nx-activity-sample").count() == 0:
            pytest.skip("No activity sample dropdowns on this record")

        _add_sample(page, "Assignment Modal")
        page.locator(".nx-activity-sample").first.select_option(label="Assignment Modal")

        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        # inner_text() reflects CSS text-transform; compare case-insensitively.
        body = page.locator("#nx-pending-changes-body").inner_text().lower()
        assert "sample assignments" in body
        assert "assignment modal" in body


# ===========================================================================
# Pending-changes modal content
# ===========================================================================


class TestPendingChangesModalContent:
    """The pending-changes modal lists the correct sections for each type of edit."""

    def test_title_change_shown_in_modal(self, annotator_page):
        """A title edit appears as a 'Record Title' section with old and new values."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Modal Title Test")
        inp.press("Enter")

        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        # inner_text() reflects CSS text-transform; compare case-insensitively.
        body = page.locator("#nx-pending-changes-body").inner_text().lower()
        assert "record title" in body
        assert "modal title test" in body

    def test_description_change_shown_in_modal(self, annotator_page):
        """Editing a textarea description appears as a 'Dataset Descriptions' section."""
        page = annotator_page
        if page.locator(".annotate-textarea").count() == 0:
            pytest.skip("No dataset textareas on this record")
        page.locator(".annotate-textarea").first.fill("Pending changes modal desc")
        # Textarea input does not auto-trigger updateToolbar; call it explicitly.
        page.evaluate("window.nxUpdateToolbar()")
        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        assert "dataset descriptions" in page.locator("#nx-pending-changes-body").inner_text().lower()

    def test_added_sample_shown_in_modal(self, annotator_page):
        """An added sample appears under 'Samples' with an 'Added' badge."""
        page = annotator_page
        _add_sample(page, "Pending Sample")
        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        body = page.locator("#nx-pending-changes-body").inner_text().lower()
        assert "samples" in body
        assert "pending sample" in body

    def test_added_activity_shown_in_modal(self, annotator_page):
        """Adding an activity appears under 'Activities' with an 'Added' badge."""
        page = annotator_page
        page.locator("#nx-add-activity-btn").click()
        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        assert "activities" in page.locator("#nx-pending-changes-body").inner_text().lower()

    def test_pending_move_shown_in_modal(self, annotator_page):
        """Moving a dataset appears under 'Pending Moves' in the modal."""
        page = annotator_page
        if page.locator(".nx-select-cb").count() == 0:
            pytest.skip("No datasets to move on this record")

        new_seqno = _add_new_activity(page)
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-dropdown-btn").wait_for(state="visible")
        page.locator("#nx-move-dropdown-btn").click()
        page.locator(f"#nx-move-dropdown [data-seqno='{new_seqno}']").click()

        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        assert "pending moves" in page.locator("#nx-pending-changes-body").inner_text().lower()


# ===========================================================================
# Title inline-edit edge cases
# ===========================================================================


class TestTitleEditBehavior:
    """Keyboard and focus behavior of the inline title editor."""

    def test_escape_cancels_edit_without_marking_dirty(self, annotator_page):
        """Pressing Escape discards the typed value and does not mark the bar dirty."""
        page = annotator_page
        original = page.locator("#nx-title-display").inner_text()
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Should Not Be Saved")
        inp.press("Escape")
        inp.wait_for(state="hidden")

        assert page.locator("#nx-title-bar.nx-title-dirty").count() == 0
        assert page.locator("#nx-title-display").inner_text() == original

    def test_blur_commits_edit_and_marks_dirty(self, annotator_page):
        """Clicking away from the title input saves the new value and marks dirty."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Blur Committed Title")
        page.locator("body").click()
        inp.wait_for(state="hidden")

        assert page.locator("#nx-title-display").inner_text() == "Blur Committed Title"
        assert page.locator("#nx-title-bar.nx-title-dirty").count() > 0


# ===========================================================================
# Keyboard shortcut and toolbar save button
# ===========================================================================


class TestKeyboardAndToolbar:
    """Ctrl+Enter keyboard shortcut and the toolbar Save button both submit the form."""

    def test_ctrl_enter_submits_form(self, annotator_page, base_url, test_record_id):
        """Pressing Ctrl+Enter saves the form and redirects to the detail page."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Ctrl Enter Save")
        inp.press("Enter")
        page.keyboard.press("Control+Enter")
        page.wait_for_load_state("networkidle")
        assert f"id={test_record_id}" in page.url

    def test_toolbar_save_button_submits_form(self, annotator_page, base_url, test_record_id):
        """Clicking the toolbar's Save button submits the form."""
        page = annotator_page
        page.locator("#nx-title-edit-btn").click()
        inp = page.locator("#nx-title-bar input[type='text']")
        inp.wait_for(state="visible")
        inp.fill("Toolbar Save Button")
        inp.press("Enter")
        page.locator("#nx-toolbar-save-btn").wait_for(state="visible")
        page.locator("#nx-toolbar-save-btn").click()
        page.wait_for_load_state("networkidle")
        assert f"id={test_record_id}" in page.url

    def test_help_modal_opens(self, annotator_page):
        """Clicking the '?' button opens the help modal."""
        page = annotator_page
        page.locator("button[data-bs-target='#annotate-help-modal']").click()
        page.locator("#annotate-help-modal").wait_for(state="visible")
        assert page.locator("#annotate-help-modal").is_visible()

    def test_cancel_navigates_to_detail_page(self, annotator_page, test_record_id):
        """Clicking Cancel navigates to the record detail page."""
        page = annotator_page
        page.locator("a.btn.btn-outline-secondary:has-text('Cancel')").click()
        page.wait_for_load_state("networkidle")
        assert f"id={test_record_id}" in page.url


# ===========================================================================
# Dataset card status-dot color coding
# ===========================================================================


class TestCardStatusDot:
    """Typing in a textarea updates the card's data-status attribute in real time."""

    def test_typing_in_textarea_marks_card_unsaved(self, annotator_page):
        """Filling a textarea changes its card's data-status to 'unsaved'."""
        page = annotator_page
        if page.locator(".annotate-textarea").count() == 0:
            pytest.skip("No dataset textareas on this record")
        page.locator(".annotate-textarea").first.fill("Status dot test content")
        assert page.locator(".annotate-card[data-status='unsaved']").count() > 0

    def test_restoring_original_text_clears_unsaved_status(self, annotator_page):
        """Restoring a textarea to its original value reverts data-status."""
        page = annotator_page
        ta = page.locator(".annotate-textarea").first
        if ta.count() == 0:
            pytest.skip("No dataset textareas on this record")
        original = ta.get_attribute("data-original") or ""
        ta.fill("Temporary change")
        ta.fill(original)
        expected = "annotated" if original.strip() else "empty"
        assert page.locator(f".annotate-card[data-status='{expected}']").count() > 0


# ===========================================================================
# Error banners
# ===========================================================================


class TestErrorBanners:
    """Error conditions render the appropriate alert banners."""

    def test_error_query_param_shows_danger_alert(self, annotator_page, base_url, test_record_id):
        """Navigating to the annotator with ?error=1 renders the error alert."""
        page = annotator_page
        page.goto(f"{base_url}/annotate/{test_record_id}/?error=1")
        page.wait_for_load_state("networkidle")
        assert page.locator(".alert-danger").count() > 0
