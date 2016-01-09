#
# WaNo = Workflow Actice Nodes are the element Workflows are made of 
#
#
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
from   lxml import etree

from .WaNoWidgets import *

class WaNoElementFactory:
    factories = {}
    @staticmethod
    def addFactory(id, shapeFactory):
        WaNoElementFactory.factories.put[id] = shapeFactory

    # A Template Method:
    @staticmethod
    def createWaNoE(id,inputData):
        if id not in WaNoElementFactory.factories:
            #xclass = globals()[id]
            #xclass.widget = eval(id + 'Widget')   ## this is a sick way to assign the widget functions to the classes 
            WaNoElementFactory.factories[id] = \
              eval(id + '.Factory()')
        return  WaNoElementFactory.factories[id].create(inputData)
    
class WaNoElement(object):   # abstract class: does not implement validator
    def __init__(self,inputData):
        self.name    = inputData.get("name")
        self.logger  = logging.getLogger("WFELOG")
        
        self.attrib = {}
        for key in list(inputData.attrib.keys()):
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
        self.logger.debug("Creating Widget: " + self.__class__.__name__ + 'Widget')
        self.myWidget = eval(self.__class__.__name__ + 'Widget')(self,labelSize,importedItems) 
        #TODO connect WaNoChangedSig to WaNoEditor.hasChanged.
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
        if "selected_item" in list(self.attrib.keys()):
            self.selectedItems = [int(self.attrib["selected_item"])]
        else:
            self.selectedItems = []
            
    def copyContent(self):
        self.selectedItems    = getSelectedItems(self.myWidget.editor)
        self.attrib['hidden'] = str(self.myWidget.hiddenButton.isChecked())
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
    def __init__(self,inputData):
        super(WaNoScript,self).__init__(inputData)
        
        #try:
            #self.name    = self.attrib['name']
        #except:
            #self.logger.error("No name attribute in script WaNo element")
            #self.name    = 'Unnamed'
        
        self.imports = []
        try:
            impxml = inputData.find('Imports')
            for c in impxml:
                if c.tag == 'ImportElement':
                    self.imports.append((c.get('local'),c.get('source_wano'),c.get('source')))
        except:
            pass
       
        
        if inputData.text != None:
            self.value = inputData.text
        else:
            self.value = ''
        
        
    def __str__(self):
        return self.value


    def xml(self):
        ee = super(WaNoScript,self).xml()
        impXml = etree.Element('Imports')
        for imp in self.imports:
            impXmlE = etree.Element('ImportElement',local=imp[0],source_wano=imp[1],source=imp[2])
            impXml.append(impXmlE)
        ee.append(impXml)
        return ee 
            
        
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
       
        self.elements = []
        
        self.name = inputData.get('name')
        self.logger.info('Parsing Wano:  '+ self.name) 
        for c in inputData:
            if c.tag != 'WaNoScript':
                self.logger.debug('Making Element: ' + c.tag)
                xx = WaNoElementFactory.createWaNoE(c.tag,c) 
                self.elements.append(xx)
            else:
                if c.get('name') == 'PreProcessor':
                    self.preScript = WaNoScript(c)
                elif c.get('name') == 'PostProcessor':
                    self.postScript = WaNoScript(c)
                    
       
        if not hasattr(self,'preScript'):
            self.preScript = WaNoScript(etree.Element('WaNoScript',name='PreProcessor'))

        if not hasattr(self,'postScript'):
            self.postScript = WaNoScript(etree.Element('WaNoScript',name='PostProcessor'))

        
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
        ee.append(self.preScript.xml())
        for e in self.elements:
            ee.append(e.xml())
        ee.append(self.postScript.xml())
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
        #self.is_sub_workflow = False 
        self.isOpen = False
        self.parse(inputData)
    
    def setToXML(self,xml):
        for x in range(len(self)):
            self.pop()
            
        for c in xml:
            print("Workflow parse",c.tag,c.get('name'))
            if c.tag == 'WaNo':
                e = WaNo(c)
            else:
                e = eval(c.tag)(c) 
            self.append(e)
        
            
    def xml(self):
        ee =  etree.Element(self.__class__.__name__,name=self.name)
        for key in self.attrib:
            ee.set(key,self.attrib[key])
        for e in self:
            ee.append(e.xml())
        return ee
    
    def parse(self,xml):
        self.attrib = {}
        for key in list(xml.attrib.keys()):
            self.attrib[key] = xml.get(key)
        self.name = xml.get('name')
        if 'name' in self.attrib:
            del self.attrib['name']
        for c in xml:
            print ("Workflow parse",c.tag)
            if c.tag == 'WaNo':
                e = WaNo(c)
            else:
                print(c.tag)
                e = eval(c.tag)(c) 
            self.append(e)
      

        
class WorkflowControlElement(object):
    def __init__(self):
        self.logger = logging.getLogger('WFELOG')
        self.wf = []

    def parse(self,xml):
        count = 0
        for c in xml:
            if c.tag != 'Base':
                self.logger.error("Found Tag ",c.tag, " in control block")
            else:
                w = WorkFlow(c)
                #self.wf[count].parse(c)
                count += 1
                #self.wf.append(e)
        if count != len(self.wf):
            self.logger.error("Not enough base widgets in control element")
#
# Workflow Control Elements
#
class ForEach(WorkflowControlElement):
    def __init__(self, c):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
        
class If(WorkflowControlElement):
    def __init__(self, c):
        super(If,self).__init__(self)
        self.parse(c)
        
        
class While(WorkflowControlElement):
    def __init__(self, c):
        super(While,self).__init__(self)
        self.parse(c)
        
class Parallel(WorkflowControlElement):
    def __init__(self, c):
        super(Parallel, self).__init__()
        self.parse(c)
