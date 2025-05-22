from simstack.Constants import SETTING_KEYS


def test_setting_keys_exists():
    """Test that SETTING_KEYS is defined and is a dictionary."""
    assert isinstance(SETTING_KEYS, dict)
    assert len(SETTING_KEYS) > 0


def test_setting_keys_values():
    """Test that SETTING_KEYS contains the expected keys and values."""
    expected_keys = [
        "registries",
        "registry.name",
        "registry.username",
        "registry.sshprivatekey",
        "registry.extraconfig",
        "registry.port",
        "registry.baseURI",
        "registry.calculation_basepath",
        "registry.software_directory",
        "registry.queueing_system",
        "registry.default_queue",
        "registry.is_default",
        "wanoRepo",
        "workflows",
    ]

    # Check that all expected keys are in SETTING_KEYS
    for key in expected_keys:
        assert key in SETTING_KEYS

    # Check that all keys in SETTING_KEYS are in expected_keys
    for key in SETTING_KEYS:
        assert key in expected_keys

    # Check specific values
    assert SETTING_KEYS["registries"] == "registries"
    assert SETTING_KEYS["registry.name"] == "name"
    assert SETTING_KEYS["registry.username"] == "username"
    assert SETTING_KEYS["registry.sshprivatekey"] == "sshprivatekey"
    assert SETTING_KEYS["registry.extraconfig"] == "extraconfig"
    assert SETTING_KEYS["registry.port"] == "port"
    assert SETTING_KEYS["registry.baseURI"] == "baseURI"
    assert SETTING_KEYS["registry.calculation_basepath"] == "calculation_basepath"
    assert SETTING_KEYS["registry.software_directory"] == "software_directory"
    assert SETTING_KEYS["registry.queueing_system"] == "queueing_system"
    assert SETTING_KEYS["registry.default_queue"] == "default_queue"
    assert SETTING_KEYS["registry.is_default"] == "is_default"
    assert SETTING_KEYS["wanoRepo"] == "WaNo_Repository_Path"
    assert SETTING_KEYS["workflows"] == "workflow_path"
