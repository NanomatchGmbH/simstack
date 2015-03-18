import abc
from six import string_types
import logging
import yaml


stuff  = [ {'sect1': {'var1':'val1','var2':'val2'}},{'sect2':{'var1':'val1','var2':'val2'}}]

filename = 'test2.yml'
with open(filename,'w') as outfile:
    outfile.write(yaml.dump(stuff,default_flow_style=False))
            
            
stream = open('test2.yml', 'r')

#for token in yaml.scan(stream):
#   print token


print yaml.load(stream)
