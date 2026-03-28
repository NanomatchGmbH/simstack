"""Regression test for MultipleOfModel.add_item() spec-based path ignoring build_view.

When a WaNo with WaNoMultipleOf fields is loaded with Qt views and then a delta
(wano_configuration.json) is applied that expands the number of items, the
spec-based add_item() path was not creating Qt views for the new child models.
This caused MultipleOfView.init_from_model() to crash with:
    AttributeError: 'NoneType' object has no attribute 'get_widget'
"""
from pathlib import Path

import pytest

BROKEN_WF = Path(__file__).parents[2] / "broken_wf" / "Complex_WF"
WANOS_DIR = BROKEN_WF / "wanos"
WANO_CONFIGS_DIR = BROKEN_WF / "wano_configurations"

# UUID → WaNo folder mapping from broken_wf
_WANOS = {
    "2ca2a7af-9529-45e3-b8f8-bc80a0ecb328": "lightforge2",
    "54b08f75-d766-43c9-bf35-7b870d31c6df": "Deposit4",
}


@pytest.mark.parametrize("uuid,wano_name", list(_WANOS.items()))
def test_apply_delta_after_view_construction_no_crash(qtbot, uuid, wano_name):
    """Applying a delta with extra MultipleOf items must not crash when views exist.

    Regression test for the bug where MultipleOfModel.add_item() in the
    spec-based path ignored build_view=True and created child models without
    Qt views, causing MultipleOfView.init_from_model() to raise AttributeError.
    """
    from SimStackServer.WaNo.WaNoFactory import wano_constructor_helper
    from SimStackServer.WaNo.WaNoModels import WaNoModelRoot
    from simstack.view.WaNoViews import WanoQtViewRoot

    wano_dir = WANOS_DIR / wano_name
    delta_dir = WANO_CONFIGS_DIR / uuid

    # Build model + views
    wmr = WaNoModelRoot(wano_dir_root=wano_dir)
    wmr.set_view_class(WanoQtViewRoot)
    wmr, rootview = wano_constructor_helper(wmr)
    qtbot.addWidget(rootview.get_widget())

    # Apply the stored delta — this triggers apply_delta → add_item(build_view=True)
    # which previously crashed with AttributeError: 'NoneType' has no 'get_widget'
    wmr.read(delta_dir)
