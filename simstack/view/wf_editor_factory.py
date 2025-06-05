from .wf_editor_models import (
    ForEachModel,
    AdvancedForEachModel,
    IfModel,
    WhileModel,
    VariableModel,
    ParallelModel,
    SubWFModel,
)
from .wf_editor_views import (
    ForEachView,
    AdvancedForEachView,
    IfView,
    WhileView,
    VariableView,
    ParallelView,
    SubWorkflowView,
)


class ControlFactory(object):
    n_t_c = {
        "ForEach": (ForEachModel, ForEachView),
        "AdvancedFor": (AdvancedForEachModel, AdvancedForEachView),
        "If": (IfModel, IfView),
        "While": (WhileModel, WhileView),
        "Variable": (VariableModel, VariableView),
        "Parallel": (ParallelModel, ParallelView),
        "SubWorkflow": (SubWFModel, SubWorkflowView),
    }

    @classmethod
    def name_to_class(cls, name):
        return cls.n_t_c[name]

    @classmethod
    def construct(cls, name, qt_parent, logical_parent, editor, wf_root):
        modelc, viewc = cls.name_to_class(name)
        view = viewc(qt_parent=qt_parent, logical_parent=logical_parent)
        model = modelc(editor=editor, view=view, wf_root=wf_root)
        view.set_model(model)
        view.init_from_model()
        return model, view