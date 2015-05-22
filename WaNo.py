#
# WaNo = Workflow Actice Nodes are the element Workflows are made of 
#
#
import WFELicense
from   six import string_types
import logging
import sys
import glob

#import yaml
from   lxml import etree
#from   io import StringIO, BytesIO

from   WaNoWidgets import *

class WaNoElementFactory:
    factories = {}
    def addFactory(id, shapeFactory):
        WaNoElementFactory.factories.put[id] = shapeFactory
    addFactory = staticmethod(addFactory)
    # A Template Method:
    def createWaNoE(id,inputData):
        if not WaNoElementFactory.factories.has_key(id):    
            xclass = globals()[id]
            xclass.widget = eval(id + 'Widget')   ## this is a sick way to assign the widget functions to the classes 
            WaNoElementFactory.factories[id] = \
              eval(id + '.Factory()')
        return  WaNoElementFactory.factories[id].create(inputData)
    createWaNoE = staticmethod(createWaNoE)
    
class WaNoElement(object):   # abstract class: does not implement validator
    def __init__(self,inputData):
        self.name    = inputData.get("name")
        self.logger  = logging.getLogger("WFELOG")
        
        self.attrib = {}
        for key in inputData.attrib.keys():
            self.attrib[key] = inputData.get(key)
        if 'name' in self.attrib:
            del self.attrib['name']
        
        if not 'sourceType' in self.attrib:
            self.attrib['sourceType']  = 'V'
        if not 'importFrom' in self.attrib:
            self.attrib['importFrom']  = ''
        
        if inputData.text != None:
            self.value  = self.fromString(inputData.text.strip())
            
       
    def makeWidget(self,labelSize,importedItems):
        self.logger.info("Creating Widget: " + self.__class__.__name__ + 'Widget')
        self.myWidget = eval(self.__class__.__name__ + 'Widget')(self,labelSize,importedItems) 
        return self.myWidget
        
    def fromString(self,s):
        return s
    
    def __str__(self):
        return 'WaNoElement: ' + self.__class__.__name__ + ' Named: ' + self.name + ' Value: ' + str(self.value)
    
    def copyContent(self): # override for all that have no 'text' in the widget
        text = getWidgetText(self.myWidget.editor)
        
        self.attrib['hidden']     = str(self.myWidget.hiddenButton.isChecked())
        self.attrib['sourceType'] = self.myWidget.typeSelect.currentText()
        if hasattr(self.myWidget,"importSelect"):
            self.attrib['importFrom'] = self.myWidget.importSelect.currentText()
        self.value = text
        
    def xmlNode(self):
        ee =  etree.Element(self.__class__.__name__,name=self.name)
        for key in self.attrib:
            ee.set(key,self.attrib[key])
        return ee
        
    def xml(self):
        ee = self.xmlNode()
        ee.text = str(self.value)
        return ee 

class WaNoString(WaNoElement): 
    class Factory:
        def create(self,inputData): return WaNoEString(inputData)
  
        
class WaNoFile(WaNoElement): 
    class Factory:
        def create(self,inputData): return WaNoFile(inputData)
  
        
class WaNoOutputFile(WaNoElement): 
    class Factory:
        def create(self,inputData): return WaNoOutputFile(inputData)
   
        
class WaNoLocalFile(WaNoElement): 
    class Factory:
        def create(self,inputData): return WaNoLocalFile(inputData)
        
class WaNoInt(WaNoElement): 
    class Factory:
        def create(self,inputData): return WaNoInt(inputData)
    def fromString(self,s):
        return int(s)
    
class WaNoFloat(WaNoElement):
    class Factory:
        def create(self,inputData): return WaNoFloat(inputData)
    def fromString(self,s):
        return float(s)
    
class WaNoSelectionElement(WaNoElement):
    def __init__(self,inputData):
        super(WaNoSelectionElement,self).__init__(inputData)
        self.name = "NoName"
        
    class Factory:
        def create(self,inputData): return WaNoSelectionElement(inputData)

class WaNoSelection(WaNoElement):  
    def __init__(self,value):
        super(WaNoSelection,self).__init__(value)
        self.elements = []
        for c in value:
            if c.tag != "WaNoSelectionElement":
                self.logger.error("Illegal Element in WaNoSelection" + self.name + " Type: " + c.tag)
            else:
                self.elements.append(WaNoElementFactory.createWaNoE(c.tag,c) )
        if "selected_item" in self.attrib.keys():
            self.selectedItems = [int(self.attrib["selected_item"])]
        else:
            self.selectedItems = []
            
    def copyContent(self):
        self.selectedItems = getSelectedItems(self.myWidget.editor)
    
    def xml(self):
        if len(self.selectedItems) > 0:
            self.attrib["selected_item"]=str(self.selectedItems[0])
        ee = self.xmlNode()
        for e in self.elements:
            ee.append(e.xml())
        return ee
    
    class Factory:
        def create(self,inputData): return WaNoSelection(inputData)
 
class WaNoScript(WaNoElement):  # this is a wrapper for strings
    def __init__(self,name,inputData):
        super(WaNoScript,self).__init__(inputData)
        
        self.name = name
        
        if not name in inputData:
            self.logger.info('Creating default WaNoScript ' + name)
            self.value = ''
            
        #self.attrib  = {}
        
    def __str__(self):
        return self.value

class WaNoSection(WaNoElement):
    def __init__(self,inputData):
        super(WaNoSection, self).__init__(inputData)        
        self.logger = logging.getLogger('WFELOG')
        self.logger.debug("WaNo Section: " + inputData.get("name"))
        self.elements = []
   
        for einfo in inputData:
            # here we can variables assigment or sections 
            # a variable assignment has the form:
            # 
           
            self.logger.debug('... Parsing: ' + einfo.get("name") + ' Type: ' + einfo.tag)
            try:
                ee = WaNoElementFactory.createWaNoE(einfo.tag,einfo)
                self.elements.append(ee)
            except:
                self.logger.error('Input element '+ einfo.tag +  
                                  ' with name ' + einfo.get("name") +
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
 
    def xml(self):
        ee = self.xmlNode()
        for e in self.elements:
            ee.append(e.xml())
        return ee
    
    class Factory:
        def create(self,inputData): return WaNoSection(inputData)    
    
    
        
class WaNoVarSection(WaNoSection):
    def __init__(self,inputData,logger=None):
        super(WaNoVarSection, self).__init__(inputData)  
     
    class Factory:
        def create(self,inputData): return WaNoVarSection(inputData)    
        
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
        self.logger = logging.getLogger('WFELOG')
        self.name            = name
        self.gbType          = 'standard'
        
        self.importSelection = []
        
        self.preScript = WaNoScript('PreProcessor',inputData)
        self.postScript = WaNoScript('PostProcessor',inputData)
        
        self.elements = []
        
        self.name = inputData.get('name')
        self.logger.info('Parsing Wano:  '+ self.name) 
        for c in inputData:
            if not c in ['PreProcessor','PostProcessor']:
                self.logger.debug('Making Element: ' + c.tag)
                xx = WaNoElementFactory.createWaNoE(c.tag,c) 
                self.elements.append(xx)

   # def myCopy(self,source):
        
    def gatherExports(self,varEx,filEx,waNoNames):
        xx    = self.name
        count = 1
        if xx in waNoNames:
            if count == 1:
                del waNoNames[waNoNames.index(xx)]
                waNoNames.append(self.name + '.1')
                count = 2
            xx = self.name + '.' + str(count)
            count += 1
        waNoNames.append(xx)
            
        #varEx.update(self.varExports)
        #filEx.update(self.fileExports)
  
    def xml(self):
        ee = etree.Element(self.__class__.__name__,name=self.name)
        for e in self.elements:
            ee.append(e.xml())
        return ee
       
   
class WorkFlow(list):
    def __str__(self):
        s = 'Workflow: ' + self.name + '\n'
        for e in self.elements:
            s += '\t' + str(e) + '\n'
        return s
        
    def __init__(self,inputData):
        super(WorkFlow, self).__init__() 
        self.logger = logging.getLogger('WFELOG')
        self.name     = name
        self.is_sub_workflow = False 
    
    def parse(self,xml):
        for c in xml:
            print ("Workflow parse",c.tag)
            if c.tag == 'WaNo':
                w = WaNo(c)
            else:
                e = eval(c.tag)(c) 
            self.append(e)
      

class WorkflowControlElement():
    def __init__(self):
        self.logger = logging.getLogger('WFELOG')
        self.wf = []

    def parse(self,c):
        count = 0
        for c in xml:      
            if c.tag != 'Base':
                self.logger.error("Found Tag ",c.tag, " in control block")
            else:
                w = Workflow(c)
                self.wf[count].parse(c)
                count += 1
                #self.wf.append(e)
        if count != len(self.wf):
            self.logger.error("Not enough base widgets in control element")
class ForEach(WorkflowControlElement):
    def __init__(self):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
        
class If(WorkflowControlElement):
    def __init__(self):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
        
class While(WorkflowControlElement):
    def __init__(self):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
class Parallel(WorkflowControlElement):
    def __init__(self):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
            
        
class WaNoRepository(dict):
    def __init__(self):
        super(WaNoRepository, self).__init__()
        self.logger = logging.getLogger(__name__)
        
  
    def parse_xml_doc(self,stream):
        self.logger.error('Not Implemented')
                
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
    
    def parse_xml_dir(self,directory):
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
        self.logger = logging.getLogger('WFELOG')
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
    gbr.parse_xml_file('WaNoRepository/Deposit.xml')
    
    ee = gbr['Deposit'].xml()
    print etree.tostring(ee,pretty_print=True)

    print "done"
    

        
        
