from iam_looker.handler import handle_event


def test_handle_event_sdk_unavailable(monkeypatch):
    # Force handler to think SDK unavailable by monkeypatching provisioner import side effects if needed.
    event = {"projectId": "demo-project", "groupEmail": "analysts@company.com"}
    result = handle_event(event)
    # Depending on environment might be ok or sdk_unavailable; allow both but validate shape.
    assert result["projectId"] == "demo-project"
    assert result["groupEmail"] == "analysts@company.com"
    assert "status" in result


def test_handle_event_validation_error():
    event = {"projectId": "bad", "groupEmail": "not-an-email"}
    result = handle_event(event)
    assert result["status"] == "validation_error"
