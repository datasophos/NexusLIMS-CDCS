"""Shared utilities for E2E tests."""

from pathlib import Path

import requests
from playwright.sync_api import expect

_REPO_ROOT = Path(__file__).resolve().parents[2]

RESETTABLE_RECORDS = {
    "Example record": _REPO_ROOT / "deployment/test-data/example_record.xml",
    "Example record large": _REPO_ROOT / "deployment/test-data/example_record_large.xml",
    "Example record multisample": _REPO_ROOT
    / "deployment/test-data/example_record_multisample.xml",
    "Example record curation": _REPO_ROOT
    / "deployment/test-data/example_record_curation.xml",
}


def fetch_all_records(cookies, base_url):
    """Fetch all records from the CDCS REST API, following pagination."""
    results = []
    url = f"{base_url}/rest/data/"
    while url:
        resp = requests.get(
            url,
            cookies=cookies,
            verify=False,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        results.extend(data.get("results", []))
        url = data.get("next")
    return results


def add_sample(page, name, pid="", description="", elements=()):
    """Add a sample via the annotator modal and wait for it to appear in the list."""
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
    save_btn = page.locator("#nx-sample-modal-save")
    expect(save_btn).to_be_enabled()
    save_btn.click()
    expect(page.locator("#nx-sample-modal")).to_be_hidden()
    expect(page.locator("#nx-samples-list")).to_contain_text(name)


def add_new_activity(page):
    """Click 'Add Activity' and return the seqno of the newly added row."""
    before = page.locator(".nx-sortable-activity").count()
    page.locator("#nx-add-activity-btn").click()
    expect(page.locator(".nx-sortable-activity")).to_have_count(before + 1)
    return page.locator(".nx-sortable-activity").last.get_attribute("data-seqno")


def reset_records(cookies, base_url, by_title=None):
    """Patch each resettable record back to its canonical XML content.

    If by_title is given (a pre-built {title: id} map), use it directly.
    This is important when calling after annotator tests have mutated the
    CDCS metadata title -- re-fetching would no longer find the original titles.
    """
    if by_title is None:
        records = fetch_all_records(cookies, base_url)
        by_title = {r["title"]: r["id"] for r in records if isinstance(r, dict)}
    csrf = cookies.get("csrftoken", "")
    headers = {"X-CSRFToken": csrf, "Referer": base_url}
    for title, xml_path in RESETTABLE_RECORDS.items():
        rid = by_title.get(title)
        if rid is None or not xml_path.exists():
            continue
        resp = requests.patch(
            f"{base_url}/rest/data/{rid}/",
            cookies=cookies,
            verify=False,
            headers=headers,
            json={"xml_content": xml_path.read_text(encoding="utf-8")},
        )
        resp.raise_for_status()
