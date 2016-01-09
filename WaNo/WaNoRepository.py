import logging
import glob
from   lxml import etree

from .view.WaNo import WaNo

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
            print (filename)
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

