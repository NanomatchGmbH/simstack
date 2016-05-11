#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

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

from PySide import QtCore
import yaml
import os
import shutil

from jinja2 import Template, FileSystemLoader, Environment



class WaNoModelDictLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelDictLike, self).__init__(*args, **kwargs)
        self.wano_dict = collections.OrderedDict()
        self.xml = kwargs["xml"]

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self, self)
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

    def items(self):
        return self.wano_dict.items()

    def get_data(self):
        return self.wano_dict

    def set_data(self, wano_dict):
        self.wano_dict = wano_dict

    def wanos(self):
        return self.wano_dict.values()

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

    def get_data(self):
        return self.choices[self.chosen]

    @QtCore.Slot(int)
    def set_chosen(self,choice):
        self.chosen = int(choice)

    def update_xml(self):
        for child in self.xml.iter("Entry"):
            myid = int(child.attrib["id"])
            if "chosen" in child.attrib:
                del child.attrib["chosen"]

            if self.chosen == myid:
                child.attrib["chosen"] = "True"




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
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self.root_model, self)
            # view.set_model(model)
            self.wano_list.append(model)

    def __getitem__(self, item):
        return self.wano_list[item]

    def items(self):
        return enumerate(self.wano_list)

    def wanos(self):
        return self.wano_list

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
        wano_temp_dict = collections.OrderedDict()
        for cchild in child:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(cchild, self, self)
            wano_temp_dict[cchild.attrib['name']] = model
        return wano_temp_dict

    def __getitem__(self, item):
        return self.list_of_dicts[item]

    def __iter__(self):
        return iter(self.list_of_dicts)

    def items(self):
        return enumerate(self.list_of_dicts)

    def __reversed__(self):
        return reversed(self.list_of_dicts)

    def get_data(self):
        return self.list_of_dicts

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
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        my_xml = copy.copy(self.first_xml_child)
        my_xml.attrib["id"] = str(len(self.list_of_dicts))
        self.xml.append(my_xml)
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        model_dict = self.parse_one_child(my_xml)
        WaNo.WaNoFactory.WaNoFactory.build_views()
        self.list_of_dicts.append(model_dict)

    def update_xml(self):
        for wano_dict in self.list_of_dicts:
            for wano in wano_dict.values():
                wano.update_xml()


# This is the parent class and grandfather. Children have to be unique, no lists here
class WaNoModelRoot(WaNoModelDictLike):
    def __init__(self, *args, **kwargs):
        self.root_model = self
        self.full_xml = kwargs['xml']
        kwargs['xml'] = self.full_xml.find("WaNoRoot")
        super(WaNoModelRoot, self).__init__(*args, **kwargs)
        self.exec_command = self.full_xml.find("WaNoExecCommand").text
        self.input_files = []

        self.wano_dir_root = kwargs["wano_dir_root"]
        for child in self.full_xml.findall("./WaNoInputFiles/WaNoInputFile"):
            self.input_files.append((child.attrib["logical_filename"],child.text))

        self.output_files = []
        for child in self.full_xml.findall("./WaNoOutputFiles/WaNoOutputFile"):
            self.output_files.append(child.text)

    @staticmethod
    def construct_from_wano(filename, rootview):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.ElementTree(file=filename,parser=parser)
        root = tree.getroot()
        wano_dir_root = os.path.dirname(os.path.realpath(filename))
        modelroot = WaNoModelRoot(xml=root, view=rootview, parent_model=None, wano_dir_root=wano_dir_root)
        return modelroot

    def save_xml(self,filename):
        with open(filename,'w') as outfile:
            outfile.write(etree.tostring(self.full_xml,pretty_print=True).decode("utf-8"))

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

    def wano_walker_render_pass(self, rendered_wano, parent = None, path = ""):
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
                my_list.append(self.wano_walker_render_pass(rendered_wano,parent=wano, path=mypath))
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
                my_dict[key] = self.wano_walker_render_pass(rendered_wano,parent=wano, path=mypath)
            return my_dict
        else:
            # We should avoid merging and splitting. It's useless, we only need splitpath anyways
            splitpath=path.split(".")
            return parent.render(rendered_wano,splitpath)

    def mock_submission(self,rendered_wano):
        with open("Staging/rendered_wano.yml",'w') as outfile:
            outfile.write(yaml.dump(rendered_wano,default_flow_style=False))

        with open("Staging/submit_command.sh", 'w') as outfile:
            outfile.write(self.exec_command)

        template_loader = FileSystemLoader(searchpath="/")
        template_env = Environment(loader = template_loader)

        for remote_file,local_file in self.input_files:
            comp_filename = os.path.join(self.wano_dir_root,local_file)
            template = template_env.get_template(comp_filename)
            outfile = os.path.join("Staging",remote_file)
            with open(outfile,'w') as outfile:
                outfile.write(template.render(wano = rendered_wano))

    def render(self):
        #We do two render passes in case values depend on each other
        rendered_wano = self.wano_walker()
        # We do two render passes, in case the rendering reset some values:
        rendered_wano = self.wano_walker_render_pass(rendered_wano)
        self.exec_command = Template(self.exec_command).render(wano = rendered_wano)
        self.mock_submission(rendered_wano)




class WaNoItemFloatModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatModel, self).__init__(*args, **kwargs)
        self.myfloat = float(kwargs['xml'].text)
        self.xml = kwargs['xml']

    def get_data(self):
        return self.myfloat

    def set_data(self, data):
        self.myfloat = float(data)

    def __getitem__(self, item):
        return None

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

    def __getitem__(self, item):
        return None

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
        self.mystring = kwargs['xml'].text
        self.logical_name = self.xml.attrib["logical_filename"]

    def get_data(self):
        return self.mystring

    def set_data(self, data):
        self.mystring = str(data)

    def __getitem__(self, item):
        return None

    def update_xml(self):
        self.xml.text = self.mystring

    def __repr__(self):
        return repr(self.mystring)

    def get_rendered_wano_data(self):
        return self.logical_name

    def render(self, rendered_wano, path):
        rendered_logical_name = Template(self.logical_name).render(wano=rendered_wano, path=path)
        #Upload and copy
        destdir = os.path.join("Staging",rendered_logical_name)
        shutil.copy(self.mystring,destdir)
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

    def __getitem__(self, item):
        return None

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
