from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.helpers import check_safety
 
class Application:
    """Unicore Server Side Application.
    """
    def get_application_name(self):
        """Returns the application's name.

        Return:
            name (str):   the application's name
        """
        return self.app_name

    def get_application_version(self):
        """Return the application's version.

        Return:
            version (str):   the application's version.
        """
        return self.app_version

    def __init__(self, name, version):
        """Initializes a new Application instance.
        """
        check_safety([(name, str), (version, str)])

        self.app_name       = name
        self.app_version    = version
