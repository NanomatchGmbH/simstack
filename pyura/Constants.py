# python < 3.3: requires enum34 package
from enum import Enum, IntEnum, EnumMeta


class _HTTPStatusCodes(IntEnum):
    """
    This Enum provides a bidirectional mapping from HTTP status codes to 
    easy-to-understand enum names and vice versa.

    .. note::
        This Enum is limited to the most important HTTP status codes.
        Not all available HTTP status codes are represented.
    """
    ## INVALID STATUS is returned when, for example, the requests is not executed at all and an error occures before.
    INVALID_STATUS            = -1
    OK                        = 200
    Resource_Created          = 201
    Accepted                  = 202
    No_Content                = 204
    Bad_Request               = 400 
    Unauthorized              = 401 
    Payment_Required          = 402 
    Forbidden                 = 403 
    Not_Found                 = 404 
    Request_Timeout           = 408 
    Gone                      = 410 
    Unsupported_Media_Type    = 415 
    Im_a_teapot               = 418 
    Authentication_Timeout    = 419 
    Upgrade_Required          = 426 
    Internal_Server_Error     = 500 
    Not_Implemented           = 501 
    Bad_Gateway               = 502 
    Service_Unavailable       = 503 

URIs = {
        'job_list':                 'jobs',
        'job_create':               'jobs',
        'job_sigle_job':            'jobs/%s',
        'job_delete':               'jobs/%s',
        'job_start':                'jobs/%s/actions/start',
        'job_restart':              'jobs/%s/actions/restart',
        'job_abort':                'jobs/%s/actions/abort',

        'storage_list':             'storages',
        'storage_create':           'storages',
        'storage_single_storage':   'storages/%s',
        'storage_file_list':        'storages/%s/files%s',
        'storage_file_upload':      'storages/%s/files/%s',
        'storage_file_download':    'storages/%s/files/%s',
        'storage_file_delete':      'storages/%s/files/%s',
        'storage_search':           'storages/%s/search',

        'sites_list':               'sites',
        'site_create':              'sites',
        'sites_delete':             'sites/%s',
        'sites_single_site':        'sites/%s',
        'sites_query_jobs':         'sites/%s/jobs',
        }
#URIs.__doc__ = """List of REST resource paths"""

JSONKeys = {
        'job_list':             'jobs',
        'job_executable':       'Executable',
        'job_arguments':        'Arguments',
        'job_client_stage_in':  'haveClientStageIn',
        'job_environment':      'Environment',
        'job_imports':          'Imports',
        'job_resources':        'Resources',
        'job_app':              'ApplicationName',
        'job_app_params':       'Parameters',

        'storage_list':         'storages',
        'storage_file_list':    'children',

        'sites_list':           'sites',
        }
#JSONKeys.__doc__ = """List of JSON key words in the REST API."""


# This class is required for proper documentation of the Enums.
#TODO check, why Enum values are not getting documented
class _AutoEnum(Enum):
    """
    Automatically numbers enum members starting from 1.

    Includes support for a custom docstring per member.

    Adapted from `http://stackoverflow.com/a/19330461 <http://stackoverflow.com/a/19330461>`.

    """
    __last_number__ = 0

    def __new__(cls, *args):
        """Ignores arguments (will be handled in __init__."""
        value = cls.__last_number__ + 1
        cls.__last_number__ = value
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, *args):
        """Can handle 0 or 1 argument; more requires a custom __init__.

        0  = auto-number w/o docstring
        1  = auto-number w/ docstring
        2+ = needs custom __init__

        """
        if len(args) == 1 and isinstance(args[0], str):
            self.__doc__ = args[0]
        elif args:
            raise TypeError('%s not dealt with -- need custom __init__' % (args,))

class Protocols(_AutoEnum):
    """
    List of supported file transfer protocols:

    * UFTP
    * BFT
    * RBYTEIO
    * SBYTEIO

    For more information please refer to
    `the Unicore Manual <https://www.unicore.eu/documentation/manuals/unicore/manual_installation.html#_data_transfer_with_uftp>`.
    """
    UFTP     = ""
    BFT      = ""
    RBYTEIO  = ""
    SBYTEIO  = ""

class JobStatus(_AutoEnum):
    """
    List of Job states:

    * QUEUED
    * RUNNING
    * READY
    * FAILED
    * SUCCESSFUL
    * ABORTED
    """ 
    QUEUED      = ""
    RUNNING     = ""
    READY       = ""
    FAILED      = ""
    SUCCESSFUL  = ""
    ABORTED     = ""

class ResourceStatus(_AutoEnum):
    """
    List of Resource states:

    * READY
    * UNAVAILABLE
    """
    READY = ""
    UNAVAILABLE = ""

class ErrorCodes(_AutoEnum):
    """
    List of Errors:

    * NO_ERROR
    * NOT_CONNECTED
    * DECODE_ERROR
    * EMPTY_RESPONSE
    * NOT_A_FILE
    * INVALID_QUERY
    * INVALID_SETUP
    * HTTP_ERROR
    * CONN_TIMEOUT
    * REQ_TIMEOUT
    * SSL_ERROR
    * CONN_ERROR
    * UNKONWN_EXCPTION
    * FILE_IO_ERROR
    * REMOTE_FILE_NOT_FOUND
    * RESOURCE_DOES_NOT_EXIST
    """

    NO_ERROR                    = ""
    NOT_CONNECTED               = ""
    DECODE_ERROR                = ""
    EMPTY_RESPONSE              = ""
    NOT_A_FILE                  = ""
    INVALID_QUERY               = ""
    INVALID_SETUP               = ""
    HTTP_ERROR                  = ""
    CONN_TIMEOUT                = ""
    REQ_TIMEOUT                 = ""
    SSL_ERROR                   = ""
    CONN_ERROR                  = ""
    UNKONWN_EXCPTION            = ""
    FILE_IO_ERROR               = ""
    REMOTE_FILE_NOT_FOUND       = ""
    RESOURCE_DOES_NOT_EXIST     = ""

HTTPStatusCodes = _HTTPStatusCodes

