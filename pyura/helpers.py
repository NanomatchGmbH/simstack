from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import simplejson
import sys
#from datetime import datetime
from dateutil.parser import parse as parse_date


def convert_date_time(string):
#    return datetime.strptime(string, '%Y-%m-%dT%H:%M:%S%z')
    return parse_date('2015-07-15T11:42:13+0200')


def get_enum_by_str(enum, string):
    rv = None
    for e in enum:
        if (e.name == string):
            rv = e
            break
    return rv

def get_enums_by_strs(enum, strings):
    rv = []
    for s in strings:
        rv.append(get_enum_by_str(enum, s))
    return rv
            

def is_in_list(l, e):
    #TODO this is kind of hackish...
    rv = True
    try:
        i = l.index(e)
    except:
        rv = False
    return rv

def _check_list_safety(check_list, list_type):
    rv = True
    for i,l in enumerate(check_list):
        if not isinstance(l, list_type):                     
            raise TypeError('List element %d (%s) of wrong type, expected %s' % (
                i, str(l), str(list_type)
                ))

def check_safety(check_me):
    rv = True
    for l in check_me:
        if isinstance(l[0], list) and isinstance(l[1], list):
            _check_list_safety(l[0], l[1][0])
        elif isinstance(l[1], list):
            raise ValueError(
                'Type field can only be of type list if the element to check is also a list.'
                )
        else:
            if not isinstance(l[0], l[1]):
                raise TypeError('Invalid type %s (%s), expected %s' % (
                    str(l[0]), str(type(l[0])), str(l[1]))
                    ) 
                rv = False
                break
    return rv

# from http://stackoverflow.com/a/6633651
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, str) \
                or sys.version_info.major < 3 and isinstance(item, unicode):
            item = item.encode('utf-8') if sys.version_info.major < 3 else item
        elif isinstance(item, bytes):
            item = item.decode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

# from http://stackoverflow.com/a/6633651
def _decode_dict(data):
    rv = {}
    for key, value in data.items():
        if isinstance(key, str) \
                or sys.version_info.major < 3 and isinstance(key, unicode):
            key = key.encode('utf-8') if sys.version_info.major < 3 else key
        elif isinstance(key, bytes):
            key = key.decode('utf-8')
        else:
            raise ValueError("Key %s has unexpected type %s" % (key, type(key)))

        if isinstance(value, str) \
                or sys.version_info.major < 3 and isinstance(value, unicode):
            value = value.encode('utf-8') \
                    if sys.version_info.major < 3 else value
        elif isinstance(value, bytes):
            value = value.decode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        elif isinstance(value, bool) \
                or isinstance(value, int) \
                or isinstance(value, float):
            value = value
        else:
            raise ValueError(
                    "Value %s for key %s has unexpected type %s" % 
                    (str(value), str(key), type(value))
                )
        rv[key] = value
    return rv

def __decode(string):
    if sys.version_info.major < 3:
        return string
    else:
        print("foo: %s " % type(string))
        return string.decode("utf-8")

def decode_json(string):
    """Converts string to JSON without unicode elements."""
    return simplejson.JSONDecoder.decode(
        simplejson.JSONDecoder(
                encoding='utf-8',
                object_hook=_decode_dict
                ),
        string
        ) 
