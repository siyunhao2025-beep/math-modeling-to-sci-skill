from __future__ import annotations

from audit_repo import audit


def test_all_registered_repository_risks_are_guarded():
    results = audit()
    failed = [item for item in results if item["status"] != "PASS"]
    assert not failed, failed
    assert len(results) == 18
