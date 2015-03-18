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
            
                