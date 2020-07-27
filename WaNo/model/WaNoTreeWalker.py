from TreeWalker.TreeWalker import TreeWalker


class WaNoTreeWalker(TreeWalker):
    @staticmethod
    def _isdict(myobject) -> bool:
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike
        if hasattr(myobject, "dictlike"):
            return myobject.dictlike
        return isinstance(myobject, WaNoModelDictLike) or \
               isinstance(myobject, OrderedDictIterHelper) or \
               isinstance(myobject, MultipleOfModel)

    @staticmethod
    def _islist(myobject) -> bool:
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        from WaNo.model.WaNoModels import WaNoModelDictLike, MultipleOfModel, WaNoModelListLike
        if hasattr(myobject, "listlike"):
            return myobject.listlike
        return isinstance(myobject, WaNoModelListLike) or isinstance(myobject, MultipleOfModel)


class ViewCollector:
    def __init__(self):
        self._views_by_path = {}
        self._wano_model_root = None
        self._start_path = []

    def get_views_by_path(self):
        return self._views_by_path

    def set_wano_model_root(self, wano_model_root):
        self._wano_model_root = wano_model_root

    def set_start_path(self, start_path):
        self._start_path = start_path

    def _get_mypath_treewalker(self, call_info):
        tw_paths = call_info["treewalker_paths"]
        tw: TreeWalker = call_info["treewalker"]
        abspath = tw_paths.abspath
        if abspath is None:
            listpath = []
            mypath = (*listpath,)
        else:
            listpath = abspath
            mypath = (*listpath,)
        return mypath, tw

    def root_setter_subdict(self, subdict, call_info):
        assert self._wano_model_root is not None, "WaNoModelRoot has to be set prior."
        from WaNo.model.WaNoModels import MultipleOfModel
        if hasattr(subdict, "set_root"):
            subdict.set_root(self._wano_model_root)

    def root_setter_data(self, data, call_info):
        assert self._wano_model_root is not None, "WaNoModelRoot has to be set prior."
        from WaNo.model.WaNoModels import MultipleOfModel
        if hasattr(data, "set_root"):
            data.set_root(self._wano_model_root)

    def path_setter_subdict(self, subdict, call_info):
        path, _ = self._get_mypath_treewalker(call_info)
        if hasattr(subdict, "set_path"):
            mp = ".".join(self._start_path + [str(p) for p in path])
            subdict.set_path(mp)

    def path_setter_data(self, data, call_info):
        path, _ = self._get_mypath_treewalker(call_info)
        if hasattr(data, "set_path"):
            mp = ".".join(self._start_path + [str(p) for p in path])
            data.set_path(mp)

    def assemble_views(self, subdict, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        if isinstance(subdict, OrderedDictIterHelper):
            return None

        mypath,tw = self._get_mypath_treewalker(call_info)

        ViewClass = subdict.get_view_class()

        vc = ViewClass()
        self._views_by_path[mypath] = vc
        subdict.set_view(vc)
        vc.set_model(subdict)
        return None

    def _skip_level(self, myobject):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
        skipmodels = [OrderedDictIterHelper]
        for mt in skipmodels:
            if isinstance(myobject, mt):
                return True
        return False

    def assemble_views_parenter(self, subdict, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper


        if isinstance(subdict, OrderedDictIterHelper):
            return None

        mypath,tw = self._get_mypath_treewalker(call_info)
        vc = subdict.view
        cutnum = 1
        if mypath != tuple():
            parent = tw.resolve(mypath[:-cutnum])
            while self._skip_level(parent):
                cutnum+=1
                parent = tw.resolve(mypath[:-cutnum])
            #print(mypath)
            vc.set_parent(parent.view)
            subdict.set_parent(parent)
        return None

    def data_visitor_view_assembler(self, data, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
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
            data.set_parent(parent)
        return data


    def data_visitor_model_parenter(self, data, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper

        if isinstance(data, OrderedDictIterHelper):
            return data
        mypath, tw = self._get_mypath_treewalker(call_info)

        if mypath != tuple(""):
            checktuple = mypath[:-1]
            parent = tw.resolve(mypath[:-1])
            while isinstance(parent, OrderedDictIterHelper):
                checktuple = checktuple[:-1]
                parent = tw.resolve(checktuple)
            data.set_parent(parent)
        return data

    def assemble_model_parenter(self, subdict, call_info):
        from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper


        if isinstance(subdict, OrderedDictIterHelper):
            return None

        mypath,tw = self._get_mypath_treewalker(call_info)
        cutnum = 1
        if mypath != tuple():
            parent = tw.resolve(mypath[:-cutnum])
            while self._skip_level(parent):
                cutnum+=1
                parent = tw.resolve(mypath[:-cutnum])
            #print(mypath)
            subdict.set_parent(parent)
        return None