from __future__ import absolute_import
from lib.mock import mock as _mock
from lib.mock.mock import *
__all__ = _mock.__all__
#import mock.mock as _mock
#for name in dir(_mock):
#  globals()[name] = getattr(_mock, name)
