from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .helpers import check_safety, decode_json
import types
from requests import Session
from requests import exceptions as reqexcept
from .Constants import ErrorCodes, HTTPStatusCodes
from .AuthProvider import AuthProvider
import json
import os
import logging
from simplejson import JSONDecodeError

CONST_VERIFY                = False
CONST_HEADERS_GET           = {'Accept': 'application/json'}
CONST_HEADERS_GET_FILE      = {'Accept': 'application/octet-stream'}
CONST_HEADERS_POST          = {'content-type': 'application/json'}
CONST_HEADERS_PUT_FILE      = {'content-type': 'application/octet-stream'}
CONST_HEADERS_IDENTITY      = {'Accept-Encoding': 'identity'}

#TODO 
# * status codes and error return values must match. Currently one might be
#   unset or set to success while the other one is not

class ChunkedUpload(object):
    """Helper class to support chunked file uploads.

    .. important:: Do not instantiate directly.
    """
    # from http://stackoverflow.com/a/13911048
    def __init__(self, filename, chunksize=1024, callback=None):
        self.filename   = filename
        self.chunksize  = chunksize
        self.callback   = callback
        self.totalsize  = os.path.getsize(filename)
        self.readsofar  = 0

    def __iter__(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    break
                self.readsofar += len(data)
                #percent = self.readsofar * 1e2 / self.totalsize
                if not self.callback is None:
                    self.callback(self.readsofar, self.totalsize)
                yield data

    def __len__(self):
        return self.totalsize

class IterableToFileAdapter(object):
    """Helper class to support chunked file uploads.

    .. important:: Do not instantiate directly.
    """
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    def read(self, size=-1): # TBD: add buffer for `len(data) > size` case
        return next(self.iterator, b'')

    def __len__(self):
        return self.length

class Connection:
    """This class maintains a network connection to the Unicore Server and
    handles all communication to and from the Server.

    Most of the methods offered by this class do not need to be invoked directly
    but are encapsulated by methods of the respective
    :class:`ServerPrimitive.ServerPrimitive`.
    """

    base_uri                    = None
    auth_provider               = None
    session                     = None
    set_user_callback           = None
    # _is_connected                = False

    def is_connected(self):
        """Returns true, if the connection to the Unicore Server has been
        established.

        Returns:
            true, if connected.
        """
        return self._is_connected

    @staticmethod
    def _http_status_is_success(status):
        return (status >= 200 and status < 300)

    @staticmethod
    def _http_status_is_client_error(status):
        return (status >= 400 and status < 500)

    def _exec_request(self, func, uri, args={}):
        resp = None
        err = ErrorCodes.NO_ERROR
        try:
            resp = func(uri, **args)
        except reqexcept.ConnectTimeout as e:
            self.logger.debug('Exception: %s' , str(e))
            err = ErrorCodes.CONN_TIMEOUT
        except reqexcept.Timeout as e:
            self.logger.debug('Exception: %s' , str(e))
            err = ErrorCodes.REQ_TIMEOUT
        except reqexcept.InvalidURL as e:
            self.logger.debug('Exception: %s' , str(e))
            err = ErrorCodes.INVALID_SETUP
        except reqexcept.SSLError as e:
            self.logger.debug('Exception: %s' , str(e))
            err = ErrorCodes.SSL_ERROR
        except reqexcept.ConnectionError as e:
            self.logger.debug('Exception: %s' , str(e))
            err = ErrorCodes.CONN_ERROR
        except Exception as e:
            self.logger.debug('Exception (unknown): %s' , str(e))
            err = ErrorCodes.UNKONWN_EXCPTION

        return (err, resp)

    @staticmethod
    def _get_status(resp):
        return resp.status_code if not resp is None \
                else HTTPStatusCodes.INVALID_STATUS

    def _get(self, uri, header, payload=None):
        self.logger.info('_get')
        args = {
                    'auth'      : self.auth_provider,
                    'headers'   : header,
                    'verify'    : CONST_VERIFY
                }
        if (not payload is None):
            args['payload'] = payload

        #resp = self.session.get(uri, **args)
        err, resp = self._exec_request(self.session.get, uri, args)
        self.logger.debug('GET [%d]: %s: %s',
                int(Connection._get_status(resp)), uri, str(err))
        return (err, resp)

    def _post(self, uri, data, header):
        self.logger.info('_post')
        args = {
                    'auth'      : self.auth_provider,
                    'headers'   : header,
                    'verify'    : CONST_VERIFY,
                    'data'      : data
               }
        err, resp = self._exec_request(self.session.post, uri, args)
        self.logger.debug('POST [%d]: %s to %s: %s',
                Connection._get_status(resp), data, uri, str(err))
        return (err, resp)

    def _put(self, uri, data, header, kwargs={}):
        self.logger.info('_put')
        args = kwargs
        args.update( {
                    'auth'      : self.auth_provider,
                    'headers'   : header,
                    'verify'    : CONST_VERIFY,
                    'data'      : data
               })
        err, resp = self._exec_request(self.session.put, uri, args)
        self.logger.debug('PUT [%d]: %s to %s: %s',
                Connection._get_status(resp),
                        data[:100 if len(data) > 100 else len(data)] \
                                if isinstance(data, str) else data,
                        uri, str(err))
        return (err, resp)

    def _delete(self, uri):
        args = {
                    'auth'      : self.auth_provider,
                    'headers'   : CONST_HEADERS_POST,
                    'verify'    : CONST_VERIFY,
               }
        err, resp = self._exec_request(self.session.delete, uri, args)
        self.logger.debug('DELETE [%d]: %s: %s',
                Connection._get_status(resp), uri, str(err))
        return (err, resp)

    @staticmethod
    def _is_valid_header(header):
        rv = False
        if (not header is None
                and header != ""
                and (header == CONST_HEADERS_PUT_FILE
                    or header == CONST_HEADERS_GET
                    or header == CONST_HEADERS_POST)
                ):
            rv = True
        return rv

    def post_uri(self, uri, data, header=None):
        """Sends data to the server via HTTP POST.

        Args:
            uri (str): the URI to the resource, relative to base_uri.

            data: arbitrary data (usually JSON) to send to the server.

            header: The header to use. If None, the default header will be used.

        Returns:
            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (:class:`requests.models.Response`):
            The response of the server. This will contain an empty
            string in most cases.
        """
        self.logger.info('post_uri')
        err = ErrorCodes.NO_ERROR
        resp = None
        data = data if not data is None else ""

        _header = header if Connection._is_valid_header(header) \
                else CONST_HEADERS_POST

        if (self._is_connected):
            check_safety([(uri, str), (data, str)])
            full_uri = "%s/%s" % (self.base_uri, uri)
            err, resp = self._post(full_uri, data, _header)
        else:
            err = ErrorCodes.NOT_CONNECTED

        return (err, resp)

    def open_uri(self, uri, header=None, payload=None):
        """Opens the given URI and returns its contents.

        Args:
            uri (str): the URI to the resource, relative to base_uri.

            header: The header to use. If None, the default header will be used.

            payload: data to send to the server as part of the URL.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (:class:`requests.models.Response`):
            The response of the server. This will contain an empty
            string in most cases.
        """
        self.logger.info('open_uri')
        err = ErrorCodes.NO_ERROR
        status = HTTPStatusCodes.INVALID_STATUS
        resp = None
        _header = header if Connection._is_valid_header(header) \
                else CONST_HEADERS_GET
        if (self._is_connected):
            check_safety([(uri, str)])
            full_uri = "%s/%s" % (self.base_uri, uri)
            err, resp = self._get(full_uri, _header, payload=payload)
            status = Connection._get_status(resp) if not resp is None else status
            err = ErrorCodes.HTTP_ERROR \
                if err == ErrorCodes.NO_ERROR \
                        and not Connection._http_status_is_success(status) \
                else err
        else:
            err = ErrorCodes.NOT_CONNECTED
        return (status, err, resp)

    def open_json_uri(self, uri, payload=None):
        """Convenience function, calls Connection.open_uri and returns the 
            response body as json.
        
        This function catches any kind of exceptions in case of decoding errors.
        Errors are indicated by the returned values.

        Args:
            uri (str): the URI to the resource, relative to base_uri.
        
            payload: data to send to the server as part of the URL.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            json (json, str):
            The JSON object might be empty ( {} ) if an error occurred.
        """
        self.logger.info('open_json_uri')

        json = {}
        status_code, err, resp       = self.open_uri(
                uri,
                header=CONST_HEADERS_GET,
                payload=payload
        )

        if (err == ErrorCodes.NO_ERROR and status_code == 200):
            try:
                json = decode_json(resp.content)
            except JSONDecodeError as e:
                err = ErrorCodes.DECODE_ERROR
                self.logger.error('JSONDecodeError: Could not decode response to json.')
                self.logger.debug('JSONDecodeError: Raw response: %s', resp.content)
                self.logger.debug('JSONDecodeError: msg: %s\ndoc: %s\npos: %d',
                        e.msg,
                        e.doc,
                        e.pos)
        return (status_code, err, json)

    def post_json(self, uri, jsondata):
        """Sends JSON data to the server via HTTP POST.

        Args:
            uri (str): the URI to the resource, relative to base_uri.

            jsondata: JSON data to send to the server.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (:class:`requests.models.Response`):
            The response of the server. This will contain an empty
            string in most cases.
        """
        self.logger.info('post_json')
    
        #TODO try catch
        data = json.dumps(jsondata)

        err, resp       = self.post_uri(uri, data, CONST_HEADERS_POST)
        status_code     = Connection._get_status(resp) if (
                err == ErrorCodes.NO_ERROR
                ) else HTTPStatusCodes.INVALID_STATUS

        return (status_code, err, resp)

    def put_file(self, uri, localfile, callback=None):
        """Sends a file to the server via HTTP PUT.

        This method has an optional parameter for a callback function, that
        will be called every time a chunk of the file has been uploaded.
        This can be used to refresh a progress bar, for example.
        The callback must have two parameters, the first one will be the
        amount of data uploaded so far, the second will be the total size of
        the file: ::

            def callback(read_so_far, total_filesize):
                # update progress bar.

        Args:
            uri (str): the URI to the resource, relative to base_uri.

            localfile (str): the local file to upload to the server.

            callback (func): a callback function.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (:class:`requests.models.Response`):
            The response of the server. This will contain an empty
            string in most cases.
        """
        full_uri = "%s/%s" % (self.base_uri, uri)

        it = ChunkedUpload(localfile, callback=callback)
        args = {'stream': True}
        err, resp       = self._put(full_uri, IterableToFileAdapter(it),
                CONST_HEADERS_PUT_FILE, args)

        #resp = self.session.put(full_uri,
        #        data=IterableToFileAdapter(it),
        #        #data= f,
        #        auth = self.auth_provider,
        #        verify = CONST_VERIFY,
        #        headers = CONST_HEADERS_POST,
        #        stream = True)
        #if (resp.status_code >= 300 or resp.status_code < 200):
        #    err = ErrorCodes.HTTP_ERROR
        #else:
        #    err = ErrorCodes.NO_ERROR

        status_code     = Connection._get_status(resp) if (
                err == ErrorCodes.NO_ERROR
                ) else HTTPStatusCodes.INVALID_STATUS

        return (status_code, err, resp)

    # TODO deprecated
    #def put_data(self, uri, data):
    #    self.logger.info('put_data')

    #    full_uri = "%s/%s" % (self.base_uri, uri)
    #    #TODO use http://stackoverflow.com/a/13911048
    #    err, resp       = self._put(full_uri, data, CONST_HEADERS_PUT_FILE)
    #    status_code     = Connection._get_status(resp) if (
    #            err == ErrorCodes.NO_ERROR
    #            ) else HTTPStatusCodes.INVALID_STATUS

    #    return (status_code, err, resp)


    def get_data(self, uri):
        self.logger.info('get_data')

        data = None
        err, resp       = self.open_uri(uri, CONST_HEADERS_GET_FILE)

        #TODO:
        #data = base64.b64decode(res.json()
        raise NotImplementedError("This method is not yet finished/tested.")
        status_code     = Connection._get_status(resp) if (
                err == ErrorCodes.NO_ERROR
                ) else HTTPStatusCodes.INVALID_STATUS

        return (status_code, err, data)

    def delete_uri(self, uri):
        resp = None
        status_code = 0
        err = ErrorCodes.NO_ERROR

        if (self._is_connected):
            check_safety([(uri, str)])
            full_uri = "%s/%s" % (self.base_uri, uri)
            err, resp = self._delete(full_uri)
            status_code     = Connection._get_status(resp) if (
                    err == ErrorCodes.NO_ERROR
                    ) else HTTPStatusCodes.INVALID_STATUS
        else:
            err = ErrorCodes.NOT_CONNECTED

        return (status_code, err, resp)


    def disconnect(self):
        """Disconnects from the server.
        
        Returns:
            true, if successful.
        """
        self.logger.info('disconnect')

        if (not self.session is None):
            self.session.close()
            self.session = None

        self._is_connected = False
        return not self._is_connected

    def connect(self):
        """Connects to the URI using the given AuthProvider.
        
        Returns:
            status_code: Standard HTTP status code of the request.
        """
        self.logger.info('connect')

        # Since the Unicore REST API does not (yet) support sessions, this function
        # does not create a session but rather tests login and url 

        # disconnect any previous session
        self.disconnect() 
        status_code = HTTPStatusCodes.Bad_Request
        err = ErrorCodes.INVALID_SETUP
        
        if (not self.base_uri is None) and (not self.auth_provider is None): 
            self.session = Session()
            # This needs to be set to 'cheat' the open_uri function
            self._is_connected = True
            status_code, err, respjson = self.open_json_uri('')

            if (err == ErrorCodes.NO_ERROR 
                    and Connection._http_status_is_success(status_code)
                ):
                if (not self.user_callback is None and 'client' in respjson):
                    self.user_callback(respjson['client'])
            elif (err == ErrorCodes.NOT_CONNECTED):
                self._is_connected = False
                self.logger.error('Connection could not be established.')
            else:
                self._is_connected = False
                self.logger.error('Connection got error: ErrorCode: %s', str(err))

        return (err, status_code)

    def send_files(self, uri, files):
        self.logger.info('send_files')

        check_safety([(uri, str), (files, [str])])
        #TODO
        pass

    def _get_dl_filesize(self, uri):
        args = {
                    'auth'      : self.auth_provider,
                    'verify'    : CONST_VERIFY,
                    'headers'   : CONST_HEADERS_IDENTITY
                }

        err, resp = self._exec_request(self.session.head, uri, args)
        return (err, resp.status_code,
            int(resp.headers['content-length']) if err == ErrorCodes.NO_ERROR \
                    else -1)

    def get_file(self, uri, localdest, callback=None):
        """ Downloads a file from the given url to a local file.

        The callback will be called on any progress of the download, the first
        parameter will be the already downloaded data in bytes, the second the
        total file size.
        This function **must not** block!
        Also note that the amount of downloaded data might exceed the file size
        for the last chunk of data.

        Note: This method will **not** check the input parameters in any way.
            Therefore, it is recommanded not to use this function direct but
            rather the wrapper functions in the Manager classes. 
        """
        chunk_count = 0
        chunk_size  = 1024

        full_uri = "%s/%s" % (self.base_uri, uri)

        #err, status, size   = self._get_dl_filesize(full_uri)
        status, err, json = self.open_json_uri(uri)
        size = json['size'] if err == ErrorCodes.NO_ERROR else 0

        print('size ', size)

        if (err == ErrorCodes.NO_ERROR
                    and Connection._http_status_is_success(status)):
            err, resp = self._exec_request(self.session.get, full_uri,
                    {'auth'      : self.auth_provider,
                    'headers'   : CONST_HEADERS_GET_FILE,
                    'stream':True})
            status = resp.status_code

            if (err == ErrorCodes.NO_ERROR
                    and Connection._http_status_is_success(status)):
                try:
                    with open(localdest, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                f.flush()
                                chunk_count += 1
                                if not callback is None:
                                        callback(
                                            min(chunk_count * chunk_size, size),
                                            size
                                        )
                except IOError as e:
                    self.logger.error('IOError when writing to %s:', localdest,
                            str(e))
                    err = ErrorCodes.FILE_IO_ERROR
                # TODO this also catches anything else in between -> hard to debug
                except Exception as e:
                    self.logger.error('Uexpected exception when writing to %s: %s',
                            localdest, str(e))
                    err = ErrorCodes.UNKONWN_EXCPTION
            else:
                self.logger.error('Failed to get data stream from %s: %s' \
                        % (uri, str(err)))
                err = ErrorCodes.HTTP_ERROR
        elif Connection._http_status_is_client_error(status):
            # This ErrorCode is only correct for 404, but unicore always returns
            # 401 on error....
            err = ErrorCodes.REMOTE_FILE_NOT_FOUND
        else:
            self.logger.error('Failed to determine download size of %s: %s' \
                    % (uri, str(err)))

        return status, err


    def get_auth_provider(self):
        self.logger.info('get_auth_provider')

        return self.auth_provider

    def set_auth_provider(self, auth_provider):
        self.logger.info('set_auth_provider')

        if (not auth_provider is None):
            check_safety([(auth_provider, AuthProvider)])
            self.auth_provider = auth_provider
        else:
            self.auth_provider = None
    
    def set_base_uri(self, base_uri):
        self.logger.info('set_base_uri')

        if (not base_uri is None):
            check_safety([(base_uri, str)])
            self.base_uri = base_uri.rstrip('\/') # remove trailing slash, if any
        else:
            self.base_uri = None

    def get_base_uri(self):
        return self.base_uri

    def get_auth_provider_hash(self):
        return self.auth_provider.get_hash()
    
    def _set_user_callback(self, callback):
        self.logger.info('_set_user_callback')

        if (not callback is None):
        #TODO type <bound method Registry._user_callback of <Registry.Registry instance at 0x7f55c2422320>>
        #    check_safety([(callback, types.FunctionType)])
            self.user_callback = callback
        else:
            self.user_callback = None

    def __init__(self, base_uri=None, auth_provider=None, user_callback=None):
        self.logger = logging.getLogger('pyura')
        self.logger.info('Initializing Connection')

        self.set_base_uri(base_uri)
        self.set_auth_provider(auth_provider)
        self._set_user_callback(user_callback)
        self.session = None
        self._is_connected = False
