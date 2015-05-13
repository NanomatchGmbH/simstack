#
# WaNo = Workflow Actice Nodes are the element Workflows are made of 
#
#
import WFELicense
from   six import string_types
import logging
import sys
import glob
import yaml
from   lxml import etree
from   io import StringIO, BytesIO

from   WaNoWidgets import *

class WaNoElementFactory:
    factories = {}
    def addFactory(id, shapeFactory):
        WaNoElementFactory.factories.put[id] = shapeFactory
    addFactory = staticmethod(addFactory)
    # A Template Method:
    def createWaNoE(id,name,inputData):
        if not WaNoElementFactory.factories.has_key(id):
            xclass = globals()[id]
            xclass.widget = eval(id + 'Widget')   ## this is a sick way to assign the widget functions to the classes 
            WaNoElementFactory.factories[id] = \
              eval(id + '.Factory()')
        return  WaNoElementFactory.factories[id].create(name,inputData)
    createWaNoE = staticmethod(createWaNoE)
    
class WaNoElement(object):   # abstract class: does not implement validator
    def __init__(self,name,value):
        self.name    = name
        self.value   = value
    def __str__(self):
        return 'WaNoE: ' + self.__class__.__name__ + ' Named: ' + self.name + ' Value: ' + str(self.value)
    def copyContent(self): # override for all that have no 'text' in the widget
        text = getWidgetText(self.editor)
        self.value = text

class WaNoEString(WaNoElement): 
    class Factory:
        def create(self,name,inputData): return WaNoEString(name,inputData)
     
class WaNoEFile(WaNoElement): 
    class Factory:
        def create(self,name,inputData): return WaNoEFile(name,inputData)
        
class WaNoELocalFile(WaNoElement): 
    class Factory:
        def create(self,name,inputData): return WaNoELocalFile(name,inputData)
        
class WaNoEInt(WaNoElement): 
    class Factory:
        def create(self,name,inputData): return WaNoEInt(name,inputData)

class WaNoEFloat(WaNoElement):
    class Factory:
        def create(self,name,inputData): return WaNoEFloat(name,inputData)

class WaNoESelection(WaNoElement):  
    def __init__(self,name,value):
        super(WaNoESelection,self).__init__(name,value)
        self.selectedItem = 0
    def copyContent(self):
        self.selectedItem = getSelectedItem(self.editor)
        
    class Factory:
        def create(self,name,inputData): return WaNoESelection(name,inputData)
 
class Script:  # this is a wrapper for strings
    def __init__(self):
        self.content = ''
    def __str__(self):
        return self.content

class WaNoESection(WaNoElement):
    def __init__(self,name,inputData,logger=None):
        super(WaNoESection, self).__init__(name,None)        
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("WaNo Section: " + name)
        self.elements = []
   
        for einfo in inputData:
            # here we can variables assigment or sections 
            # a variable assignment has the form:
            # 
            parsedElement = YAMLInputToWaNo(einfo)
            self.logger.debug('... Parsing: ' + parsedElement.getName() + ' Type: ' + parsedElement.gbeType())
            try:
                self.elements.append(WaNoElementFactory.createWaNoE(parsedElement.gbeType(),
                                                            parsedElement.getName(),
                                                            parsedElement.getValue()))
            except:
                self.logger.error('Input element '+ parsedElement.gbeType() +  
                                  ' with name ' + parsedElement.getName() +
                                  ' could not be converted to WaNo Element')
                raise TypeError
    def copyContent(self): #
        for e in self.elements:
            e.copyContent()
            
    def __str__(self):
        xs = 'Section: ' + self.name + '\n'
        for e in self.elements:
            xs += '   ' + str(e) + '\n'
        return xs
    
    class Factory:
        def create(self,name,inputData): return WaNoESection(name,inputData)    
        
class WaNo:
    def __str__(self):
        s  = 'WaNo: ' + self.name + '\n'
        s += 'File Imports: ' + str(self.fileImports) + '\n'
        s += 'Var  Imports: ' + str(self.varImports) + '\n'
        
        s += 'Prepocessor:\n' + str(self.preScript) + '\n'
        s += '\nSettings\n'
        
        for e in self.elements:
            s += '\t' + str(e) + '\n'
            
        s +=  '\n' + 'Postpocessor:\n' + str(self.postScript) + '\n'
        s += 'File Exports: ' + str(self.fileExports) + '\n'
        s += 'Var  Exports: ' + str(self.varExports) + '\n'
        return s
    
   
      
            
    def __init__(self,inputData,name=None):
        self.logger = logging.getLogger(__name__)
        self.name        = name
        self.gbType      = 'standard'
        self.fileImports = {}          # key: local name, value: exported name from prior WaNo
        self.varImports  = {}          # key: local name, value: exported name from prior WaNo
        self.fileExports = {}          # key: exported name, value: local name
        self.varExports  = {}          # key: exported name, value: local name
        self.preScript   = Script()
        self.postScript  = Script()
        
        self.elements = []
        
        if name != None: # YML
            self.parse_yml(inputData)
        else:
            self.name = inputData.get('name')
            for c in inputData:
                xx = eval(c.tag)(c)  # 
                print c
            self.name = "Dummy"    
    def parse_yml(self,inputData):
        self.logger.debug("WaNo Parsing: " + name)
        self.name        = name
        #
        #  we expect here a list of items or a dictionary (the latter means we have sections)
        #
        assert isinstance(inputData, (list, tuple))
                
        for einfo in inputData: 
            # here we can variables assigment or sections 
            # a variable assignment has the form:
            # 
            parsedElement = YAMLInputToWaNo(einfo)
            self.logger.debug('... Parsing: ' + parsedElement.getName() + ' Type: ' + parsedElement.gbeType())
            try:
                self.elements.append(WaNoElementFactory.createWaNoE(parsedElement.gbeType(),
                                                                parsedElement.getName(),
                                                                parsedElement.getValue()))
            except:
                self.logger.error('Input element '+ parsedElement.gbeType() + 
                                   ' with name ' + parsedElement.getName() + 
                                   ' could not be generated')
                raise TypeError
       
        
class YAMLInputToWaNo:
    def __init__(self,element):
        self.element = element
        self.typekeyword  = 'WaNoType'
        self.valuekeyword = 'Value'
        self.content      = None
        self.logger = logging.getLogger(__name__)
   
        # all elements have the form:
        #   name: 
        #      WaNoTYPE : type
        #      WaNoValue: value 
        #      other_key: v1 (more of those) 
        # 
        if type(self.element) is dict:
            if len(self.element.keys()) != 1:
                logger.error('Expected Dict with one key for variable definition in ' + str(self.element))       
                raise KeyError
            else:
                self.name     = self.element.keys()[0]
                self.content  = self.element[self.name]
                required_keys = [self.typekeyword, self.valuekeyword]
                for k in required_keys:
                    if not k in self.content:
                        self.logger.error('Element: ' + str(self.content) + ' has no key: ' + k)
                        raise KeyError
                
    def gbeType(self):
        return 'WaNoE'+self.content[self.typekeyword]
    def getName(self):
        return self.name
    def getValue(self):
        return self.content[self.valuekeyword]
    def getOptions(self):
        options = copy.copy(self.content)
        del options[self.valuekeyword]
        del options[self.typekeyword]
        return options
            
    
class WorkFlow(list):
    def __str__(self):
        s = 'Workflow: ' + self.name + '\n'
        for e in self.elements:
            s += '\t' + str(e) + '\n'
        return s
        
    def __init__(self,name,inputData):
        super(WorkFlow, self).__init__() 
        self.name     = name
        self.is_sub_workflow = False 
      
class WaNoRepository(dict):
    def __init__(self):
        super(WaNoRepository, self).__init__()
        self.logger = logging.getLogger(__name__)
        
    def parse_yml_doc(self,stream):
        try:
            self.inputData = yaml.load(stream)
        except:
            print "YAML error reading/parsing stream"
            raise        
        try:
            gbName = self.inputData['Name']
        except:
            self.logger.error('YAML input has not Name field')
            raise            
        try:
            settings = self.inputData['Settings']
        except:
            self.logger.error('YAML input has no Settings field')
            raise ValueError        
        self[gbName] = WaNo(settings,gbName)
        return self[gbName]
    
    def parse_xml_doc(self,stream):
        self.logger.error('Not Implemented')
        try:
            self.inputData = etree.parse(StringIO(stream))
        except:
            print "XAML error reading/parsing stream"
            raise        

        try:
            gbName = self.inputData['Name']
        except:
            
            raise            
        try:
            settings = self.inputData['Settings']
        except:
            self.logger.error('YAML input has no Settings field')
            raise ValueError        
       
        
    def parse_yml_file(self,filename):
        try:
            stream = open(filename,'r')
        except:
            self.logger.error('File not found: ' + filename)
            raise 
        return self.parse_yml_doc(stream)
    
    def parse_xml_file(self,filename):
        try:
            self.inputData = etree.parse(filename)
        except:
            self.logger.error('File not found: ' + filename)
            raise 
        r = self.inputData.getroot()
        if r.tag == "WaNoCollection":
            for c in r:
                w = WaNo(c)
                self[w.name] = w
        else:
            if not r.tag in ['WaNoTemplate','WaNo']:
                self.logger.error('No WaNo or WaNoTemplate found as first element of ' + filename)
                raise ValueError
            w = WaNo(r)
            self[w.name] = w
        return w
        
    def parse_yml_dir(self,directory):
        for filename in glob.iglob(directory+'/*.yml'):
            print filename
            self.parse_yml_file(filename) 
        
        
"""
        self['Gromacs'] = WaNo('Gromacs',
                               [{'type': 'WaNoEString', 'name': 'Forcefield','value': 'AMBER99'} ,
                                {'type': 'WaNoEFloat',  'name': 'Temperature','value': 3.0 }])
        self['Turbomole'] = WaNo('Turbomole',
                               [{'type': 'WaNoEString', 'name': 'Basis','value': 'STG3G'} ,
                                {'type': 'WaNoEInt'   , 'name': 'Iterations','value': 1 },
                                {'type': 'WaNoEString', 'name': 'Method','value': 'DFT' },
                                ])
        self['Script']    = WaNo('Script',
                               [{'type': 'WaNoEString', 'name': 'ScriptText'}]) 
"""

import unittest


class SimpleTests(unittest.TestCase):
    def setUp(self):
        input1 = """
Name: MDSimulator
Settings:
  - Forcefield:
     WaNoType: Selection
     Value:
      - AMBER99
      - AMBER99*
      - GROMOS
  - Box:
     WaNoType: Section
     Value:
     - Lx:
        WaNoType: Float
        Value : 25.0
     - Ly:
        WaNoType: Float
        Value : 25.0
     - Lz:
        WaNoType: Float
        Value : 25.0
  - Variables:
      WaNoType:  Section
      Value:
         - Temperature:
             WaNoType: Float
             Value:  300.0
         - Inputfile: 
             WaNoType: File
             Value:  $BASE/inputs/input.top
         - Trajectory: 
              WaNoType: LocalFile
              Value:  run.tr
  # VARIOUS PREPROCESSING OPTIONS
  - PREPROCESSING OPTIONS:
      WaNoType: Section
      Value:
       - define: 
           WaNoType: String
           Value: -DPOSRES
           
           
""" 
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Parsing WaNo')      
        try:
            self.inputData = yaml.load(input1)
        except:
            print "YAML error reading/parsing " + filename
            raise ValueError            
        
    def test_parse(self):
        try:
            gbName = self.inputData['Name']
        except:
            self.logger.error('YAML input has not Name field')
            raise ValueError           
        try:
            settings = self.inputData['Settings']
        except:
            self.logger.error('YAML input has not Settings field')
            raise ValueError
        
        gb = WaNo(gbName,settings)
        
    def test_single_file(self):
        waNoRep = WaNoRepository()
        waNoRep.parse_yml_file('WaNoRepository/MDSimulator.yml')
        
    def test_all_dir(self):
        waNoRep = WaNoRepository()
        waNoRep.parse_yml_dir('WaNoRepository')
        

if __name__ == '__main__':
    logging.basicConfig(filename='wano.log',filemode='w',level=logging.DEBUG)
    logging.getLogger(__name__).addHandler(logging.StreamHandler())
    #unittest.main()
    gbr = WaNoRepository()
    gbr.parse_xml_file('WaNoRepository/Simona.xml')
    

    print "done"
    

        
        
