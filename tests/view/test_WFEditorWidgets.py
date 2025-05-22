import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

from simstack.view.WFEditorWidgets import (
    WFEListWidget,
    WFEWaNoListWidget,
    WFEWorkflowistWidget
)


class TestWFEListWidget:
    """Tests for the WFEListWidget class."""

    @pytest.fixture
    def list_widget(self, qtbot):
        """Create a WFEListWidget instance."""
        widget = WFEListWidget()
        qtbot.addWidget(widget)
        return widget
    
    def test_init(self, list_widget):
        """Test initialization of WFEListWidget."""
        # Verify drag is enabled
        assert list_widget.dragEnabled() is True
        
        # Verify no controls by default
        assert list_widget.count() == 0
    
    def test_init_with_controls(self, qtbot):
        """Test initialization with controls."""
        # Create mock controls
        controls = [
            ("Control1", "path/to/icon1.png"),
            ("Control2", "path/to/icon2.png")
        ]
        
        # Initialize with controls
        with patch('simstack.view.WFEditorWidgets.QIcon') as mock_icon:
            widget = WFEListWidget(controls=controls)
            qtbot.addWidget(widget)
            
            # Verify controls were added
            assert widget.count() == 2
            assert widget.item(0).text() in ["Control1", "Control2"]  # Order may change due to sorting
            assert widget.item(1).text() in ["Control1", "Control2"]
            assert widget.item(0).text() != widget.item(1).text()
            
            # Verify icons were set
            assert mock_icon.call_count == 2
    
    def test_update_list(self, list_widget):
        """Test update_list method."""
        # Create mock controls
        controls = [
            ("Control1", "path/to/icon1.png"),
            ("Control2", "path/to/icon2.png")
        ]
        
        # Update list
        with patch('simstack.view.WFEditorWidgets.QIcon') as mock_icon:
            list_widget.update_list(controls)
            
            # Verify controls were added
            assert list_widget.count() == 2
            assert list_widget.item(0).text() in ["Control1", "Control2"]  # Order may change due to sorting
            assert list_widget.item(1).text() in ["Control1", "Control2"]
            assert list_widget.item(0).text() != list_widget.item(1).text()
            
            # Verify icons were set
            assert mock_icon.call_count == 2
            
            # Verify myHeight was set
            assert list_widget.myHeight == 10
    
    def test_size_hint(self, list_widget):
        """Test sizeHint method."""
        # Set myHeight
        list_widget.myHeight = 50
        
        # Verify size hint
        size = list_widget.sizeHint()
        assert size.width() == 100
        assert size.height() == 50


class TestWFEWaNoListWidget:
    """Tests for the WFEWaNoListWidget class."""

    @pytest.fixture
    def wano_list_widget(self, qtbot):
        """Create a WFEWaNoListWidget instance."""
        widget = WFEWaNoListWidget()
        qtbot.addWidget(widget)
        return widget
    
    @pytest.fixture
    def mock_wano_list_entry(self):
        """Create a mock WaNoListEntry."""
        wano = MagicMock()
        wano.name = "TestWaNo"
        wano.folder = "/path/to/wano"
        wano.icon = "path/to/icon.png"
        return wano
    
    def test_init(self, wano_list_widget):
        """Test initialization of WFEWaNoListWidget."""
        # Verify drag is enabled
        assert wano_list_widget.dragEnabled() is True
        
        # Verify myHeight is initialized
        assert wano_list_widget.myHeight == 10
        
        # Verify no items by default
        assert wano_list_widget.count() == 0
    
    def test_update_list(self, wano_list_widget, mock_wano_list_entry):
        """Test update_list method."""
        # Create list of mock WaNoListEntries
        wanos = [mock_wano_list_entry]
        
        # Update list
        with patch('simstack.view.WFEditorWidgets.QIcon') as mock_icon:
            wano_list_widget.update_list(wanos)
            
            # Verify wanos were added
            assert wano_list_widget.count() == 1
            assert wano_list_widget.item(0).text() == "TestWaNo"
            
            # Verify WaNo attribute was set
            assert wano_list_widget.item(0).WaNo is mock_wano_list_entry
            
            # Verify icon was set
            mock_icon.assert_called_once_with(mock_wano_list_entry.icon)
            
            # Verify myHeight was updated
            assert wano_list_widget.myHeight == 10  # 1 item * 10
    
    def test_update_list_multiple(self, wano_list_widget):
        """Test update_list method with multiple WaNos."""
        # Create list of mock WaNoListEntries
        wanos = []
        for i in range(5):
            wano = MagicMock()
            wano.name = f"TestWaNo{i}"
            wano.folder = f"/path/to/wano{i}"
            wano.icon = f"path/to/icon{i}.png"
            wanos.append(wano)
        
        # Update list
        with patch('simstack.view.WFEditorWidgets.QIcon'):
            wano_list_widget.update_list(wanos)
            
            # Verify wanos were added
            assert wano_list_widget.count() == 5
            
            # Verify myHeight was updated
            assert wano_list_widget.myHeight == 50  # 5 items * 10
    
    def test_update_list_clears_previous(self, wano_list_widget, mock_wano_list_entry):
        """Test that update_list clears previous items."""
        # Add initial items
        with patch('simstack.view.WFEditorWidgets.QIcon'):
            wano_list_widget.update_list([mock_wano_list_entry, mock_wano_list_entry])
            assert wano_list_widget.count() == 2
            
            # Update with new items
            new_wano = MagicMock()
            new_wano.name = "NewWaNo"
            new_wano.folder = "/path/to/new_wano"
            new_wano.icon = "path/to/new_icon.png"
            
            wano_list_widget.update_list([new_wano])
            
            # Verify old items were cleared and new item was added
            assert wano_list_widget.count() == 1
            assert wano_list_widget.item(0).text() == "NewWaNo"
    
    def test_size_hint(self, wano_list_widget):
        """Test sizeHint method."""
        # Test with small myHeight
        wano_list_widget.myHeight = 50
        size = wano_list_widget.sizeHint()
        assert size.width() == 100
        assert size.height() == 200  # Should use minimum of 200
        
        # Test with large myHeight
        wano_list_widget.myHeight = 300
        size = wano_list_widget.sizeHint()
        assert size.width() == 100
        assert size.height() == 300  # Should use myHeight since it's larger than min


class TestWFEWorkflowistWidget:
    """Tests for the WFEWorkflowistWidget class."""

    @pytest.fixture
    def workflow_list_widget(self, qtbot):
        """Create a WFEWorkflowistWidget instance."""
        with patch('simstack.view.WFEditorWidgets.logging'):
            widget = WFEWorkflowistWidget()
            qtbot.addWidget(widget)
            return widget
    
    @pytest.fixture
    def mock_workflow(self):
        """Create a mock workflow."""
        workflow = MagicMock()
        workflow.name = "TestWorkflow"
        return workflow
    
    def test_init(self, workflow_list_widget):
        """Test initialization of WFEWorkflowistWidget."""
        # Verify drag is enabled
        assert workflow_list_widget.dragEnabled() is True
        
        # Verify myHeight is initialized
        assert workflow_list_widget.myHeight == 10
        
        # Verify no items by default
        assert workflow_list_widget.count() == 0
        
        # Verify itemDoubleClicked signal is connected
        assert workflow_list_widget.itemDoubleClicked.isConnected()
    
    def test_update_list(self, workflow_list_widget, mock_workflow):
        """Test update_list method."""
        # Create list of mock workflows
        workflows = [mock_workflow]
        
        # Update list
        workflow_list_widget.update_list(workflows)
        
        # Verify workflows were added
        assert workflow_list_widget.count() == 1
        assert workflow_list_widget.item(0).text() == "TestWorkflow"
        
        # Verify workflow attribute was set
        assert workflow_list_widget.item(0).workflow is mock_workflow
        
        # Verify myHeight was updated
        assert workflow_list_widget.myHeight == 10  # 1 item * 10
    
    def test_update_list_multiple(self, workflow_list_widget):
        """Test update_list method with multiple workflows."""
        # Create list of mock workflows
        workflows = []
        for i in range(5):
            workflow = MagicMock()
            workflow.name = f"TestWorkflow{i}"
            workflows.append(workflow)
        
        # Update list
        workflow_list_widget.update_list(workflows)
        
        # Verify workflows were added
        assert workflow_list_widget.count() == 5
        
        # Verify myHeight was updated
        assert workflow_list_widget.myHeight == 50  # 5 items * 10
    
    def test_update_list_clears_previous(self, workflow_list_widget, mock_workflow):
        """Test that update_list clears previous items."""
        # Add initial items
        workflow_list_widget.update_list([mock_workflow, mock_workflow])
        assert workflow_list_widget.count() == 2
        
        # Update with new items
        new_workflow = MagicMock()
        new_workflow.name = "NewWorkflow"
        
        workflow_list_widget.update_list([new_workflow])
        
        # Verify old items were cleared and new item was added
        assert workflow_list_widget.count() == 1
        assert workflow_list_widget.item(0).text() == "NewWorkflow"
    
    def test_size_hint(self, workflow_list_widget):
        """Test sizeHint method."""
        # Test with small myHeight
        workflow_list_widget.myHeight = 50
        size = workflow_list_widget.sizeHint()
        assert size.width() == 100
        assert size.height() == 100  # Should use minimum of 100
        
        # Test with large myHeight
        workflow_list_widget.myHeight = 200
        size = workflow_list_widget.sizeHint()
        assert size.width() == 100
        assert size.height() == 200  # Should use myHeight since it's larger than min
    
    def test_open_wf(self, workflow_list_widget, mock_workflow):
        """Test openWf method."""
        # Setup mock parent hierarchy
        parent = MagicMock()
        grandparent = MagicMock()
        parent.parent.return_value = grandparent
        workflow_list_widget.parent = MagicMock(return_value=parent)
        
        # Create a mock item
        item = QListWidgetItem("TestWorkflow")
        item.workflow = mock_workflow
        
        # Call the method
        workflow_list_widget.openWf(item)
        
        # Verify openWorkFlow was called on the grandparent
        grandparent.openWorkFlow.assert_called_once_with(mock_workflow)