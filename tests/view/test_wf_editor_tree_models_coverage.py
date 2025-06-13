"""Comprehensive tests for WFEditorTreeModels.py - Focus on improving coverage."""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QModelIndex, Qt

from simstack.view.WFEditorTreeModels import (
    DATA_TYPE,
    DataNode,
    DataTreeModel,
    WFEFileSystemEntry,
    WFEFileSystemModel,
    WFERemoteFileSystemEntry,
    WFERemoteFileSystemModel,
    JOB_STATUS_TO_DATA_TYPE,
    WF_STATUS_TO_DATA_TYPE,
)
from SimStackServer.MessageTypes import JobStatus


class TestDataTreeModel:
    """Test DataTreeModel methods for better coverage."""

    @pytest.fixture
    def model(self):
        """Create a mock DataTreeModel instance."""

        class TestableDataTreeModel(DataTreeModel):
            def _getDecorationIcon(self, index):
                return None

            def createNode(self, data, parent=None):
                return DataNode(data, parent)

        return TestableDataTreeModel()

    def test_init(self, model):
        """Test DataTreeModel initialization."""
        assert model._root is not None
        assert model._root._data == "root node"
        assert model._columns == 1
        assert model._items == []
        assert model.junk == []

    def test_get_node_by_index_valid(self, model):
        """Test getNodeByIndex with valid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_node = MagicMock()
        mock_index.internalPointer.return_value = mock_node

        result = model.getNodeByIndex(mock_index)
        assert result == mock_node

    def test_get_node_by_index_invalid(self, model):
        """Test getNodeByIndex with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        result = model.getNodeByIndex(mock_index)
        assert result == model._root

    def test_insert_data_rows_valid_parent(self, model):
        """Test insertDataRows with valid parent."""
        parent_index = QModelIndex()
        data_rows = ["data1", "data2"]

        with patch.object(model, "beginInsertRows") as mock_begin, patch.object(
            model, "endInsertRows"
        ) as mock_end, patch.object(model, "addNode") as mock_add:
            result = model.insertDataRows(0, data_rows, parent_index)

            assert result is True
            mock_begin.assert_called_once_with(parent_index, 0, 2)
            mock_end.assert_called_once()
            assert mock_add.call_count == 2

    def test_remove_row(self, model):
        """Test removeRow method."""
        parent_index = QModelIndex()

        with patch.object(model, "removeRows") as mock_remove:
            mock_remove.return_value = True

            result = model.removeRow(1, parent_index)

            assert result is True
            mock_remove.assert_called_once_with([1], 1, parent_index)

    def test_remove_rows_with_children(self, model):
        """Test _removeRows method with children."""
        # Create parent node with children
        parent_node = DataNode("parent")
        DataNode("child1", parent_node)
        DataNode("child2", parent_node)

        parent_index = QModelIndex()

        with patch.object(
            model, "getNodeByIndex", return_value=parent_node
        ), patch.object(model, "index", return_value=QModelIndex()), patch.object(
            model, "beginRemoveRows"
        ), patch.object(model, "endRemoveRows"):
            result = model._removeRows(0, 2, parent_index, emitSignals=False)
            assert result is True

    def test_remove_sub_rows_valid_index(self, model):
        """Test removeSubRows with valid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_node = MagicMock()
        mock_node.__len__ = MagicMock(return_value=3)

        with patch.object(
            model, "getNodeByIndex", return_value=mock_node
        ), patch.object(model, "removeRows", return_value=True) as mock_remove:
            result = model.removeSubRows(mock_index)

            assert result is True
            mock_remove.assert_called_once_with(0, 3, mock_index)

    def test_remove_sub_rows_invalid_index(self, model):
        """Test removeSubRows with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        result = model.removeSubRows(mock_index)
        assert result is False

    def test_clear(self, model):
        """Test clear method."""
        with patch.object(model, "beginResetModel") as mock_begin, patch.object(
            model, "endResetModel"
        ) as mock_end, patch.object(model, "_removeRows") as mock_remove:
            model.clear()

            mock_begin.assert_called_once()
            mock_end.assert_called_once()
            mock_remove.assert_called_once()

    def test_index_valid_row(self, model):
        """Test index method with valid row."""
        parent_node = DataNode("parent")
        child_node = DataNode("child", parent_node)

        with patch.object(
            model, "getNodeByIndex", return_value=parent_node
        ), patch.object(model, "createIndex") as mock_create:
            mock_create.return_value = QModelIndex()

            model.index(0, 0, QModelIndex())
            mock_create.assert_called_once_with(0, 0, child_node)

    def test_index_invalid_row(self, model):
        """Test index method with invalid row."""
        parent_node = DataNode("parent")

        with patch.object(model, "getNodeByIndex", return_value=parent_node):
            result = model.index(5, 0, QModelIndex())
            assert not result.isValid()

    def test_data_decoration_role(self, model):
        """Test data method with DecorationRole."""
        mock_index = MagicMock()
        mock_index.column.return_value = 0
        mock_icon = MagicMock()

        with patch.object(model, "_getDecorationIcon", return_value=mock_icon):
            result = model.data(mock_index, Qt.DecorationRole)
            assert result == mock_icon

    def test_data_text_alignment_role(self, model):
        """Test data method with TextAlignmentRole."""
        mock_index = MagicMock()
        mock_index.column.return_value = 0

        result = model.data(mock_index, Qt.TextAlignmentRole)
        assert result == Qt.AlignTop | Qt.AlignLeft

    def test_data_display_role(self, model):
        """Test data method with DisplayRole."""
        mock_index = MagicMock()
        mock_index.column.return_value = 0
        mock_node = MagicMock()
        mock_node.getText.return_value = "test text"

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.data(mock_index, Qt.DisplayRole)
            assert result == "test text"

    def test_data_display_role_root_node(self, model):
        """Test data method with DisplayRole for root node."""
        mock_index = MagicMock()
        mock_index.column.return_value = 0

        with patch.object(model, "getNodeByIndex", return_value=model._root):
            result = model.data(mock_index, Qt.DisplayRole)
            assert result == ""

    def test_column_count(self, model):
        """Test columnCount method."""
        result = model.columnCount(QModelIndex())
        assert result == 1

    def test_row_count(self, model):
        """Test rowCount method."""
        mock_node = MagicMock()
        mock_node.__len__ = MagicMock(return_value=5)

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.rowCount(QModelIndex())
            assert result == 5

    def test_row_count_none_node(self, model):
        """Test rowCount method with None node."""
        with patch.object(model, "getNodeByIndex", return_value=None):
            result = model.rowCount(QModelIndex())
            assert result == 0

    def test_parent_invalid_child(self, model):
        """Test parent method with invalid child."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = False

        result = model.parent(mock_child)
        assert not result.isValid()

    def test_parent_none_node(self, model):
        """Test parent method with None node."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = True

        with patch.object(model, "getNodeByIndex", return_value=None):
            result = model.parent(mock_child)
            assert not result.isValid()

    def test_parent_none_parent(self, model):
        """Test parent method with None parent."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = True
        mock_node = MagicMock()
        mock_node.getParent.return_value = None

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.parent(mock_child)
            assert not result.isValid()

    def test_parent_none_grandparent(self, model):
        """Test parent method with None grandparent."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = True
        mock_node = MagicMock()
        mock_parent = MagicMock()
        mock_parent.getParent.return_value = None
        mock_node.getParent.return_value = mock_parent

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.parent(mock_child)
            assert not result.isValid()

    def test_parent_valid_hierarchy(self, model):
        """Test parent method with valid hierarchy."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = True
        mock_node = MagicMock()
        mock_parent = MagicMock()
        mock_grandparent = MagicMock()
        mock_grandparent.rowOfChild.return_value = 2
        mock_parent.getParent.return_value = mock_grandparent
        mock_node.getParent.return_value = mock_parent

        with patch.object(
            model, "getNodeByIndex", return_value=mock_node
        ), patch.object(model, "createIndex") as mock_create:
            mock_create.return_value = QModelIndex()

            model.parent(mock_child)
            mock_create.assert_called_once_with(2, 0, mock_parent)

    def test_parent_invalid_row(self, model):
        """Test parent method with invalid row."""
        mock_child = MagicMock()
        mock_child.isValid.return_value = True
        mock_node = MagicMock()
        mock_parent = MagicMock()
        mock_grandparent = MagicMock()
        mock_grandparent.rowOfChild.return_value = -1
        mock_parent.getParent.return_value = mock_grandparent
        mock_node.getParent.return_value = mock_parent

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "builtins.print"
        ) as mock_print:
            result = model.parent(mock_child)
            assert not result.isValid()
            mock_print.assert_called_once_with(
                "Impossible condition in DataTreeModel, please debug"
            )


class TestWFEFileSystemModel:
    """Test WFEFileSystemModel methods."""

    @pytest.fixture
    def model(self):
        """Create WFEFileSystemModel instance."""
        return WFEFileSystemModel()

    def test_init(self, model):
        """Test WFEFileSystemModel initialization."""
        assert isinstance(model, WFEFileSystemModel)

    def test_print_rows_inserted(self, model):
        """Test print_rowsInserted method."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_node = MagicMock()
        mock_node.getText.return_value = "test_node"
        mock_index.internalPointer.return_value = mock_node
        mock_index.parent.return_value = QModelIndex()

        # Should not raise any errors
        model.print_rowsInserted(mock_index, 1, 3)

    def test_print_rows_inserted_invalid_index(self, model):
        """Test print_rowsInserted with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        # Should not raise any errors
        model.print_rowsInserted(mock_index, 1, 3)

    def test_get_decoration_icon_file(self, model):
        """Test _getDecorationIcon for file type."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.FILE

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "simstack.view.WFEditorTreeModels.QFileIconProvider"
        ) as mock_provider:
            mock_icon = MagicMock()
            mock_provider.return_value.icon.return_value = mock_icon

            result = model._getDecorationIcon(mock_index)
            assert result == mock_icon

    def test_get_decoration_icon_directory(self, model):
        """Test _getDecorationIcon for directory type."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.DIRECTORY

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "simstack.view.WFEditorTreeModels.QFileIconProvider"
        ) as mock_provider:
            mock_icon = MagicMock()
            mock_provider.return_value.icon.return_value = mock_icon

            result = model._getDecorationIcon(mock_index)
            assert result == mock_icon

    def test_get_decoration_icon_undeleteable_directory(self, model):
        """Test _getDecorationIcon for undeleteable directory type."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.UNDELETEABLE_DIRECTORY

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "simstack.view.WFEditorTreeModels.QFileIconProvider"
        ) as mock_provider:
            mock_icon = MagicMock()
            mock_provider.return_value.icon.return_value = mock_icon

            result = model._getDecorationIcon(mock_index)
            assert result == mock_icon

    def test_get_decoration_icon_loading(self, model):
        """Test _getDecorationIcon for loading type."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.LOADING

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "simstack.view.WFEditorTreeModels.QFileIconProvider"
        ) as mock_provider:
            mock_icon = MagicMock()
            mock_provider.return_value.icon.return_value = mock_icon

            result = model._getDecorationIcon(mock_index)
            assert result == mock_icon

    def test_get_decoration_icon_unknown(self, model):
        """Test _getDecorationIcon for unknown type."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.UNKNOWN

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model._getDecorationIcon(mock_index)
            assert result is None

    def test_create_node(self, model):
        """Test createNode method."""
        data = {"path": "test", "abspath": "/test"}
        parent = DataNode("parent")

        result = model.createNode(data, parent)

        assert isinstance(result, WFEFileSystemEntry)
        assert result._data == data

    def test_file_path_valid_index(self, model):
        """Test filePath with valid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_node = MagicMock()
        mock_node.getPath.return_value = "/test/path"

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.filePath(mock_index)
            assert result == "/test/path"

    def test_file_path_invalid_index(self, model):
        """Test filePath with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        result = model.filePath(mock_index)
        assert result is None

    def test_loading(self, model):
        """Test loading method."""
        mock_index = MagicMock()

        with patch.object(model, "removeSubRows") as mock_remove, patch.object(
            model, "insertDataRows", return_value=True
        ) as mock_insert, patch("builtins.print") as mock_print:
            model.loading(mock_index, "Loading test")

            mock_remove.assert_called_once_with(mock_index)
            mock_insert.assert_called_once()
            mock_print.assert_called_once_with("insertDataRows: True")

    def test_subelements_to_text(self, model):
        """Test subelementsToText method."""
        # Create a simple tree structure
        root_node = DataNode("root")
        child1 = DataNode("child1", root_node)
        child2 = DataNode("child2", root_node)

        mock_parent_index = QModelIndex()

        # Create mock indices for recursive calls
        mock_child_index1 = MagicMock()
        mock_child_index2 = MagicMock()

        with patch.object(model, "getNodeByIndex") as mock_get_node, patch.object(
            model, "index"
        ) as mock_index_method:
            # Setup mock returns for getNodeByIndex
            mock_get_node.side_effect = [root_node, child1, child2]

            # Setup mock returns for index method
            mock_index_method.side_effect = [mock_child_index1, mock_child_index2]

            # Should not raise any errors
            model.subelementsToText(mock_parent_index)


class TestWFERemoteFileSystemModel:
    """Test WFERemoteFileSystemModel methods."""

    @pytest.fixture
    def model(self):
        """Create WFERemoteFileSystemModel instance without Qt initialization."""
        # Use __new__ to avoid Qt initialization
        model = WFERemoteFileSystemModel.__new__(WFERemoteFileSystemModel)

        # Manually set required attributes
        model._icons = {
            DATA_TYPE.SEPARATOR1: MagicMock(),
            DATA_TYPE.JOB_SUCCESSFUL: MagicMock(),
            DATA_TYPE.JOB_FAILED: MagicMock(),
            DATA_TYPE.WF_SUCCESSFUL: MagicMock(),
        }
        model._root = DataNode("root node")
        model._columns = 1
        model._items = []
        model.junk = []

        return model

    def test_init(self, model):
        """Test WFERemoteFileSystemModel initialization."""
        assert isinstance(model, WFERemoteFileSystemModel)
        assert DATA_TYPE.SEPARATOR1 in model._icons
        assert DATA_TYPE.JOB_SUCCESSFUL in model._icons

    def test_pixmap_to_grayscale(self, model):
        """Test pixmap_to_grayscale method."""
        # Create a mock pixmap
        mock_pixmap = MagicMock()
        mock_image = MagicMock()
        mock_image.width.return_value = 2
        mock_image.height.return_value = 2
        mock_image.pixel.return_value = 0xFF000000  # Black pixel
        mock_pixmap.toImage.return_value = mock_image

        with patch("simstack.view.WFEditorTreeModels.qGray", return_value=128), patch(
            "simstack.view.WFEditorTreeModels.QColor"
        ) as mock_color, patch(
            "simstack.view.WFEditorTreeModels.QPixmap"
        ) as mock_qpixmap:
            mock_color.return_value.rgba.return_value = 0xFF808080
            mock_qpixmap.fromImage.return_value = mock_pixmap

            model.pixmap_to_grayscale(mock_pixmap)

            # Verify image manipulation calls
            assert mock_image.setPixel.call_count == 4  # 2x2 pixels

    def test_colorize_icon_method_exists(self, model):
        """Test colorize_icon method exists and handles non-QIcon input."""
        # Test with non-QIcon object to hit the isinstance check
        not_icon = "not an icon"
        color = MagicMock()

        result = model.colorize_icon(not_icon, color)
        assert result is None

    def test_icons_existing_type(self, model):
        """Test icons method with existing type."""
        result = model.icons(DATA_TYPE.JOB_SUCCESSFUL)
        assert result is not None

    def test_icons_non_existing_type(self, model):
        """Test icons method with non-existing type."""
        with patch(
            "simstack.view.WFEditorTreeModels.QFileIconProvider"
        ) as mock_provider:
            mock_icon = MagicMock()
            mock_provider.return_value.icon.return_value = mock_icon

            result = model.icons(DATA_TYPE.UNKNOWN)
            assert result == mock_icon

    def test_create_node(self, model):
        """Test createNode method."""
        data = {
            "id": "test",
            "name": "test_name",
            "path": "test_path",
            "abspath": "/test",
        }
        parent = DataNode("parent")

        result = model.createNode(data, parent)

        assert isinstance(result, WFERemoteFileSystemEntry)
        assert result._data == data

    def test_get_decoration_icon_fallback_to_parent(self, model):
        """Test _getDecorationIcon fallback to parent method."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getIconType.return_value = DATA_TYPE.FILE

        with patch.object(model, "getNodeByIndex", return_value=mock_node), patch(
            "simstack.view.WFEditorTreeModels.WFEFileSystemModel._getDecorationIcon"
        ) as mock_parent:
            mock_parent.return_value = None

            with patch.object(model, "icons") as mock_icons:
                mock_icon = MagicMock()
                mock_icons.return_value = mock_icon

                result = model._getDecorationIcon(mock_index)
                assert result == mock_icon

    def test_recursive_find_parent_none_index(self, model):
        """Test _recursive_find_parent with None index."""
        result = model._recursive_find_parent(None, [DATA_TYPE.JOB_SUCCESSFUL])
        assert result is None

    def test_recursive_find_parent_invalid_index(self, model):
        """Test _recursive_find_parent with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        result = model._recursive_find_parent(mock_index, [DATA_TYPE.JOB_SUCCESSFUL])
        assert result is None

    def test_recursive_find_parent_matching_type(self, model):
        """Test _recursive_find_parent with matching type."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_parent = MagicMock()
        mock_index.parent.return_value = mock_parent
        mock_node = MagicMock()
        mock_node.getDataType.return_value = DATA_TYPE.JOB_SUCCESSFUL

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model._recursive_find_parent(
                mock_index, [DATA_TYPE.JOB_SUCCESSFUL]
            )
            assert result == mock_parent

    def test_recursive_find_parent_no_matching_type(self, model):
        """Test _recursive_find_parent with no matching type (base case)."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        mock_parent = MagicMock()
        mock_parent.isValid.return_value = (
            False  # Parent is invalid, so recursion stops
        )
        mock_index.parent.return_value = mock_parent
        mock_node = MagicMock()
        mock_node.getDataType.return_value = DATA_TYPE.FILE

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model._recursive_find_parent(
                mock_index, [DATA_TYPE.JOB_SUCCESSFUL]
            )
            assert result is None

    def test_get_id(self, model):
        """Test get_id method."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getID.return_value = "test_id"

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.get_id(mock_index)
            assert result == "test_id"

    def test_get_id_none_node(self, model):
        """Test get_id with None node."""
        mock_index = MagicMock()

        with patch.object(model, "getNodeByIndex", return_value=None):
            result = model.get_id(mock_index)
            assert result is None

    def test_get_type(self, model):
        """Test get_type method."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getDataType.return_value = DATA_TYPE.FILE

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.get_type(mock_index)
            assert result == DATA_TYPE.FILE

    def test_get_type_none_node(self, model):
        """Test get_type with None node."""
        mock_index = MagicMock()

        with patch.object(model, "getNodeByIndex", return_value=None):
            result = model.get_type(mock_index)
            assert result is None

    def test_get_abspath(self, model):
        """Test get_abspath method."""
        mock_index = MagicMock()
        mock_node = MagicMock()
        mock_node.getAbsolutePath.return_value = "/test/path"

        with patch.object(model, "getNodeByIndex", return_value=mock_node):
            result = model.get_abspath(mock_index)
            assert result == "/test/path"

    def test_get_abspath_none_node(self, model):
        """Test get_abspath with None node."""
        mock_index = MagicMock()

        with patch.object(model, "getNodeByIndex", return_value=None):
            result = model.get_abspath(mock_index)
            assert result is None

    def test_get_headers(self, model):
        """Test get_headers method."""
        mock_index = MagicMock()
        mock_result = MagicMock()

        with patch.object(
            model, "_recursive_find_parent", return_value=mock_result
        ) as mock_recursive:
            result = model.get_headers(mock_index)

            assert result == mock_result
            mock_recursive.assert_called_once_with(
                mock_index, [model.HEADER_TYPE_WORKFLOW, model.HEADER_TYPE_JOB]
            )

    def test_get_category_parent(self, model):
        """Test get_category_parent method."""
        mock_index = MagicMock()
        mock_result = MagicMock()

        with patch.object(
            model, "_recursive_find_parent", return_value=mock_result
        ) as mock_recursive:
            result = model.get_category_parent(mock_index)

            assert result == mock_result
            mock_recursive.assert_called_once_with(
                mock_index, [model.DATA_TYPE_WORKFLOW, model.DATA_TYPE_JOB]
            )

    def test_get_parent_job(self, model):
        """Test get_parent_job method."""
        mock_index = MagicMock()
        mock_result = MagicMock()

        with patch.object(
            model, "_recursive_find_parent", return_value=mock_result
        ) as mock_recursive:
            result = model.get_parent_job(mock_index)

            assert result == mock_result
            mock_recursive.assert_called_once_with(mock_index, [model.DATA_TYPE_JOB])

    def test_get_parent_workflow(self, model):
        """Test get_parent_workflow method."""
        mock_index = MagicMock()
        mock_result = MagicMock()

        with patch.object(
            model, "_recursive_find_parent", return_value=mock_result
        ) as mock_recursive:
            result = model.get_parent_workflow(mock_index)

            assert result == mock_result
            mock_recursive.assert_called_once_with(
                mock_index, [model.DATA_TYPE_WORKFLOW]
            )

    def test_add_headers(self, model):
        """Test _add_headers method."""
        with patch.object(model, "insertDataRows") as mock_insert:
            model._add_headers()

            mock_insert.assert_called_once()
            args = mock_insert.call_args[0]
            assert args[0] == 0  # row
            assert len(args[1]) == 2  # two header entries
            assert isinstance(args[2], QModelIndex)  # parent index

    def test_clear_with_headers(self, model):
        """Test clear method with header restoration."""
        with patch(
            "simstack.view.WFEditorTreeModels.WFEFileSystemModel.clear"
        ) as mock_super_clear, patch.object(model, "_add_headers") as mock_add_headers:
            model.clear()

            mock_super_clear.assert_called_once()
            mock_add_headers.assert_called_once()

    def test_get_separator_indices(self, model):
        """Test get_separator_indices method."""
        model._root = MagicMock()
        model._root.__len__ = MagicMock(return_value=3)

        with patch.object(model, "index") as mock_index:
            mock_indices = [MagicMock(), MagicMock(), MagicMock()]
            mock_index.side_effect = mock_indices

            result = model.get_separator_indices()

            assert result == mock_indices
            assert mock_index.call_count == 3

    def test_loading_invalid_index(self, model):
        """Test loading method with invalid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = False

        with patch.object(model, "clear") as mock_clear, patch.object(
            model, "index"
        ) as mock_index_method, patch(
            "simstack.view.WFEditorTreeModels.WFEFileSystemModel.loading"
        ) as mock_super_loading, patch("builtins.print") as mock_print:
            model._root = MagicMock()
            model._root.__len__ = MagicMock(return_value=2)
            mock_indices = [MagicMock(), MagicMock()]
            mock_index_method.side_effect = mock_indices

            model.loading(mock_index, "Test Loading")

            mock_print.assert_called_once_with("not index.isValid()")
            mock_clear.assert_called_once()
            assert mock_super_loading.call_count == 2

    def test_loading_valid_index(self, model):
        """Test loading method with valid index."""
        mock_index = MagicMock()
        mock_index.isValid.return_value = True

        with patch.object(model, "removeSubRows") as mock_remove:
            model.loading(mock_index, "Test Loading")

            mock_remove.assert_called_once_with(mock_index)


class TestAdditionalWFERemoteFileSystemEntry:
    """Additional tests for WFERemoteFileSystemEntry edge cases."""

    def test_get_icon_type_job_with_status_none(self):
        """Test getIconType for job with None status."""
        data = WFERemoteFileSystemEntry.createData(
            id="job_id",
            name="job_name",
            path="job_path",
            abspath="job_abspath",
            data_type=WFERemoteFileSystemModel.DATA_TYPE_JOB,
            status=None,
        )
        entry = WFERemoteFileSystemEntry(data)

        # Should fall back to super().getIconType()
        with patch(
            "simstack.view.WFEditorTreeModels.WFEFileSystemEntry.getIconType"
        ) as mock_super:
            mock_super.return_value = DATA_TYPE.FILE

            result = entry.getIconType()
            assert result == DATA_TYPE.FILE

    def test_get_icon_type_workflow_with_status(self):
        """Test getIconType for workflow with status."""
        data = WFERemoteFileSystemEntry.createData(
            id="wf_id",
            name="wf_name",
            path="wf_path",
            abspath="wf_abspath",
            data_type=WFERemoteFileSystemModel.DATA_TYPE_WORKFLOW,
            status=JobStatus.SUCCESSFUL,
        )
        entry = WFERemoteFileSystemEntry(data)

        result = entry.getIconType()
        assert result == WF_STATUS_TO_DATA_TYPE[JobStatus.SUCCESSFUL]

    def test_get_icon_type_workflow_with_status_none(self):
        """Test getIconType for workflow with None status."""
        data = WFERemoteFileSystemEntry.createData(
            id="wf_id",
            name="wf_name",
            path="wf_path",
            abspath="wf_abspath",
            data_type=WFERemoteFileSystemModel.DATA_TYPE_WORKFLOW,
            status=None,
        )
        entry = WFERemoteFileSystemEntry(data)

        # Should fall back to super().getIconType()
        with patch(
            "simstack.view.WFEditorTreeModels.WFEFileSystemEntry.getIconType"
        ) as mock_super:
            mock_super.return_value = DATA_TYPE.DIRECTORY

            result = entry.getIconType()
            assert result == DATA_TYPE.DIRECTORY


class TestJobStatusMappings:
    """Test job status mappings."""

    def test_job_status_to_data_type_mappings(self):
        """Test JOB_STATUS_TO_DATA_TYPE mapping completeness."""
        assert JobStatus.READY in JOB_STATUS_TO_DATA_TYPE
        assert JobStatus.FAILED in JOB_STATUS_TO_DATA_TYPE
        assert JobStatus.ABORTED in JOB_STATUS_TO_DATA_TYPE
        assert JobStatus.SUCCESSFUL in JOB_STATUS_TO_DATA_TYPE
        assert JobStatus.QUEUED in JOB_STATUS_TO_DATA_TYPE
        assert JobStatus.RUNNING in JOB_STATUS_TO_DATA_TYPE

    def test_wf_status_to_data_type_mappings(self):
        """Test WF_STATUS_TO_DATA_TYPE mapping completeness."""
        assert JobStatus.READY in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.FAILED in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.ABORTED in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.SUCCESSFUL in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.QUEUED in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.RUNNING in WF_STATUS_TO_DATA_TYPE
        assert JobStatus.MARKED_FOR_DELETION in WF_STATUS_TO_DATA_TYPE
