import abc
from six import string_types
import logging
import yaml
from os import path


# Abstract Settings base class, handles both a settings format and a commandline parser
# Override _set_defaults in child class

# To use this class, check the code at the end of this file and do the same.

class AbstractSettings(object):
    def __init__(self, name, settings_file=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.name = name
        self.settings_container = {}
        self.explanations = {}
        self._set_defaults()
        self.__set_settings_filename(settings_file)
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

    def __set_settings_filename(self, filename):
        self.settings_file = filename

    def dump_to_file(self,filename):
        with open(filename,'w') as outfile:
            outfile.write(yaml.dump(self.settings_container,default_flow_style=False))

    """ Saves the settings to file.

    The file path set in the constructor is used by default.
    If the settings_file parameter is specified, this will be used as new 
    settings file path and it will be stored as such.

    .. note:: This differs from :func:`dump_to_file()` which allows saving
    the settings into an arbitrary file and does not change the internal state.

    """
    def save(self, settings_file = None):
        if not settings_file is None:
            self.__set_settings_filename(settings_file)

        if not self.settings_file is None and self.settings_file != '':
            self.dump_to_file(self.settings_file)
        else:
            RuntimeError("Settings file path is not configured.")

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
            current_dict = current_dict[self._cast_string_to_correct_type(key)]
        return current_dict[self._cast_string_to_correct_type(splitname[-1])]

    """ This method deletes the value of key and sets it to None.

    The key itself will not be deleted. If you want to remove the key itself,
    call :func:`delete_key()`.

    .. note:: In case the value identified by key was set to contain
    subsequent dicts or lists, they will be cleared but not deleted.
    For example::
        settings.set_value('foo.0', 'bar')
        settings.set_value('foo.1', 'abc')
        settings.get_value('foo')
          ['bar', 'abc']
        settings.get_value('foo')
          []

    """
    def delete_value(self, key):
        values = self.get_value(key)
        if not values is None:
            if isinstance(values, list) or isinstance(values, dict):
                values.clear()
            else:
                self.set_value(key, None)

    """ Deletes a given key and all subsequent values from the settings dict.
    """
    def delete_key(self, keystring):
        splitname = [x for x in \
                map(self._cast_string_to_correct_type, keystring.split("."))]
        current_dict = self.settings_container
        for key in splitname[:-1]:
            if (isinstance(current_dict, dict) and key in current_dict) \
                or (isinstance(current_dict, list) and key >= 0 \
                        and key < len(current_dict)\
                ):
                current_dict = current_dict[key]
            else:
                raise KeyError("Key '%s' not found in settings." % key)
        del(current_dict[splitname[-1]])

    """ Clears all settings.
    """
    def clear(self):
        self.settings_container.clear()
    
    #Set Value actually creates the entry:
    def set_value(self,valuename,value):
        print("set_value: %s, type: %s" % (value, type(value)))
        splitname = [x for x in \
                map(self._cast_string_to_correct_type, valuename.split("."))]
        current_dict = self.settings_container
        # in order to prevent changes in settings already saved, check validity
        # of the specified keys first.
        for key in splitname:
            if current_dict is None \
                    or not (isinstance(current_dict, dict) \
                        or isinstance(current_dict, list) \
                    ):
                raise ValueError("already set to a constant.")
            elif isinstance(key, int) and isinstance(current_dict, dict):
                raise KeyError("key is int, but str is expected.")
            elif isinstance(key, str) and isinstance(current_dict, list):
                raise KeyError("key is str, but int is expected.")
            else:
                if isinstance(current_dict, dict):
                    if key in current_dict:
                        current_dict = current_dict[key]
                    else:
                        # this key has not been added to the list yet. => OK
                        break
                elif isinstance(current_dict, list):
                    if key < len(current_dict):
                        current_dict = current_dict[key]
                    elif isinstance(current_dict, list) and key == len(current_dict):
                        print("will be added, all save")
                        break
                    else: # key > len(current_dict)
                        raise IndexError("Out of range")
                else:
                    print("foo...: type: %s, key: %s" % (str(type(current_dict)), str(key)))
                    break

        current_dict = self.settings_container
        for key, nextkey in zip(splitname[:-1], splitname[1:]):
            #parsed_key = self._cast_string_to_correct_type(key)
            if isinstance(key, str) and not key in current_dict:
                if isinstance(nextkey, str):
                    current_dict[key] = {}
                    print("setting key %s to {}" % str(key))
                elif isinstance(nextkey, int):
                    current_dict[key] = []
                    print("setting key %s to []" % str(key))
            elif isinstance(key, int) and key == len(current_dict):
                print("lenght: %d" % len(current_dict))
                if isinstance(nextkey, str):
                    current_dict.append({})
                    print("appending {}")
                elif isinstance(nextkey, int):
                    current_dict.append([])
                    print("appending []")
            else:
                print("do nothing")
                pass

            current_dict = current_dict[key]
        key = splitname[-1] # self._cast_string_to_correct_type(splitname[-1])
        if isinstance(current_dict, list):
            if key >= 0 and key < len(current_dict):
                current_dict[key] = value
            elif key == len(current_dict):
                current_dict.append(value)
            else:
                raise IndexError('Out of range. You can only append consecutive list items.')
        elif isinstance(current_dict, dict):
            current_dict[key] = value

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
        for key,value in mydict.items():
            if isinstance(value, dict):
                self._recursive_helper_finish(value)
            else:
                if isinstance(value,string_types):
                    if value.startswith("sameas:"):
                        splitsameas = value.split(":")
                        mydict[key] = self.get_value(splitsameas[1])

    def _finish_parsing(self):
        self._recursive_helper_finish(self.settings_container)

    def _recursive_load(self, load, keystring=False):
        if isinstance(load, dict) or isinstance(load, list):
            items = load.items() if isinstance(load, dict) \
                    else enumerate(load)
            for key, value in items:
                new_keystr = "%s.%s" % (str(keystring), str(key)) if keystring \
                        else str(key)
                if isinstance(value, dict) or isinstance(value, list):
                    self._recursive_load(value, new_keystr)
                else:
                    print("Setting %s to %s" % (new_keystr, str(value)))
                    self.set_value(new_keystr, value)
        else:
            raise RuntimeError("Parsing error: key: %s, load: %s" % \
                    (keystring, load))

    """ Merges keys and values from the given dict into current settings.

    Keys that have been present before will be overwritten, non-existant keys
    will be created. Keys that are not present in the given dict will remain
    unchanged, which can be usefull for a partial update of default values.
    """
    def load_from_dict(self, to_parse):
        if not isinstance(to_parse, dict):
            raise ValueError("dict type is expected, got %s" % type(to_parse))
        self._recursive_load(to_parse)


class TestSettings(AbstractSettings):
    def __init__(self):
        super(TestSettings,self).__init__("TestSettings")
        print("loading...")
        with open('/tmp/settings', 'r') as infile:
            self.load_from_dict(yaml.load(infile))
            print("parsed...")
        self._finish_parsing()


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


if __name__ == '__main__':
    #Small unit test.  
    import os,sys
    
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
