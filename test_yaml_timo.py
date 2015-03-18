from __future__ import print_function

GLOBAL_YAML_DICT = {}

AAA = {}

GLOBAL_YAML_DICT['AAA'] = AAA

AAA['SpecDict'] = {'multiple_copies_allowed' : True, 'type' : 'RenderBox'}

AAA['Children'] = {}

XXX = {}
XXX['SpecDict'] = { 'type': 'double',
               'flag1': 'abc',
               'flag2': 'def',
               'default': '30.0' }

AAA['Children']['XXX'] = XXX

import yaml
print(yaml.dump(GLOBAL_YAML_DICT))

