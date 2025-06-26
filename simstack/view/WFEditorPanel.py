# WFEditorPanel.py - Main entry point for workflow editor panel components
# This file has been refactored to import from separate module files for better maintainability

# Import all base utilities and constants
from .wf_editor_base import (
    widgetColors,
    linuxjoin,
    DragDropTargetTracker,
)

# Import all widget components
from .wf_editor_widgets import (
    SubmitType,
    WFWaNoWidget,
    WFItemListInterface,
)

# Import all model components
from .wf_editor_models import (
    WFItemModel,
    SubWFModel,
    WhileModel,
    IfModel,
    ParallelModel,
    ForEachModel,
    AdvancedForEachModel,
    WFModel,
    VariableModel,
    merge_path,
)

# Import all view components
from .wf_editor_views import (
    SubWorkflowView,
    WorkflowView,
    WFTabsWidget,
    WFFileName,
    WFControlWithTopMiddleAndBottom,
    AdvancedForEachView,
    ForEachView,
    ParallelView,
    IfView,
    VariableView,
    WhileView,
)

# Import factory
from .wf_editor_factory import ControlFactory

# Re-export all classes to maintain backwards compatibility
__all__ = [
    # Base utilities
    "widgetColors",
    "linuxjoin",
    "DragDropTargetTracker",
    # Widget components
    "SubmitType",
    "WFWaNoWidget",
    "WFItemListInterface",
    # Model components
    "WFItemModel",
    "SubWFModel",
    "WhileModel",
    "IfModel",
    "ParallelModel",
    "ForEachModel",
    "AdvancedForEachModel",
    "WFModel",
    "VariableModel",
    "merge_path",
    # View components
    "SubWorkflowView",
    "WorkflowView",
    "WFTabsWidget",
    "WFFileName",
    "WFControlWithTopMiddleAndBottom",
    "AdvancedForEachView",
    "ForEachView",
    "ParallelView",
    "IfView",
    "VariableView",
    "WhileView",
    # Factory
    "ControlFactory",
]
