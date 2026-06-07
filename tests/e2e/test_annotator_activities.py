"""E2E tests for activity management, dataset selection, batch moves, and related UI.

None of the tests in this module save to CDCS, so they are safe to run in parallel
with other annotator test modules.
"""

from tests.e2e.helpers import add_sample, add_new_activity


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
        assert page.locator(".nx-insert-activity-below").count() > 0, (
            "Canonical annotator record has no insert-below buttons"
        )
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
        assert nonempty, "Canonical annotator record has no activities with datasets"
        for btn in nonempty:
            assert btn.is_disabled()

    def test_activity_labels_are_sequential_after_add(self, annotator_page):
        """After adding an activity, all labels read 'Activity 1', 'Activity 2', …"""
        page = annotator_page
        page.locator("#nx-add-activity-btn").click()
        labels = page.locator(".nx-activity-label").all()
        for i, lbl in enumerate(labels, start=1):
            assert f"Activity {i}" in lbl.text_content()


class TestDatasetSelection:
    """Checkbox selection shows the batch toolbar and maintains a count badge."""

    def test_checking_dataset_makes_toolbar_visible(self, annotator_page):
        """Checking a dataset checkbox reveals the move toolbar."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() > 0, (
            "Canonical annotator record has no dataset checkboxes"
        )
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-toolbar").wait_for(state="visible")
        assert page.locator("#nx-move-toolbar").is_visible()

    def test_selection_count_badge_updates(self, annotator_page):
        """Checking two datasets shows '2' in the selection count badge."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() >= 2, (
            "Canonical annotator record has fewer than 2 dataset checkboxes"
        )
        page.locator(".nx-select-cb").nth(0).click()
        page.locator(".nx-select-cb").nth(1).click()
        count_el = page.locator("#nx-toolbar-sel-count")
        count_el.wait_for(state="visible")
        assert "2" in count_el.inner_text()

    def test_clear_selection_unchecks_all_datasets(self, annotator_page):
        """Clicking 'Clear selection' unchecks every dataset card."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() > 0, (
            "Canonical annotator record has no dataset checkboxes"
        )
        page.locator(".nx-select-cb").first.click()
        clear_btn = page.locator("#nx-clear-selection")
        clear_btn.wait_for(state="visible")
        clear_btn.click()
        assert page.locator(".nx-select-cb:checked").count() == 0


class TestBatchMove:
    """Select datasets and move them via the toolbar dropdown or undo controls."""

    def _select_first_and_move_to_new(self, page):
        assert page.locator(".nx-select-cb").count() > 0, (
            "Canonical annotator record has no dataset checkboxes"
        )
        new_seqno = add_new_activity(page)
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
        assert orig_count > 0, "Canonical annotator record has no datasets in first activity"

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


class TestShiftClickSelection:
    """Shift-clicking a second checkbox selects every card between the two."""

    def test_shift_click_selects_range(self, annotator_page):
        """Clicking the first checkbox then shift-clicking the third checks all three."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() >= 3, (
            "Canonical annotator record has fewer than 3 dataset checkboxes"
        )
        page.locator(".nx-select-cb").first.click()
        page.locator(".nx-select-cb").nth(2).click(modifiers=["Shift"])
        assert page.locator(".nx-select-cb:checked").count() == 3


class TestActivitySampleAssignment:
    """Assign a sample to an activity via the header dropdown."""

    def test_assigning_sample_marks_form_dirty(self, annotator_page):
        """Selecting a sample in an activity dropdown reveals the toolbar."""
        page = annotator_page
        assert page.locator(".nx-activity-sample").count() > 0, (
            "Canonical annotator record has no activity sample dropdowns"
        )

        add_sample(page, "Assignment Test")
        page.locator(".nx-activity-sample").first.select_option(label="Assignment Test")
        page.locator("#nx-move-toolbar").wait_for(state="visible")
        assert page.locator("#nx-move-toolbar").is_visible()

    def test_assignment_appears_in_pending_changes_modal(self, annotator_page):
        """Changing an activity's sample appears under 'Sample Assignments' in the modal."""
        page = annotator_page
        assert page.locator(".nx-activity-sample").count() > 0, (
            "Canonical annotator record has no activity sample dropdowns"
        )

        add_sample(page, "Assignment Modal")
        page.locator(".nx-activity-sample").first.select_option(label="Assignment Modal")

        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        body = page.locator("#nx-pending-changes-body").inner_text().lower()
        assert "sample assignments" in body
        assert "assignment modal" in body


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
        body = page.locator("#nx-pending-changes-body").inner_text().lower()
        assert "record title" in body
        assert "modal title test" in body

    def test_description_change_shown_in_modal(self, annotator_page):
        """Editing a textarea description appears as a 'Dataset Descriptions' section."""
        page = annotator_page
        assert page.locator(".annotate-textarea").count() > 0, (
            "Canonical annotator record has no dataset textareas"
        )
        page.locator(".annotate-textarea").first.fill("Pending changes modal desc")
        page.evaluate("window.nxUpdateToolbar()")
        page.locator("#nx-view-changes-btn").wait_for(state="visible")
        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        assert "dataset descriptions" in page.locator(
            "#nx-pending-changes-body"
        ).inner_text().lower()

    def test_added_sample_shown_in_modal(self, annotator_page):
        """An added sample appears under 'Samples' with an 'Added' badge."""
        page = annotator_page
        add_sample(page, "Pending Sample")
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
        assert "activities" in page.locator(
            "#nx-pending-changes-body"
        ).inner_text().lower()

    def test_pending_move_shown_in_modal(self, annotator_page):
        """Moving a dataset appears under 'Pending Moves' in the modal."""
        page = annotator_page
        assert page.locator(".nx-select-cb").count() > 0, (
            "Canonical annotator record has no datasets to move"
        )

        new_seqno = add_new_activity(page)
        page.locator(".nx-select-cb").first.click()
        page.locator("#nx-move-dropdown-btn").wait_for(state="visible")
        page.locator("#nx-move-dropdown-btn").click()
        page.locator(f"#nx-move-dropdown [data-seqno='{new_seqno}']").click()

        page.locator("#nx-view-changes-btn").click()
        page.locator("#nx-pending-changes-modal").wait_for(state="visible")
        assert "pending moves" in page.locator(
            "#nx-pending-changes-body"
        ).inner_text().lower()


class TestCardStatusDot:
    """Typing in a textarea updates the card's data-status attribute in real time."""

    def test_typing_in_textarea_marks_card_unsaved(self, annotator_page):
        """Filling a textarea changes its card's data-status to 'unsaved'."""
        page = annotator_page
        assert page.locator(".annotate-textarea").count() > 0, (
            "Canonical annotator record has no dataset textareas"
        )
        page.locator(".annotate-textarea").first.fill("Status dot test content")
        assert page.locator(".annotate-card[data-status='unsaved']").count() > 0

    def test_restoring_original_text_clears_unsaved_status(self, annotator_page):
        """Restoring a textarea to its original value reverts data-status."""
        page = annotator_page
        ta = page.locator(".annotate-textarea").first
        assert ta.count() > 0, "Canonical annotator record has no dataset textareas"
        original = ta.get_attribute("data-original") or ""
        ta.fill("Temporary change")
        ta.fill(original)
        expected = "annotated" if original.strip() else "empty"
        assert page.locator(f".annotate-card[data-status='{expected}']").count() > 0
