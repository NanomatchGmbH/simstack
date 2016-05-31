"""
pyura.StorageManager
~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .Manager import Manager
from .Constants import URIs, JSONKeys, ErrorCodes
from .Storage import Storage
from os import path


#TODO 
# * What is returned if (given) storage id is not correct?
# * upload an download might require some kind of callback for status updates


class StorageManager(Manager):
    """The StorageManager controls and manages all storages of a user on the
    Unicore server and handles file up- and downloads.
    """
    def _get_id(self, storage_id):
        return self.selected.get_id() if storage_id is None else storage_id

    def get_file_list(self, storage_id=None, path=''):
        """Returns the list of files stored in a directory pointed to by the
        given path on the storage
        with the given id.

        Args:
            storage_id (str): Path to the storage that contains remote_file
            or None in order to use the currently selected one.

            path (str): location within the storage 

        Returns:
            List of files stored at the path.
        """
        files = []
        id = self._get_id(storage_id)

        fpath = '' if path is None or path == '' else path if (
                path[0] == '/') else '/' + path

        uri = URIs['storage_file_list'] % (id, fpath)
        status, err, json = self.con.open_json_uri(uri)

        if (status == 200 and err == ErrorCodes.NO_ERROR
                and JSONKeys['storage_file_list'] in json
        ):
            for f in json[JSONKeys['storage_file_list']]:
                files.append({
                        'name': f,
                        'path': f,
                        'type': 'd' if f[-1] == '/' else 'f'
                    })

        return files


    def get_file(self, remote_file, local_file, storage_id=None, callback=None):
        """Downloads a file from the remote Unicore server to a local file.


        .. warning:: existing local files will be overwritten without warning.
                Existence must be checked by caller.

        Args:
            remote_file (str): Path to the remote file.

            local_file (str): Path to the local file.

            storage_id (str): Path to the storage that contains remote_file
            or None in order to use the currently selected one.

            callback (func): Callback function. For more information on the
            callback function see :func:`Connection.get_file`.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        #TODO check parameters
        fremote_file = '' if (
                remote_file is None or remote_file == '') else remote_file if (
                    remote_file[0] == '/') else '/' + remote_file

        id = self._get_id(storage_id)
        err = ErrorCodes.NO_ERROR
        uri = URIs['storage_file_download'] % (id, remote_file)

        status, err = self.con.get_file(uri, local_file, callback=callback)

        return (status, err)
        

    def delete_file(self, remote_file, storage_id=None):
        """Deletes a given file on the remote Unicore server.

        Args:
            remote_file (str): Path to the remote file.

            storage_id (str): Path to the storage that contains remote_file
            or None in order to use the currently selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        # TODO check parameters
        id = self._get_id(storage_id)
        err = ErrorCodes.NO_ERROR

        uri = URIs['storage_file_delete'] % (id, remote_file)

        status, err, resp = self.con.delete_uri(uri)

        return (status, err)

    def upload_file(self, local_file, storage_id=None, remote_filename=None,
                callback=None):
        """Uploads a given local file to the remote Unicore server.

        If the remote_filename is None or empty, the basename of the local file
        will be used.

        Args:
            local_file (str): Path to the local file.

            storage_id (str): Path to the storage that contains remote_file
            or None in order to use the currently selected one.

            remote_filename (str): Path to the remote upload location.

            callback (func): Callback function. For more information on the
            callback *see :func:Connection.put_file()*.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            json (json, dict): server response
        """
        err = ErrorCodes.NO_ERROR;
        status = 0
        json = ''
        if (not path.isfile(local_file)):
            err = ErrorCodes.NOT_A_FILE
        else:
            id = self._get_id(storage_id)
            filename = remote_filename if (remote_filename != "" 
                    and not remote_filename is None
                    ) else path.basename(local_file)

            uri = URIs['storage_file_upload'] % (id, filename)

            #data = open(local_file, 'rb').read()
            #status, err, json = self.con.put_data(uri, data)
            status, err, json = self.con.put_file(uri, local_file, callback)
            #status, err, json = self.con.put_file(uri, local_file)
        return (status, err, json)

    def search(self, query, storage_id=None):
        """Search by a given query in the storage.

        Args:
            query (str): Search query.

            storage_id (str): Path to the storage that contains remote_file
            or None in order to use the currently selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            list: list of search results
        """
        check_safety([(query, str)])

        err = ErrorCodes.NO_ERROR
        status = 0
        json = ''
        rv_list = []
        uri = ''
        id = self._get_id(storage_id)

        if (query is None or query == ''):
            err = ErrorCodes.INVALID_QUERY
        else:
            payload = {'q', query}
            uri = URIs['storage_search'] % (id)

            status, err, json = self.con.open_json_uri(uri, payload=payload)

        if (status == 200 and err == ErrorCodes.NO_ERROR):
            numberOfResults = json['numberOfResults']

            for n in range(1, (numberOfResults + 1)):
                key = "search-result-%d" % n
                rv_list.append(json['_links'][key])

            # TODO should we check, if len(rv_list) == numberOfResults??

        return (status, err, rv_list)

    def create(self):
        """Creates a new storage.

            .. note:: This method is currently does not accept any parameters
                due to a lack of documentation.

        Returns:
            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            storage (:class:`Sorage.Sorage`): Representation of the newly
            created site on the server. This will be None in an error case.
        """
        #TODO there is no description in the docs. This might follow the
        # specifications for ucc in section 8.6 of the ucc manual.
        # There is also no comment on any json format to specify storage
        # name, type, etc.
        return self._create(URIs['storage_create'], {}, Storage)

    def update_list(self):
        # Documented in parent class.
        self._update_list(
                URIs['storage_list'],
                JSONKeys['storage_list'],
                Storage
                )
        if len(self.list) > 1:
            self.select(self.list[0])
            print('Autoselected storage site: %s' % self._get_id(None))

    def __init__(self, connection):
        super(StorageManager, self).__init__(connection)
