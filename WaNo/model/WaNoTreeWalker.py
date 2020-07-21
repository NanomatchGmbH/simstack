from TreeWalker.TreeWalker import TreeWalker

class WaNoTreeWalker(TreeWalker):
    @staticmethod
    def _isdict(myobject) -> bool:
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike
        return isinstance(myobject, WaNoModelDictLike) or \
               isinstance(myobject, OrderedDictIterHelper) or \
               isinstance(myobject, MultipleOfModel)

    @staticmethod
    def _islist(myobject) -> bool:
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike
        return isinstance(myobject, WaNoModelListLike) or isinstance(myobject, MultipleOfModel)


class ViewCollector:
    def __init__(self):
        self._views_by_path = {}

    def get_views_by_path(self):
        return self._views_by_path

    def _get_mypath_treewalker(self, call_info):
        tw_paths = call_info["treewalker_paths"]
        tw: TreeWalker = call_info["treewalker"]
        abspath = tw_paths.abspath
        if abspath is None:
            mypath = tuple("")
        else:
            mypath = tuple(abspath)
        return mypath, tw

    def assemble_views(self, subdict, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike

        if isinstance(subdict, OrderedDictIterHelper):
            return

        mypath,tw = self._get_mypath_treewalker(call_info)

        ViewClass = subdict.get_view_class()

        vc = ViewClass()
        self._views_by_path[mypath] = vc
        subdict.set_view(vc)
        vc.set_model(subdict)
        return None

    def assemble_views_parenter(self, subdict, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike

        if isinstance(subdict, OrderedDictIterHelper):
            return

        mypath,tw = self._get_mypath_treewalker(call_info)
        vc = subdict.view
        if mypath != tuple(""):
            parent = tw.resolve(mypath[:-1])
            vc.set_parent(parent.view)
        return None

    def data_visitor_view_assembler(self, data, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike

        if isinstance(data, OrderedDictIterHelper):
            return data
        mypath, tw = self._get_mypath_treewalker(call_info)

        ViewClass = data.get_view_class()
        vc = ViewClass()
        self._views_by_path[mypath] = vc
        data.set_view(vc)
        vc.set_model(data)
        return data

    def data_visitor_view_parenter(self, data, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike

        if isinstance(data, OrderedDictIterHelper):
            return data
        mypath, tw = self._get_mypath_treewalker(call_info)

        vc = data.view

        if mypath != tuple(""):
            checktuple = mypath[:-1]
            parent = tw.resolve(mypath[:-1])
            while isinstance(parent, OrderedDictIterHelper):
                checktuple = checktuple[:-1]
                parent = tw.resolve(checktuple)
            vc.set_parent(parent.view)
        return data