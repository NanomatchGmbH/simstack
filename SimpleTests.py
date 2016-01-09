import unittest

from .WaNo.WaNoRepository import WaNoRepository

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
            print ("YAML error reading/parsing " + filename)
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
        mypath = os.path.dirname(os.path.realpath(__file__))
        waNoRep.parse_yml_file(mypath + '/WaNoRepository/MDSimulator.yml')
        
    def test_all_dir(self):
        waNoRep = WaNoRepository()
        waNoRep.parse_yml_dir(mypath + '/WaNoRepository')
        

if __name__ == '__main__':
    logging.basicConfig(filename='wano.log',filemode='w',level=logging.DEBUG)
    logging.getLogger(__name__).addHandler(logging.StreamHandler())
    #unittest.main()
    gbr = WaNoRepository()
    gbr.parse_xml_file(mypath + '/WaNoRepository/Deposit.xml')
    
    ee = gbr['Deposit'].xml()
    print (etree.tostring(ee,pretty_print=True))

 
    

        
        
