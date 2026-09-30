"""Phase 31 — Fee Administration UI & Portal Manager Unit Tests.

Verifies:
1. CSS and JS asset existence and key selectors.
2. FeeAdminTab enum & supported tabs retrieval.
3. FeeAdminSummary calculation & dataclass serialization.
4. Outstanding report generation and CSV export structure.
"""

from pathlib import Path
import pytest

from central_platform.portals.fee_admin import (
    FeeAdminTab,
    FeeAdminSummary,
    OutstandingReportItem,
    FeeAdminController,
)


def test_fee_admin_assets_exist():
    css_path = Path("app/ui/design_system/fee_admin.css")
    js_path = Path("app/ui/design_system/fee_admin.js")

    assert css_path.exists(), "fee_admin.css must exist"
    assert js_path.exists(), "fee_admin.js must exist"

    css_content = css_path.read_text(encoding="utf-8")
    assert ".fee-admin-container" in css_content
    assert ".fee-table" in css_content

    js_content = js_path.read_text(encoding="utf-8")
    assert "GayatriFeeAdmin" in js_content


def test_fee_admin_tab_enum_and_supported_tabs():
    assert len(FeeAdminTab) == 6
    tabs = FeeAdminController.get_supported_tabs()
    assert len(tabs) == 6
    tab_keys = [t["tab"] for t in tabs]
    assert "fee_setup" in tab_keys
    assert "monthly_billing" in tab_keys
    assert "outstanding_reports" in tab_keys


def test_fee_admin_summary():
    summary = FeeAdminController.get_fee_admin_summary(org_id="org_test_01")
    assert isinstance(summary, FeeAdminSummary)
    assert summary.org_id == "org_test_01"
    assert summary.total_collected > 0
    d = summary.to_dict()
    assert "total_pending" in d
    assert "total_overdue" in d


def test_outstanding_reports_and_csv_export():
    items = FeeAdminController.get_outstanding_reports(org_id="org_test_01")
    assert len(items) >= 1
    first_item = items[0]
    assert isinstance(first_item, OutstandingReportItem)
    assert first_item.student_name == "Aarav Sharma"

    csv_data = FeeAdminController.export_outstanding_report_csv(org_id="org_test_01")
    assert "Student ID,Student Name,Grade" in csv_data
    assert "Aarav Sharma" in csv_data
    assert "15000.00" in csv_data
