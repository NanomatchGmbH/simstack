from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .Manager import Manager
from .Constants import URIs, JSONKeys, ErrorCodes
from .Site import Site


#TODO
# * move _get_id upwards into Manager

class SiteManager(Manager):
    """The SiteManager controls and manages Unicore sites."""

    def _get_id(self, site):
        id = ''
        if (site is None or site == ''):
            id = self.selected.get_id()
        else:
            if (isinstance(site, Site)):
                id = site.get_id()
            elif (isinstance(site, str)):
                id = site
            else:
                raise TypeError('Got site object of wrong type (%s), ' \
                        'expected %s or %s' % (
                    str(type(site)), str(Site), str(str)))
        return id

    def create(self):
        """Creates a new site.

            .. note:: This method is currently does not accept any parameters
                due to a lack of documentation.

        Returns:
            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            site (:class:`Site.Site`): Representation of the newly created
            site on the server.
            This will be None in an error case.
        """
        return self._create(URIs['site_create'], {}, Storage)

    def delete(self, site=None):
        """Deletes a site.

        If no site is given as parameter, the currently selected site is
        deleted.

        Args:
            site (str, Site): (optional) the site to delete.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        id = self._get_id(site)
        uri = URIs['sites_delete'] % id
        status, err, resp = self.con.delete_uri(uri)

        # This combination of return values only appears if one tries to delete
        # a site that has already been deleted.
        if status == HTTPStatusCodes.Internal_Server_Error \
                and err == ErrorCodes.NO_ERROR:
            err = ErrorCodes.RESOURCE_DOES_NOT_EXIST

        return (status, err)

    #TODO where should this be placed? here or in JobManager?
    def submit_job_to_site(self, site=None): # ...
        # The call is the same as in JobManager.create.
        raise NotImplementedError('Not yet implemented.')

    def get_jobs_on_site(self, site=None, offset=0, num=None):
        """Returns a list of jobs that are currently executed or have been
        executed on the site.

        Returns:
            jobs ([]):  list of jobs on the site.
        """
        id = self._get_id(site)
        uri = URIs['sites_query_jobs'] % id
        payload = {}
        rv = []
        
        if (isinstance(offset, int) and offset >= 0):
            payload['offset'] = offset
        
        if (isinstance(num, int) and num >= 0):
            payload['num'] = num

        status, err, json = self.con.open_json_uri(uri, payload)

        if (status == 200 and err == ErrorCodes.NO_ERROR):
            for j in json[JSONKeys['sites_resp_job_query']]:
                rv.append(ServerPrimitive.get_id_from_uri(j))

        return (status, err, rv)

    
    def update_list(self):
        # Documented in parent class.
        self._update_list(URIs['sites_list'], JSONKeys['sites_list'], Site)


    def __init__(self, connection):
        super(SiteManager, self).__init__(connection)

