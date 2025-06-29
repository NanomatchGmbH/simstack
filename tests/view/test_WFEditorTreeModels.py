import pytest
from unittest.mock import patch

from simstack.view.WFEditorTreeModels import (
    DATA_TYPE,
    DataNode,
    WFEFileSystemEntry,
    WFERemoteFileSystemEntry,
    WFERemoteFileSystemModel,
)


class TestDataType:
    """Tests for the DATA_TYPE enum class."""

    def test_data_type_values(self):
        """Test DATA_TYPE enum values."""
        # Test a few enum values to ensure they're defined correctly
        assert DATA_TYPE.FILE.value == 0
        assert DATA_TYPE.DIRECTORY.value == 1
        assert DATA_TYPE.UNKNOWN.value == 2
        assert DATA_TYPE.LOADING.value == 3
        assert DATA_TYPE.JOB_QUEUED.value == 8
        assert DATA_TYPE.JOB_RUNNING.value == 9
        assert DATA_TYPE.WF_SUCCESSFUL.value == 19


class TestDataNode:
    """Tests for the DataNode class."""

    @pytest.fixture
    def data_node(self):
        """Create a DataNode instance."""
        return DataNode("test_data")

    @pytest.fixture
    def parent_node(self):
        """Create a parent DataNode instance."""
        return DataNode("parent_data")

    def test_init(self, data_node):
        """Test initialization of DataNode."""
        assert data_node._data == "test_data"
        assert data_node._parent is None
        assert data_node._children == []

    def test_init_with_parent(self, parent_node):
        """Test initialization with parent."""
        child_node = DataNode("child_data", parent_node)

        # Verify parent-child relationship
        assert child_node._parent is parent_node
        assert child_node in parent_node._children
        assert len(parent_node._children) == 1

    def test_set_parent(self, data_node, parent_node):
        """Test setParent method."""
        # Set parent
        data_node.setParent(parent_node)

        # Verify parent was set
        assert data_node._parent is parent_node
        assert data_node in parent_node._children

        # Test setting parent to None
        data_node.setParent(None)
        assert data_node._parent is None

        # Original parent should still have the child in its list
        # (setParent doesn't remove from original parent)
        assert data_node in parent_node._children

    def test_append_child(self, data_node):
        """Test appendChild method."""
        # Create child node without parent relationship
        child_node = DataNode("child_data")

        # Add as child
        data_node.appendChild(child_node)

        # Verify child was added
        assert child_node in data_node._children
        assert len(data_node._children) == 1

        # Parent relationship is not automatically set by appendChild
        assert child_node._parent is None

    def test_child_at_row(self, parent_node):
        """Test childAtRow method."""
        # Create child nodes
        child1 = DataNode("child1", parent_node)
        child2 = DataNode("child2", parent_node)

        # Verify children can be retrieved by row
        assert parent_node.childAtRow(0) is child1
        assert parent_node.childAtRow(1) is child2

        # Test invalid row
        assert parent_node.childAtRow(-1) is None
        assert parent_node.childAtRow(2) is None

    def test_row_of_child(self, parent_node):
        """Test rowOfChild method."""
        # Create child nodes
        child1 = DataNode("child1", parent_node)
        child2 = DataNode("child2", parent_node)

        # Verify row indices
        assert parent_node.rowOfChild(child1) == 0
        assert parent_node.rowOfChild(child2) == 1

        # Test for non-child
        non_child = DataNode("non_child")
        assert parent_node.rowOfChild(non_child) == -1

    def test_remove_child(self, parent_node):
        """Test removeChild method."""
        # Create child nodes
        DataNode("child1", parent_node)
        child2 = DataNode("child2", parent_node)

        # Remove first child
        result = parent_node.removeChild(0)

        # Verify child was removed
        assert result is True
        assert len(parent_node._children) == 1
        assert parent_node.childAtRow(0) is child2

    def test_len(self, parent_node):
        """Test __len__ method."""
        # Create child nodes
        DataNode("child1", parent_node)
        DataNode("child2", parent_node)

        # Verify length
        assert len(parent_node) == 2

    def test_abstract_methods(self, data_node):
        """Test abstract methods raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            data_node.getText()

        with pytest.raises(NotImplementedError):
            data_node.getIconType()

    def test_get_parent(self, data_node, parent_node):
        """Test getParent method."""
        # Set parent
        data_node.setParent(parent_node)

        # Verify getParent returns the parent
        assert data_node.getParent() is parent_node


class TestWFEFileSystemEntry:
    """Tests for the WFEFileSystemEntry class."""

    @pytest.fixture
    def file_entry_data(self):
        """Create data for a file entry."""
        return WFEFileSystemEntry.createData("path", "abspath", DATA_TYPE.FILE)

    @pytest.fixture
    def dir_entry_data(self):
        """Create data for a directory entry."""
        return WFEFileSystemEntry.createData("path", "abspath", DATA_TYPE.DIRECTORY)

    @pytest.fixture
    def file_entry(self, file_entry_data):
        """Create a WFEFileSystemEntry instance for a file."""
        return WFEFileSystemEntry(file_entry_data)

    @pytest.fixture
    def dir_entry(self, dir_entry_data):
        """Create a WFEFileSystemEntry instance for a directory."""
        return WFEFileSystemEntry(dir_entry_data)

    def test_init(self, file_entry, file_entry_data):
        """Test initialization of WFEFileSystemEntry."""
        assert file_entry._data == file_entry_data

    def test_get_absolute_path(self, file_entry):
        """Test getAbsolutePath method."""
        assert file_entry.getAbsolutePath() == "abspath"

    def test_get_path(self, file_entry):
        """Test getPath method."""
        assert file_entry.getPath() == "path"

    def test_get_text(self, file_entry):
        """Test getText method."""
        assert file_entry.getText() == "path"

    def test_get_data_type(self, file_entry, dir_entry):
        """Test getDataType method."""
        # Explicit data type
        assert file_entry.getDataType() == DATA_TYPE.FILE
        assert dir_entry.getDataType() == DATA_TYPE.DIRECTORY

        # Test implicit type based on children
        entry_without_type = WFEFileSystemEntry(
            WFEFileSystemEntry.createData("path", "abspath")
        )
        assert entry_without_type.getDataType() == DATA_TYPE.FILE  # No children -> file

        # Add a child to make it a directory
        child = WFEFileSystemEntry(
            WFEFileSystemEntry.createData("child", "abspath/child")
        )
        entry_without_type.appendChild(child)
        assert (
            entry_without_type.getDataType() == DATA_TYPE.DIRECTORY
        )  # Has children -> directory

    def test_get_icon_type(self, file_entry):
        """Test getIconType method."""
        # getIconType should return the same as getDataType
        assert file_entry.getIconType() == file_entry.getDataType()

    def test_create_data(self):
        """Test createData static method."""
        data = WFEFileSystemEntry.createData("path", "abspath", DATA_TYPE.FILE)

        assert data == {
            "path": "path",
            "abspath": "abspath",
            "data_type": DATA_TYPE.FILE,
        }

        # Test without data_type
        data = WFEFileSystemEntry.createData("path", "abspath")
        assert data == {"path": "path", "abspath": "abspath", "data_type": None}


class TestWFERemoteFileSystemEntry:
    """Tests for the WFERemoteFileSystemEntry class."""

    @pytest.fixture
    def entry_data(self):
        """Create data for a remote file system entry."""
        return WFERemoteFileSystemEntry.createData(
            id="entry_id",
            name="entry_name",
            path="path",
            abspath="abspath",
            data_type=DATA_TYPE.FILE,
            status="successful",
            original_result_directory=None,
        )

    @pytest.fixture
    def entry(self, entry_data):
        """Create a WFERemoteFileSystemEntry instance."""
        return WFERemoteFileSystemEntry(entry_data)

    def test_init(self, entry, entry_data):
        """Test initialization of WFERemoteFileSystemEntry."""
        assert entry._data == entry_data

    def test_get_name(self, entry):
        """Test getName method."""
        assert entry.getName() == "entry_name"

        # Test fallback to ID when name is empty
        entry._data["name"] = ""
        assert entry.getName() == "entry_id"

    def test_get_id(self, entry):
        """Test getID method."""
        assert entry.getID() == "entry_id"

    def test_get_status(self, entry):
        """Test getStatus method."""
        assert entry.getStatus() == "successful"

    def test_get_icon_type(self, entry):
        """Test getIconType method for regular file."""
        # For a file, it should return the data type
        assert entry.getIconType() == DATA_TYPE.FILE

        # Mock job entry with successful status
        job_data = WFERemoteFileSystemEntry.createData(
            id="job_id",
            name="job_name",
            path="job_path",
            abspath="job_abspath",
            data_type=WFERemoteFileSystemModel.DATA_TYPE_JOB,
            status="SUCCESSFUL",
        )
        job_entry = WFERemoteFileSystemEntry(job_data)

        # Test job iconType - should look up in JOB_STATUS_TO_DATA_TYPE
        with patch(
            "simstack.view.WFEditorTreeModels.JOB_STATUS_TO_DATA_TYPE",
            {job_entry.getStatus(): DATA_TYPE.JOB_SUCCESSFUL},
        ):
            assert job_entry.getIconType() == DATA_TYPE.JOB_SUCCESSFUL

        # Test reused result
        job_data["original_result_directory"] = "original_dir"
        assert job_entry.getIconType() == DATA_TYPE.JOB_REUSED_RESULT

    def test_create_data(self):
        """Test createData static method."""
        data = WFERemoteFileSystemEntry.createData(
            id="entry_id",
            name="entry_name",
            path="path",
            abspath="abspath",
            data_type=DATA_TYPE.FILE,
            status="successful",
            original_result_directory="original_dir",
        )

        assert data == {
            "id": "entry_id",
            "name": "entry_name",
            "path": "path",
            "abspath": "abspath",
            "data_type": DATA_TYPE.FILE,
            "status": "successful",
            "original_result_directory": "original_dir",
        }

        # Test with defaults
        data = WFERemoteFileSystemEntry.createData(
            id="entry_id", name="entry_name", path="path", abspath="abspath"
        )
        assert data["status"] is None
        assert data["original_result_directory"] is None
