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
        self.logger = self.logger.debug("GridBean Section Init",name,inputData)
        self.elements = []
        self.name     = name
                
        if hasattr(inputData,'keys'): 
            parsedElement = YAMLInputToGB(inputData)
            
           
            print 'parsing:',inputData,parsedElement.gbeType()
            #try:
            print parsedElement.getName()
            print parsedElement.getValue()
            self.elements.append(GBElementFactory.createGBE(parsedElement.gbeType(),
                                                                parsedElement.getName(),
                                                                parsedElement.getValue()))
            #except:
            #    self.logger.error('YAMLI input element could not be converted to Gridbean Element')
  
               
        elif hasattr(inputData,'__getitem__'):
            for einfo in inputData:
                # here we can variables assigment or sections 
                # a variable assignment has the form:
                # 
                parsedElement = YAMLInputToGB(einfo)
                print 'parsing:',einfo,parsedElement.gbeType()
                #try:
                print parsedElement.getName()
                print parsedElement.getValue()
                self.elements.append(GBElementFactory.createGBE(parsedElement.gbeType(),
                                                                parsedElement.getName(),
                                                                parsedElement.getValue()))
                #except:
                #    self.logger.error('YAMLI input element could not be converted to Gridbean Element')
        else:
            self.logger.exception('YAMLI input element is neither list nor dict')
            
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
        
    def __init__(self,name,inputData,logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger = self.logger.debug("GridBean init",name,inputData)
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
        if hasattr(inputData,'keys'): 
            for key in inputData.keys():
                print key # maybe is a dict
        elif hasattr(inputData,'__getitem__'):
            for einfo in inputData:
                # here we can variables assigment or sections 
                # a variable assignment has the form:
                # 
                parsedElement = YAMLInputToGB(einfo)
                print 'parsing:',einfo,parsedElement.gbeType()
                #try:
                print parsedElement.getName()
                print parsedElement.getValue()
                self.elements.append(GBElementFactory.createGBE(parsedElement.gbeType(),
                                                                parsedElement.getName(),
                                                                parsedElement.getValue()))
                #except:
                #    self.logger.error('YAMLI input element could not be converted to Gridbean Element')
        else:
            self.logger.exception('YAMLI input element is neither list nor dict')
            
        
class YAMLInputToGB:
    def __init__(self,element):
        self.element = element
        self.namekeyword  = 'YAMLINAME'
        self.typekeyword  = 'YAMLITYPE'
        self.valuekeyword = 'YAMLIVALUE'
        self.isParsed    = False
        
    def gbeType(self):
        # there are 2 types of elements: 
        #       variable assignments
        #       sections
        # variable assignments are of type:
        #     { name : val } or 
        #     { %NAMEKEYWORD% : name, 
        #       %TYPEKEYWORD% : type, 
        #       %VALUEKEYWORD%: val,
        #             .... other stuff .... (optional keywords) 
        #     }
        # the first form defaults to 'string' (this could be generalized later)
        # anything not fitting this pattern is a section, sections consist of:
        # { heading: list or dict of elements }
        # 
        # 
        if type(self.element) is dict:
            if len(self.element.keys()) == 1:  # could be simple variable
                self.name  = self.element.keys()[0]
                self.value = self.element[self.name]
                self.isParsed = True
                if isinstance(self.value,basestring):
                    return 'GBEString'
                elif isinstance(self.value,(list,tuple)): # could be a selection
                    for e in self.value:
                        isSelection = True
                        if not isinstance(e,basestring): # one subelement is not a string, could still be a section 
                            isSelection = False
                            break 
                    if isSelection:
                        return 'GBESelection'
                    return 'GBESection'
                else: # we have a { aaa : bbb } pair that cannot be parsed 
                    return 'GBESection'
            else: # could still be a var if the keywords are there
                keys = self.element.keys()
                if self.namekeyword in keys and self.typekeyword in keys and self.valuekeyword in keys:
                    # its a variable
                    self.name  = self.element[self.namekeyword]
                    self.value = self.element[valuekeyword]
                    self.isParsed = True
                    return 'GBE'+keys[self.typekeyword]
                else:
                    if self.namekeyword in keys:
                        logger.error('error parsing yamli input: ' + self.varkeyword + 
                                     ' found but other keywords missing in ' + str(self.element))
                        raise ValueError
                    # 
                    # unclear what we have 
                    #
                    return 'GBESection'
    def getName(self):
        if not self.isParsed:
            raise ValueError
        return self.name
    def getValue(self):
        if not self.isParsed:
            raise ValueError
        return self.value
            
                
                
        
    
    
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
        
if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    import yaml
    try:
        filename  = "TestSettings.yml"
        stream    = open("TestSettings.yml", 'r')
        inputData = yaml.load(stream)
    except:
        print "YAML error reading/parsing " + filename
        sys.exit()
    print inputData
    try:
        gbName = inputData['Name']
    except:
        logger.error('YAML input has not Name field')
        raise ValueError
                    
    try:
        settings = inputData['Settings']
    except:
        logger.error('YAML input has not Settings field')
        raise ValueError
    
    gb = GridBean(gbName,settings)
    
    #gbr = GridBeanRepository()
    #print gbr['Gromacs']
    #print "done"
    

        
        
