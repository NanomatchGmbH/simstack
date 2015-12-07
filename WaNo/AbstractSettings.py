import abc
from six import string_types
import logging
import yaml


# Abstract Settings base class, handles both a settings format and a commandline parser
# Override _set_defaults in child class

# To use this class, check the code at the end of this file and do the same.

class AbstractSettings(object):
    def __init__(self,name,logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.name = name
        self.settings_container = {}
        self.explanations = {}
        self._set_defaults()
        pass

    def _cast_string_to_correct_type(self,string):
        #Negative Numbers isdigit:
        if string.replace('-','').isdigit():
            return int(string)
        try:
            float(string)
            return float(string)
        except ValueError:
            pass
        if string == "True":
            return True
        if string == "False":
            return False
        return string

    def dump_to_file(self,filename):
        with open(filename,'w') as outfile:
            outfile.write(yaml.dump(self.settings_container,default_flow_style=False))

    def as_dict(self):
        return self.settings_container

    def __getattr__(self, item):
        raise NotImplementedError("Still todo") 

    @abc.abstractmethod
    def _set_defaults(self):
        raise NotImplementedError("Abstract Virtual Method, please implement in child class")
        return

    def _add_default(self,valuename,value,explanation):
        eq_arg = "%s=%s" %(valuename,value)
        self.explanations[valuename] = explanation
        self.parse_eq_args([eq_arg],True)

    def get_value(self,valuename):
        splitname = valuename.split(".")
        current_dict = self.settings_container
        for key in splitname[:-1]:
            current_dict = current_dict[key]
        return current_dict[splitname[-1]]

    #Set Value actually creates the entry:
    def set_value(self,valuename,value):
        splitname = valuename.split(".")
        current_dict = self.settings_container
        for key in splitname[:-1]:
            if not key in current_dict:
                current_dict[key] = {}
            current_dict = current_dict[key]
        current_dict[splitname[-1]] = value

    def print_options(self,outstream):
        outstream.write("%s paramaters: \n" %(self.name))
        for valuename in sorted(self.explanations.keys()):
            explanation = self.explanations[valuename]
            outstream.write("\t%s:\n\t\t%s\n\t\tDefault: %s.\n" %(valuename,explanation,self.get_value(valuename)))

    #The next two functions allow overriding dict values
    #This function returns
    # for the input abc.def=540.0
    # [["abc","def"],540.0]
    @staticmethod
    def settingsplit(infield):
        splitvalues = infield.split("=")
        if len(splitvalues) == 2:
            return (splitvalues[0].split("."),splitvalues[1])
        else:
            raise ValueError()

    #if args contains abc.def=640.0, self["abc"]["def"]=640.0 will be set
    #with createdicts == False, the dicts have to exist already
    def parse_eq_args(self,args, createdicts = False):
        for argtuple in args:
            self.logger.debug("Parsing:",argtuple)
            try:
                splitset = AbstractSettings.settingsplit(argtuple)
                current_dict=self.settings_container
                for field in splitset[0][:-1]:
                    if (not field in current_dict) and createdicts:
                        current_dict[field] = {}
                    if (not field in current_dict):
                        raise KeyError("The settings module did not contain %s. Please check your input."
                        % argtuple )
                    current_dict = current_dict[field]
                final_key = splitset[0][-1]
                if final_key in current_dict or createdicts:
                    current_dict[final_key] = self._cast_string_to_correct_type(splitset[1])
                else:
                    raise KeyError("The settings module did not contain %s. Please check your input."
                    % argtuple )
            except ValueError:
                #We don't discard args with another format to allow for things like argparse
                pass


    def _recursive_helper_finish(self,mydict):
        for key,value in list(mydict.items()):
            if isinstance(value, dict):
                self._recursive_helper_finish(value)
            else:
                if isinstance(value,string_types):
                    if value.startswith("sameas:"):
                        splitsameas = value.split(":")
                        mydict[key] = self.get_value(splitsameas[1])

    def _finish_parsing(self):
        self._recursive_helper_finish(self.settings_container)


if __name__ == '__main__':
    #Small unit test.  
    import os,sys
    
    class TestSettings(AbstractSettings):
        def __init__(self):
            super(TestSettings,self).__init__("TestSettings")

        def _set_defaults(self):
            defaults = [
                ('Box.Lx' , 25.0 , "Half box length, x direction [Angstrom]"),
                ('Box.Ly' , "sameas:Box.Lx",  "Half box length, y direction [Angstrom] By default same as Box.Lx"),
                ('Temperature', 50.0, "Temperature of the sim"),
                ('simparams.acceptance', 1.0, 'Acceptance factor of simulation'),
                ('settings.filename','TestSettings.yml','Filename of the file the chosen settings are written to')
                ]
            for valuename,default,explanation in defaults:
                self._add_default(valuename,default,explanation)
    
    myset = TestSettings()
    myset.parse_eq_args(sys.argv)
    myset._finish_parsing()
    
    if len(sys.argv) <= 1:
        print("Use this class with: %s Box.Lx=11" % os.path.basename(__file__))
        print("Afterwards check the file TestSettings.yml\n")
        myset.print_options(sys.stdout)
        
    #These are the current two ways to access the data:
    settings_filename = myset.get_value('settings.filename')
    settings_filename2 = myset.as_dict()['settings']['filename']
    assert(settings_filename == settings_filename2)
    myset.dump_to_file(settings_filename)
    print("\nWrote settings to %s" % settings_filename)
