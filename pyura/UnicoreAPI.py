from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .Registry import Registry
from .AuthProvider import AuthProvider
import logging

_registries = []
_logger = None
_init_state = False

def _search_in_registries(base_uri, auth_provider):
    rv = (None, None)
    auth_hash = auth_provider.get_hash() \
            if isinstance(auth_provider, AuthProvider) \
            else auth_provider
    for i, r in enumerate(_registries):
        if (base_uri == r.get_base_uri() \
                and (not auth_provider is None
                    and auth_provider == r.get_auth_provider_hash()
                ) or auth_provider is None
        ):
            rv = (r, i)
            break
        else:
            print("%s vs %s" % (base_uri, r.get_base_uri()))
    return rv

def _check_init_state():
    if not _init_state:
        raise RuntimeError("The UnicoreAPI must be initialized first.")

def init():
    """Initializes pyura.

    This method **must** be called prior to any other API call.
    """
    global _logger
    global _init_state
    if not _init_state:
        _logger = logging.getLogger('pyura')
        _init_state = True

def add_registry(base_uri, auth_provider):
    """Adds a registry.

    Multiple registries can be managed in a list of unique registries.
    If a registry should be added with the same arguments as one that has been
    added before, the existing one is returned.

    Args:
        base_uri (str): URI pointing to a Unicore REST service.
        auth_provider (:class:`AuthProvider.AuthProvider`): Authentication
        provider that can be used to log in.

    Returns:
        registry (:class:`Registry.Registry`): a fresh created or previously
        existing registry.
    """
    global _registries

    _check_init_state()

    if base_uri is None:
        raise ValueError("A base URI is required to create a Registry.")

    if auth_provider is None:
        raise ValueError("An Authentication provider is required to "\
                "create a Registry.")

    reg, idx = _search_in_registries(base_uri, auth_provider)
    if reg is None:
        reg = Registry(base_uri, auth_provider)
        _registries.append(reg)
        _logger.info("Added new Registry: %s." % base_uri)
    else:
        _logger.info("Registry already exists, returning known one.")
    return reg

def remove_registry(registry):
    """Removes a given registry from the list of managed registries.

    .. note:: The registry's connection should be closed first.

    Args:
        registry: A :class:`Registry.Registry` or a tuple containing a
        base URI and an authentication provider.

    Returns:
        true on success, false otherwise.
    """
    global _registries
    base_uri = None
    auth_hash = None
    rv = False

    if (isinstance(registry, Registry)):
        base_uri = registry.get_base_uri()
        auth_hash = registry.get_auth_provider_hash()
    elif (isinstance(registry, tuple) and len(registry) == 2 \
            and isinstance(registry[0], str) \
            and isinstance(registry[1], AuthProvider)
    ):
        base_uri = registry[0]
        auth_hash = registry[1].get_hash()
    else:
        raise ValueError("registry must be either of type Registry or a tuple "\
            "containing a base URI string and an authentication provider."
        )

    if (base_uri is None):
        raise ValueError("Could not determine base URI.")
    if (auth_hash is None):
        raise ValueError("Could not determine authentication provider.")

    reg, idx = _search_in_registries(base_uri, auth_hash)
    if not reg is None:
        reg = _registries.pop(idx)
        del reg
        rv = True

    return rv


def get_registries():
    """Returns the list of managed registries.

    Returns:
        registries: list of managed registries.
    """
    _check_init_state()

    return _registries
