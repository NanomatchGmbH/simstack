#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


import Qt.QtCore as QtCore
import Qt.QtGui as QtGui

# requires python 2.7,
try:
    import collections
except ImportError as e:
    print("OrderedDict requires Python 2.7 or higher or Python 3.1 or higher")
    raise e

from WaNo.model.AbstractWaNoModel import AbstractWanoModel
import WaNo.WaNoFactory
from lxml import etree
import copy

from Qt import QtCore
import yaml
import os
import sys
import shutil
import ast

from jinja2 import Template, FileSystemLoader, Environment

from WaNo.view.PropertyListView import ResourceTableModel,ImportTableModel,ExportTableModel

from pyura.pyura.WorkflowXMLConverter import JSDLtoXML

import numpy as np



class WaNoModelDictLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelDictLike, self).__init__(*args, **kwargs)
        self.wano_dict = collections.OrderedDict()
        self.xml = kwargs["xml"]

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self.root_model, self, self.full_path)
            self.wano_dict[child.attrib['name']] = model

    def __getitem__(self, item):
        return self.wano_dict[item]

    def keys(self):
        return self.wano_dict.keys()

    def values(self):
        return self.wano_dict.values()

    def items(self):
        return self.wano_dict.items()

    def __iter__(self):
        return iter(self.wano_dict)

    def get_data(self):
        return self.wano_dict

    def set_data(self, wano_dict):
        self.wano_dict = wano_dict

    def items(self):
        return self.wano_dict.items()

    def wanos(self):
        return self.wano_dict.values()

    def get_type_str(self):
        return None

    def __repr__(self):
        return repr(self.wano_dict)

    def update_xml(self):
        for wano in self.wano_dict.values():
            wano.update_xml()


class WaNoChoiceModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoChoiceModel,self).__init__(*args,**kwargs)

        self.xml = kwargs["xml"]
        self.choices = []
        self.chosen=0
        for child in self.xml.iter("Entry"):
            myid = int(child.attrib["id"])
            self.choices.append(child.text)
            assert(len(self.choices) == myid + 1)
            if "chosen" in child.attrib:
                if child.attrib["chosen"].lower() == "true":
                    self.chosen = myid

    def __getitem__(self, item):
        return None

    def get_type_str(self):
        return "String"

    def get_data(self):
        return self.choices[self.chosen]

    @QtCore.Slot(int)
    def set_chosen(self,choice):
        self.chosen = int(choice)
        self.set_data(self.choices[self.chosen])

    def update_xml(self):
        for child in self.xml.iter("Entry"):
            myid = int(child.attrib["id"])
            if "chosen" in child.attrib:
                del child.attrib["chosen"]

            if self.chosen == myid:
                child.attrib["chosen"] = "True"

class WaNoMatrixModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoMatrixModel, self).__init__(*args, **kwargs)
        self.xml = kwargs["xml"]
        self.rows = int(self.xml.attrib["rows"])
        self.cols = int(self.xml.attrib["cols"])
        self.col_header = None
        if "col_header" in self.xml.attrib:
            self.col_header = self.xml.attrib["col_header"].split(";")
        self.row_header = None
        if "row_header" in self.xml.attrib:
            self.row_header = self.xml.attrib["row_header"].split(";")

        try:
            self.storage = self._fromstring(self.xml.text)

        except Exception as e:
            self.storage = np.zeros((self.rows, self.cols))
        print(self.storage)

    def _tostring(self, ar):
        return np.array2string(ar, separator=',')

    def _fromstring(self,stri):
        list_of_lists = ast.literal_eval(stri)
        return np.array(list_of_lists,dtype=np.float64)

    def __getitem__(self,item):
        return self._tostring(self.storage)

    def get_type_str(self):
        return None

    def update_xml(self):
        self.xml.text = self._tostring(self.storage)


class WaNoModelListLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelListLike, self).__init__(*args, **kwargs)
        self.wano_list = []
        self.xml = kwargs["xml"]
        self.listlike = True

        if "style" in self.xml.attrib:
            self.style = self.xml.attrib["style"]
        else:
            self.style = ""

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self.root_model, self, self.full_path)
            # view.set_model(model)
            self.wano_list.append(model)

    def __getitem__(self, item):
        item = int(item)
        return self.wano_list[item]

    def get_type_str(self):
        return None

    def items(self):
        return enumerate(self.wano_list)

    def wanos(self):
        return enumerate(self.wano_list)

    def update_xml(self):
        for wano in self.wano_list:
            wano.update_xml()


class MultipleOfModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(MultipleOfModel, self).__init__(*args, **kwargs)
        self.xml = kwargs["xml"]
        self.first_xml_child = None
        self.list_of_dicts = []
        self.listlike = True
        for child in self.xml:
            if self.first_xml_child is None:
                self.first_xml_child = child
            wano_temp_dict = self.parse_one_child(child)
            self.list_of_dicts.append(wano_temp_dict)

    def numitems_per_add(self):
        return len(self.first_xml_child)

    def parse_one_child(self,child):
        #A bug still exists, which allows visibility conditions to be fired prior to the existence of the model
        #but this is transient.
        wano_temp_dict = collections.OrderedDict()
        current_id = len(self.list_of_dicts)
        fp = "%s.%d"%(self.full_path,current_id)
        for cchild in child:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(cchild, self.root_model, self, fp)
            wano_temp_dict[cchild.attrib['name']] = model
        return wano_temp_dict

    def __getitem__(self, item):
        item = int(item)
        return self.list_of_dicts[item]

    def __iter__(self):
        return iter(self.list_of_dicts)

    def items(self):
        return enumerate(self.list_of_dicts)

    def __reversed__(self):
        return reversed(self.list_of_dicts)

    def get_data(self):
        return self.list_of_dicts

    def get_type_str(self):
        return None

    def set_data(self, list_of_dicts):
        self.list_of_dicts = list_of_dicts

    def delete_item(self):
        if len(self.list_of_dicts) > 1:
            self.list_of_dicts.pop()
            #print(etree.tostring(self.xml,pretty_print=True).decode("utf-8"))
            for child in reversed(self.xml):
                self.xml.remove(child)
                break
            #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
            return True
        return False

    def add_item(self):
        print("Additem called")
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        my_xml = copy.copy(self.first_xml_child)
        my_xml.attrib["id"] = str(len(self.list_of_dicts))
        self.xml.append(my_xml)
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        model_dict = self.parse_one_child(my_xml)
        WaNo.WaNoFactory.WaNoFactory.build_views()
        self.list_of_dicts.append(model_dict)
        self.root_model.datachanged_force()


    def update_xml(self):
        for wano_dict in self.list_of_dicts:
            for wano in wano_dict.values():
                wano.update_xml()

class WaNoModelRootSignal(QtCore.QObject):
    dataChanged = QtCore.Signal(int, name="dataChanged")
    def __init__(self):
        super(WaNoModelRootSignal, self).__init__()



# This is the parent class and grandfather. Children have to be unique, no lists here
class WaNoModelRoot(WaNoModelDictLike):
    dataChanged = QtCore.Signal(str, name="dataChanged")
    def exists_read_load(self,object,filename):
        if os.path.exists(filename):
            object.load(filename)
        else:
            object.make_default_list()
            object.save(filename)


    def __init__(self, *args, **kwargs):
        self.root_model = self
        self.full_xml = kwargs['xml']
        kwargs['xml'] = self.full_xml.find("WaNoRoot")
        kwargs["root_model"] = self.root_model
        kwargs["full_path"] = ""
        self.parent_wf = kwargs["parent_wf"]
        wano_dir_root = kwargs["wano_dir_root"]
        resources_fn = os.path.join(wano_dir_root, "resources.yml")
        super(WaNoModelRoot, self).__init__(*args, **kwargs)
        #WaNoModelRootSignal.emit()
        #wmrs = WaNoModelRootSignal()
        #self.dataChanged = wmrs.dataChanged

        self.resources = ResourceTableModel(parent=None,wano_parent=self)
        self.exists_read_load(self.resources, resources_fn)

        imports_fn = os.path.join(wano_dir_root, "imports.yml")
        self.import_model = ImportTableModel(parent=None,wano_parent=self)
        self.import_model.make_default_list()
        self.exists_read_load(self.import_model,imports_fn)

        exports_fn = os.path.join(wano_dir_root, "exports.yml")
        self.export_model = ExportTableModel(parent=None,wano_parent=self)
        self.export_model.make_default_list()
        self.exists_read_load(self.export_model, exports_fn)


        self.exec_command = self.full_xml.find("WaNoExecCommand").text
        self.rendered_exec_command = ""
        self.input_files = []


        self.wano_dir_root = kwargs["wano_dir_root"]
        for child in self.full_xml.findall("./WaNoInputFiles/WaNoInputFile"):
            self.input_files.append((child.attrib["logical_filename"],child.text))

        self.output_files = []
        for child in self.full_xml.findall("./WaNoOutputFiles/WaNoOutputFile"):
            self.output_files.append(child.text)

    def get_type_str(self):
        return None

    def get_resource_model(self):
        return self.resources

    def get_import_model(self):
        return self.import_model

    def get_export_model(self):
        return self.export_model

    def get_output_files(self):
        return self.output_files + [ a[0] for a in self.export_model.get_contents() ]

    def datachanged_force(self):
        self.dataChanged.emit("force")

    @staticmethod
    def construct_from_wano(filename, rootview, parent_wf):
        parser = etree.XMLParser(remove_blank_text=True,remove_comments=True)
        tree = etree.ElementTree(file=filename,parser=parser)
        root = tree.getroot()
        wano_dir_root = os.path.dirname(os.path.realpath(filename))
        modelroot = WaNoModelRoot(xml=root, view=rootview, parent_model=None, wano_dir_root=wano_dir_root,parent_wf = parent_wf)
        return modelroot

    def save_xml(self,filename):
        print("Writing to ",filename)
        self.wano_dir_root = os.path.dirname(filename)
        success = False
        try:
            with open(filename,'w') as outfile:
                outfile.write(etree.tostring(self.full_xml,pretty_print=True).decode("utf-8"))
            success = True
            resources_fn = os.path.join(self.wano_dir_root, "resources.yml")
            self.resources.save(resources_fn)

            imports_fn = os.path.join(self.wano_dir_root, "imports.yml")
            self.import_model.save(imports_fn)

            exports_fn = os.path.join(self.wano_dir_root, "exports.yml")
            self.export_model.save(exports_fn)

        except Exception as e:
            print(e)
        return success

    def wano_walker_paths(self,parent = None, path = "" , output = []):
        if (parent == None):
            parent = self
        if hasattr(parent,'items') and hasattr(parent,'listlike'):
            my_list = []
            for key, wano in parent.items():
                mypath = copy.copy(path)
                if mypath == "":
                    mypath = "%s" % (key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                self.wano_walker_paths(parent=wano, path=mypath,output=output)
        elif hasattr(parent,'items'):

            for key,wano in parent.items():
                mypath = copy.copy(path)
                if hasattr(wano,"name"):
                    #Actual dict
                    key = wano.name
                #else list
                if mypath == "":
                    mypath="%s" %(key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                self.wano_walker_paths(parent=wano,path=mypath,output=output)
        else:
            #print("%s %s" % (path, parent.get_data()))
            output.append((path,parent.get_type_str()))
        return output

    def wano_walker(self, parent = None, path = ""):
        if (parent == None):
            parent = self
        #print(type(parent))
        if hasattr(parent,'items') and hasattr(parent,'listlike'):
            my_list = []
            for key, wano in parent.items():
                mypath = copy.copy(path)
                if mypath == "":
                    mypath = "%s" % (key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                my_list.append(self.wano_walker(parent=wano, path=mypath))
            return my_list
        elif hasattr(parent,'items'):
            my_dict = {}
            for key,wano in parent.items():
                mypath = copy.copy(path)
                if hasattr(wano,"name"):
                    #Actual dict
                    key = wano.name
                #else list
                if mypath == "":
                    mypath="%s" %(key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                my_dict[key] = self.wano_walker(parent=wano,path=mypath)
            return my_dict
        else:
            #print("%s %s" % (path, parent.get_data()))
            return parent.get_rendered_wano_data()

    def wano_walker_render_pass(self, rendered_wano, parent = None, path = "",submitdir="", flat_variable_list = None):
        if (parent == None):
            parent = self
        #print(type(parent))
        if hasattr(parent,'items') and hasattr(parent,'listlike'):
            my_list = []
            for key, wano in parent.items():
                mypath = copy.copy(path)
                if mypath == "":
                    mypath = "%s" % (key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                my_list.append(self.wano_walker_render_pass(rendered_wano,parent=wano, path=mypath,submitdir=submitdir,flat_variable_list=flat_variable_list))
            return my_list
        elif hasattr(parent,'items'):
            my_dict = {}
            for key,wano in parent.items():
                mypath = copy.copy(path)
                if hasattr(wano,"name"):
                    #Actual dict
                    key = wano.name
                #else list
                if mypath == "":
                    mypath="%s" %(key)
                else:
                    mypath = "%s.%s" % (mypath, key)
                my_dict[key] = self.wano_walker_render_pass(rendered_wano,parent=wano, path=mypath, submitdir=submitdir,flat_variable_list=flat_variable_list)
            return my_dict
        else:
            # We should avoid merging and splitting. It's useless, we only need splitpath anyways
            splitpath=path.split(".")
            #path is complete here, return path
            rendered_parent =  parent.render(rendered_wano,splitpath, submitdir=submitdir)
            if flat_variable_list is not None:
                rendered_parent_jsdl = rendered_parent
                if parent.get_type_str() == "File":
                    filename = parent.get_data()
                    if parent.get_local():
                        to_upload = os.path.join(submitdir, "jobs")
                        cp = os.path.commonprefix([to_upload, filename])
                        relpath = os.path.relpath(filename, cp)
                        #print("relpath was: %s"%relpath)
                        #filename= "c9m:${WORKFLOW_ID}/%s" % relpath
                        #filename = "BFT:${STORAGE_ID}/%s" % relpath
                        filename = relpath
                        #Absolute filenames will be replace with BFT:STORAGEID etc. below.
                    elif not filename.endswith("_VALUE}"):
                        filename = "c9m:${WORKFLOW_ID}/%s" % filename

                    rendered_parent_jsdl = (rendered_parent,filename)

                flat_variable_list.append((path,parent.get_type_str(),rendered_parent_jsdl))
            return rendered_parent


    def prepare_files_submission(self,rendered_wano, basefolder):
        render_wano_filename = os.path.join(basefolder,"rendered_wano.yml")
        with open(render_wano_filename,'w') as outfile:
            outfile.write(yaml.safe_dump(rendered_wano,default_flow_style=False))

        submit_script_filename = os.path.join(basefolder,"submit_command.sh")
        with open(submit_script_filename, 'w') as outfile:
            outfile.write(self.rendered_exec_command)

        template_loader = FileSystemLoader(searchpath="/")
        template_env = Environment(loader = template_loader)

        for remote_file,local_file in self.input_files:
            comp_filename = os.path.join(self.wano_dir_root,local_file)
            if not os.path.exists(comp_filename):
                print("File <%s> not found on disk, please check for spaces before or after the filename."%comp_filename)
                raise OSError("File <%s> not found on disk, please check for spaces before or after the filename."%comp_filename)
            template = template_env.get_template(comp_filename)
            outfile = os.path.join(basefolder,remote_file)
            with open(outfile,'w') as outfile:
                outfile.write(template.render(wano = rendered_wano))

    def flat_variable_list_to_jsdl(self,fvl,basedir,stageout_basedir):
        files = []
        print("CONVERTING FVL to JDSL")
        for myid,(logical_filename, source) in enumerate(self.input_files):
            fvl.append(("IFILE%d"%(myid),"File",(logical_filename,source)))
            #print("Trying to add ",logical_filename,source)


        for (varname,type,var) in fvl:
            if type == "File":
                print("HERE",varname,type,var)
                if var[1].startswith("c9m:"):
                    filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=var[0], overwrite=False,source_uri=var[1])
                elif var[1].endswith("_VALUE}"):
                    filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=var[0], overwrite=False,
                                                                     source_uri=var[1])
                else:
                    #filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=var[0], overwrite=False,source_uri="%s/%s"%(basedir, var[0]))

                    filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=var[0], overwrite=False,
                                                                     source_uri="BFT:${STORAGE_ID}#%s/%s" % (
                                                         stageout_basedir, var[0]))


                files.append(filejsdl)
            else:
                #These should be NON posix arguments in the end
                varname.replace(".","_")
                #not yet done, TODO: TIMO!
        #filejsdl = JSDLtoXML.xml_datastaging_from_source(filename="rendered_wano.yml", overwrite=False, source_uri="c9m:${WORKFLOW_ID}/%s/%s"%(stageout_basedir,"rendered_wano.yml"))
        filejsdl = JSDLtoXML.xml_datastaging_from_source(filename="rendered_wano.yml", overwrite=False,
                                                         source_uri="BFT:${STORAGE_ID}#%s/%s" % (
                                                         stageout_basedir, "rendered_wano.yml"))

        #### TIMO HERE
        files.append(filejsdl)

        for otherfiles in self.get_import_model().get_contents():
            name,importloc,tostage = otherfiles[0],otherfiles[1],otherfiles[2]
            if importloc.endswith("_VALUE}"):
                filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=name, overwrite=False,
                                                                 source_uri=importloc)
            else:
                filejsdl = JSDLtoXML.xml_datastaging_from_source(filename=tostage , overwrite=False,
                                                             source_uri="c9m:${WORKFLOW_ID}/%s"%importloc )
            files.append(filejsdl)


        for filename in self.output_files + [ a[0] for a in self.export_model.get_contents() ]:
            filejsdl = JSDLtoXML.xml_datastaging_to_target(filename=filename, overwrite=True,
                                                           target_uri="c9m:${WORKFLOW_ID}/%s/%s"%(stageout_basedir,filename))
            files.append(filejsdl)

        xml_app = JSDLtoXML.xml_application(self.rendered_exec_command)
        resources = self.resources.render_to_resource_jsdl()
        job_desc = JSDLtoXML.xml_job_description(self.name,xml_app,datastagings=files,resource=resources)

        return job_desc
        #print(etree.tostring(job_desc, pretty_print=True).decode("utf-8"))

    def render_wano(self,submitdir,stageout_basedir=""):
        #We do two render passes in case values depend on each other
        rendered_wano = self.wano_walker()
        # We do two render passes, in case the rendering reset some values:
        fvl = []
        rendered_wano = self.wano_walker_render_pass(rendered_wano,submitdir=submitdir,flat_variable_list=fvl)
        self.rendered_exec_command = Template(self.exec_command).render(wano = rendered_wano)
        self.rendered_exec_command = self.rendered_exec_command.strip(' \t\n\r')
        jsdl = self.flat_variable_list_to_jsdl(fvl, submitdir,stageout_basedir)
        return rendered_wano,jsdl

    def render_and_write_input_files(self,basefolder,stageout_basedir = ""):
        rendered_wano,jsdl = self.render_wano(basefolder,stageout_basedir)
        self.prepare_files_submission(rendered_wano, basefolder)
        return jsdl

    def get_value(self,uri):
        split_uri = uri.split(".")
        current = self.__getitem__(split_uri[0])
        for item in split_uri[1:]:
            current = current[item]
        return current

class WaNoVectorModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoVectorModel, self).__init__(*args, **kwargs)
        self.myvalues = float(kwargs['xml'].text)
        for child in self.xml:
            my_id = int(child.attrib["id"])
            value = float(child.text)
            while (len(self.myvalues) <= my_id):
                self.myvalues.append(0.0)
            self.myvalues[my_id] = value





class WaNoItemFloatModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatModel, self).__init__(*args, **kwargs)
        self.myfloat = float(kwargs['xml'].text)
        self.xml = kwargs['xml']

    def get_data(self):
        return self.myfloat

    def set_data(self, data):
        self.myfloat = float(data)
        super(WaNoItemFloatModel, self).set_data(data)

    def __getitem__(self, item):
        return None

    def get_type_str(self):
        return "Float"

    def update_xml(self):
        self.xml.text = str(self.myfloat)

    def __repr__(self):
        return repr(self.myfloat)


class WaNoItemIntModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemIntModel, self).__init__(*args, **kwargs)
        self.myint = float(kwargs['xml'].text)
        self.xml = kwargs['xml']

    def get_data(self):
        return self.myint

    def set_data(self, data):
        self.myint = int(data)
        super(WaNoItemIntModel,self).set_data(data)

    def __getitem__(self, item):
        return None

    def get_type_str(self):
        return "Int"

    def update_xml(self):
        self.xml.text = str(self.myint)

    def __repr__(self):
        return repr(self.myint)


class WaNoItemBoolModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemBoolModel, self).__init__(*args, **kwargs)
        bool_as_text = kwargs['xml'].text
        self.xml = kwargs['xml']
        if bool_as_text.lower() == "true":
            self.mybool = True
        else:
            self.mybool = False

    def get_data(self):
        return self.mybool

    def set_data(self, data):
        self.mybool = data
        super(WaNoItemBoolModel,self).set_data(data)

    def get_type_str(self):
        return "Boolean"

    def __getitem__(self, item):
        return None

    def update_xml(self):
        if self.mybool:
            self.xml.text = "True"
        else:
            self.xml.text = "False"


class WaNoItemFileModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFileModel, self).__init__(*args, **kwargs)
        self.xml = kwargs['xml']
        self.is_local_file = True
        self.mystring = kwargs['xml'].text
        self.logical_name = self.xml.attrib["logical_filename"]
        if "local" in self.xml.attrib:
            if self.xml.attrib["local"].lower() == "true":
                self.is_local_file = True
            else:
                self.is_local_file = False
        else:
            self.xml.attrib["local"] = "True"

    def get_data(self):
        return self.mystring

    def set_data(self, data):
        self.mystring = str(data)
        super(WaNoItemFileModel,self).set_data(data)

    def __getitem__(self, item):
        return None

    def set_local(self,is_local):
        self.is_local_file = is_local
        if self.is_local_file:
            self.xml.attrib["local"] = "True"
        else:
            self.xml.attrib["local"] = "False"

    def get_local(self):
        return self.is_local_file

    def get_type_str(self):
        return "File"

    def update_xml(self):
        self.xml.text = self.mystring

    def __repr__(self):
        return repr(self.mystring)

    def get_rendered_wano_data(self):
        return self.logical_name

    def render(self, rendered_wano, path, submitdir):
        rendered_logical_name = Template(self.logical_name).render(wano=rendered_wano, path=path)
        #Upload and copy
        #print(submitdir)
        if self.is_local_file:
            destdir = os.path.join(submitdir,rendered_logical_name)
            print("Copying",self.root_model.wano_dir_root,rendered_logical_name,destdir)
            shutil.copy(self.mystring,destdir)
        if sys.version_info >= (3,0):
            return rendered_logical_name
        else:
            return rendered_logical_name.encode("utf-8")



class WaNoItemScriptFileModel(WaNoItemFileModel):
    def __init__(self,*args,**kwargs):
        super(WaNoItemScriptFileModel,self).__init__(*args,**kwargs)
        self.xml = kwargs['xml']
        self.mystring = self.xml.text
        self.logical_name = self.mystring

    def get_path(self):
        root_dir = self.root_model.wano_dir_root
        return os.path.join(root_dir, self.mystring)

    def save_text(self,text):
        with open(self.get_path(),'w') as outfile:
            outfile.write(text)

    def get_type_str(self):
        return "File"

    def get_as_text(self):
        fullpath = self.get_path()
        content = ""
        try:
            #print("Reading script from ",fullpath)
            with open(fullpath,'r') as infile:
                content = infile.read()
            #print("Contents were",content)
            return content
        except FileNotFoundError:
            return ""

    def render(self, rendered_wano, path, submitdir):
        rendered_logical_name = Template(self.logical_name).render(wano=rendered_wano, path=path)
        destfile = os.path.join(submitdir, rendered_logical_name)

        with open(destfile,'w') as out:
            out.write(self.get_as_text())
        return rendered_logical_name


class WaNoItemStringModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemStringModel, self).__init__(*args, **kwargs)
        self.xml = kwargs['xml']
        self.mystring = kwargs['xml'].text

    def get_data(self):
        return self.mystring

    def set_data(self, data):
        self.mystring = str(data)
        super(WaNoItemStringModel,self).set_data(data)

    def __getitem__(self, item):
        return None

    def get_type_str(self):
        return "String"

    def update_xml(self):
        self.xml.text = self.mystring

    def __repr__(self):
        return repr(self.mystring)


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)
