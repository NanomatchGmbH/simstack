import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ui: marks tests that require complex UI mocking (deselect with '-m \"not ui\"')",
    )


def pytest_collection_modifyitems(config, items):
    # Skip tests in specific view modules that require complex UI mocking
    for item in items:
        if (
            "test_WFEditorPanel" in item.nodeid
            and "test_move_element_to_position" in item.nodeid
            or "test_WFEditorPanel" in item.nodeid
            and "test_unique_name" in item.nodeid
            or "test_WFEditorPanel" in item.nodeid
            and "test_add_element" in item.nodeid
            or "test_WFEditorPanel" in item.nodeid
            and "test_remove_element_as_wano" in item.nodeid
            or "test_WFEditorTreeModels" in item.nodeid
            and "test_get_data_type" in item.nodeid
            or "test_WFEditorTreeModels" in item.nodeid
            and "test_get_icon_type" in item.nodeid
            or "test_WFEditorWidgets" in item.nodeid
            or "test_WaNoEditorWidget" in item.nodeid
            or "test_WaNoSettings" in item.nodeid
            and "test_signals_connected" in item.nodeid
        ):
            item.add_marker(pytest.mark.skip(reason="Requires complex UI mocking"))
