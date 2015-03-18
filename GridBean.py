#
# Gridbeans are a list of GridBeanElements
# Not implemented: 
#         creation by Factories
#         markup files in kivy
#
import WFELicense
from six import string_types
import logging
import sys



class GBElementFactory:
    factories = {}
    def addFactory(id, shapeFactory):
        GBElementFactory.factories.put[id] = shapeFactory
    addFactory = staticmethod(addFactory)
    # A Template Method:
    def createGBE(id,name,inputData):
        if not GBElementFactory.factories.has_key(id):
            GBElementFactory.factories[id] = \
              eval(id + '.Factory()')
        return  GBElementFactory.factories[id].create(name,inputData)
    createGBE = staticmethod(createGBE)
    
class GridBeanElement:
    def __init__(self,name,value):
        self.name  = name
        self.value = value
    def __str__(self):
        return 'GBE: ' + self.__class__.__name__ + ' Named: ' + self.name + ' Value: ' + str(self.value)
    
   
class GBEString(GridBeanElement): 
    class Factory:
        def create(self,name,inputData): return GBEString(name,inputData)
        
class GBEInt(GridBeanElement): 
    class Factory:
        def create(self,name,inputData): return GBEInt(name,inputData)

class GBEFloat(GridBeanElement):
    class Factory:
        def create(self,name,inputData): return GBEFloat(name,inputData)


class GBESelection(GridBeanElement):    
    class Factory:
        def create(self,name,inputData): return GBESelection(name,inputData)
 
class Script:  # this is a wrapper for strings
    def __init__(self):
        self.content = ''
    def __str__(self):
        return self.content

class GBESection(GridBeanElement):
    def __init__(self,name,inputData,logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("GridBean Section Init" + name)
        self.elements = []
        self.name     = name
   
        for einfo in inputData:
            # here we can variables assigment or sections 
            # a variable assignment has the form:
            # 
            parsedElement = YAMLInputToGB(einfo)
            self.logger.debug('... Parsing: ' + parsedElement.getName() + ' Type: ' + parsedElement.gbeType())
            try:
                self.elements.append(GBElementFactory.createGBE(parsedElement.gbeType(),
                                                            parsedElement.getName(),
                                                            parsedElement.getValue()))
            except:
                self.logger.error('YAMLI input element could not be converted to Gridbean Element')
            
    class Factory:
        def create(self,name,inputData): return GBESection(name,inputData)    
        
class GridBean:
    def __str__(self):
        s  = 'Gridbean: ' + self.name + '\n'
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
        
    def __init__(self,name,inputData):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("GridBean init" + name)
        self.name        = name
        self.gbType      = 'standard'
        self.fileImports = {}          # key: local name, value: exported name from prior GB
        self.varImports  = {}          # key: local name, value: exported name from prior GB
        self.fileExports = {}          # key: exported name, value: local name
        self.varExports  = {}          # key: exported name, value: local name
        self.preScript   = Script()
        self.postScript  = Script()
        
        self.elements = []
        #
        #  we expect here a list of items or a dictionary (the latter means we have sections)
        #
        assert isinstance(inputData, (list, tuple))
                
        for einfo in inputData: 
            # here we can variables assigment or sections 
            # a variable assignment has the form:
            # 
            parsedElement = YAMLInputToGB(einfo)
            self.logger.debug('... Parsing: ' + parsedElement.getName() + ' Type: ' + parsedElement.gbeType())
            try:
                self.elements.append(GBElementFactory.createGBE(parsedElement.gbeType(),
                                                                parsedElement.getName(),
                                                                parsedElement.getValue()))
            except:
                self.logger.error('YAMLI input element could not be converted to Gridbean Element')
       
        
class YAMLInputToGB:
    def __init__(self,element):
        self.element = element
        self.typekeyword  = 'GBType'
        self.valuekeyword = 'Value'
        self.content      = None
        self.logger = logging.getLogger(__name__)
   
        # all elements have the form:
        #   name: 
        #      GBTYPE : type
        #      GBValue: value 
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
        return 'GBE'+self.content[self.typekeyword]
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
  
  
      
class GridBeanRepository(dict):
    def __init__(self,*arg,**kw):
        super(GridBeanRepository, self).__init__(*arg, **kw)
        self['Gromacs'] = GridBean('Gromacs',
                               [{'type': 'GBEString', 'name': 'Forcefield','value': 'AMBER99'} ,
                                {'type': 'GBEFloat',  'name': 'Temperature','value': 3.0 }])
        self['Turbomole'] = GridBean('Turbomole',
                               [{'type': 'GBEString', 'name': 'Basis','value': 'STG3G'} ,
                                {'type': 'GBEInt'   , 'name': 'Iterations','value': 1 },
                                {'type': 'GBEString', 'name': 'Method','value': 'DFT' },
                                ])
        self['Script']    = GridBean('Script',
                               [{'type': 'GBEString', 'name': 'ScriptText'}]) 
      
import unittest
class SimpleTester(unittest.TestCase):
    def setUp(self):
        filename  = "TestSettings.yml"
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Parsing Gridbean in ' + filename)
        import yaml
        try:
            stream    = open(filename, 'r')
            self.inputData = yaml.load(stream)
        except:
            print "YAML error reading/parsing " + filename
            sys.exit()
            
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
        
        gb = GridBean(gbName,settings)

if __name__ == '__main__':
    with open('Gridbean.log', 'w'):
        pass
    logging.basicConfig(filename='Gridbean.log',level=logging.DEBUG)
    unittest.main()

    print "done"
    

        
        
