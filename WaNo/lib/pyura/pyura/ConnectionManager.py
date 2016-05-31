from enum import Enum
import logging

from .Connection import Connection
from .Constants import ConnectionState, ErrorCodes, JSONKeys


class ConnectionManager:
    @staticmethod
    def _extract_base_uri(uri):
        u = uri['href'] if 'href' in uri else uri
        return '/'.join(u.split('/')[:-1]) if not u is None else None

    def get_job_base_uri(self):
        return self._connections['job']['uri']

    def get_factory_base_uri(self):
        return self._connections['factory']['uri']

    def get_transfer_base_uri(self):
        return self._connections['transfer']['uri']

    def get_registry_base_uri(self):
        return self._connections['registry']['uri']

    def get_storagefactory_base_uri(self):
        return self._connections['storagefactory']['uri']

    def get_storage_base_uri(self):
        return self._connections['storage']['uri']

    def get_site_base_uri(self):
        return self._connections['site']['uri']

    def get_workflow_base_uri(self):
        return self._connections['workflow']['uri']


    def get_job_connection(self):
        return self._connections['job']['con']

    def get_factory_connection(self):
        return self._connections['factory']['con']

    def get_transfer_connection(self):
        return self._connections['transfer']['con']

    def get_registry_connection(self):
        return self._connections['registry']['uri']

    def get_storagefactory_connection(self):
        return self._connections['storagefactory']['con']

    def get_storage_connection(self):
        return self._connections['storage']['con']

    def get_site_connection(self):
        return self._connections['site']['con']

    def get_workflow_connection(self):
        return self._connections['workflow']['con']

    def _find_by_uri(self, uri):
        con = None
        for key in self._connections:
            if self._connections[key]['uri'] == uri \
                    and not self._connections[key]['con'] is None:
                con = self._connections[key]['con']
                break
        return con

    def _usage(self, con):
        usage = []
        for key in self._connections:
            if self._connections[key]['con'] == con:
                usage.append(key)
        return usage

    def _replace_connection(self, key, con):
        self.logger.info("_replace_connection")
        old_con = self._connections[key]['con']
        self._connections[key]['con'] = None

        if not old_con is None:
            old_con_usage = self._usage(old_con)
            if len(old_con_usage) == 0:
                old_con.disconnect()

        self._connections[key]['con'] = con
        if not con is None:
            self.logger.info("Connection for '%s' to '%s' established." % \
                    (key, self._connections[key]['uri']))
        else:
            self.logger.info("Removed connection for '%s'." % key)
            
    def _setup_connection(self, key, auth_provider):
        self.logger.info("_setup_connection")
        uri = self._connections[key]['uri']
        con = self._find_by_uri(uri)
        if con is None:
            con = Connection(base_uri=uri, auth_provider=auth_provider)
            print("connecting %s" % key)
            err, status, resp = con.connect()
            if err != ErrorCodes.NO_ERROR:
                self.logger.error(
                        "Could not establish connection for '%s' to '%s'." % \
                                (key, uri))
                #TODO inform user -> callback
                con = None
        self._replace_connection(key, con)
        print("connected %s: %s" % (key, self._connections[key]))


    def _connect_all(self, auth_provider):
        self.logger.info("_connect_all")
        for key in self._connections:
            if key == 'registry':
                continue
            print("%s\t\t: %s" % (key, self._connections[key]))
            self._setup_connection(
                    key, auth_provider)

    def _set_base_uri(self, key, uri, auto):
        self._connections[key]['uri'] = uri
        self._connections[key]['auto'] = auto

    def _autoset_uri(self, key, uri):
        if self._connections[key]['auto']:
            print("auto setted: %s" % key)
            self._set_base_uri(
                    key,
                    uri,
                    (key != 'registry')) # the registry uri is not auto-settable

    def _autoset_unparsed_uri(self, key, uri):
        if not uri is None and uri != '':
            parsed = ConnectionManager._extract_base_uri(uri)
            if not parsed is None:
                self._autoset_uri(key, parsed)
            else:
                #TODO tell user!
                self.logger.error("Could not parse uri: %s." % str(uri))

    def set_job_base_uri(self, uri):
        self._set_base_uri('job', uri, False)

    def set_factory_base_uri(self, uri):
        self._set_base_uri('factory', uri, False)

    def set_transfer_base_uri(self, uri):
        self._set_base_uri('transfer', uri, False)

    def set_registry_base_uri(self, uri):
        self._set_base_uri('registry', uri, False)

    def set_storagefactory_base_uri(self, uri):
        self._set_base_uri('storagefactory', uri, False)

    def set_storage_base_uri(self, uri):
        self._set_base_uri('storage', uri, False)

    def set_site_base_uri(self, uri):
        self._set_base_uri('site', uri, False)

    def set_workflow_base_uri(self, uri):
        self._set_base_uri('workflow', uri, False)

    def __handle_registry_response(self, resp, user_callback=None):
        if (JSONKeys['registry_client_info'] in resp \
                    and not user_callback is None):
            user_callback(resp[JSONKeys['registry_client_info']])
        if JSONKeys['registry_link_list'] in resp:
            uris = resp[JSONKeys['registry_link_list']]
            self._autoset_unparsed_uri('job', uris[JSONKeys['registry_link_jobs']])
            self._autoset_unparsed_uri('factory', uris[JSONKeys['registry_link_factories']])
            self._autoset_unparsed_uri('transfer', uris[JSONKeys['registry_link_transfers']])
            self._autoset_unparsed_uri('storagefactory', uris[JSONKeys['registry_link_storagefactories']])
            self._autoset_unparsed_uri('storage', uris[JSONKeys['registry_link_storages']])
            self._autoset_unparsed_uri('site', uris[JSONKeys['registry_link_sites']])
            #TODO 
            self._autoset_unparsed_uri('workflow', '')

    def _autoset_connections(self, con):
        for key in self._connections:
            if self._connections[key]['auto']:
                self._connections[key]['con'] = con

    def _inform(self, connection, old_state, new_state):
        if not self._connection_info_cb is None:
            self._connection_info_cb(connection, old_state, new_state)

    def connect(self, auth_provider, user_callback=None):
        # TODO save status per connection, use _inform on any status change
        con_status = ConnectionState.CONNECTING

        if not self._connections['registry']['uri'] is None \
                and self._connections['registry']['uri'] != "":

            registry_con = Connection(
                    base_uri=self._connections['registry']['uri'],
                    auth_provider=auth_provider)

            #TODO handle registry respones synchronously, not by callback
            err, status, resp = registry_con.connect()
            print("err: %s, status: %s\nresp: %s" % (str(err), str(status), resp))
            if err == ErrorCodes.NO_ERROR:
                self._connections['registry']['con'] = registry_con
                self.__handle_registry_response(resp, user_callback)
                self._autoset_connections(registry_con)

                self.logger.info("Connected to registry @ '%s'" % \
                            str(self._connections['registry']['uri']))
                self._connect_all(auth_provider)
                con_status = ConnectionState.CONNECTED
            else:
                con_status = ConnectionState.FAILED
        else:
            con_status = ConnectionState.NOT_SETUP

        return (err, con_status)

    def reset_uris(self, base_uri):
        self._connections = {
            # the registry uri is not auto-settable
            "registry":         {'uri': base_uri, 'con': None, 'auto': False},
            "job":              {'uri': base_uri, 'con': None, 'auto': True},
            "factory":          {'uri': base_uri, 'con': None, 'auto': True},
            "transfer":         {'uri': base_uri, 'con': None, 'auto': True},
            "storagefactory":   {'uri': base_uri, 'con': None, 'auto': True},
            "storage":          {'uri': base_uri, 'con': None, 'auto': True},
            "site":             {'uri': base_uri, 'con': None, 'auto': True},
            "workflow":         {'uri': base_uri, 'con': None, 'auto': True},
        }

    def disconnect(self):
        for key in self._connections:
            con = self._connections[key]['con']
            if not con is None:
                usages = self._usage(con)
                con.disconnect()
                for ukey in usages:
                    self._connections[ukey]['con'] = None
                del(con)

    def __init__(self, base_uri=None):
        self._global_status         = ConnectionState.INVALID
        self.logger                 = logging.getLogger('pyura')
        self._connection_info_cb    = None
        self.reset_uris(base_uri)
