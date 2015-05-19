#
#  Supply the memberfunctions making the widgets 
#
import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

def getWidgetText(myWidget):
    return myWidget.text()
    
def getSelectedItems(myWidget):
    items = myWidget.selectedItems()
    elements = [ myWidget.item(i).text() for i in  range(myWidget.count())]
    xlist    = [ elements.index(item.text()) for item in items]
    return xlist

def WaNoSectionWidget(self,ll,importSelection):
    self.layout = QtGui.QVBoxLayout()
    self.layout.addWidget(QtGui.QLabel(self.name))

    ll = max( [ len(element.name) for element in self.elements] )
    
    for element in self.elements:
        widget = element.widget(ll,importSelection)
        self.layout.addWidget(widget)
            
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget

def WaNoVarSectionWidget(self,ll,importSelection):
    self.layout = QtGui.QVBoxLayout()
    self.layout.addWidget(QtGui.QLabel(self.name))
    
    ll = max( [ len(element.name) for element in self.elements] )
    for element in self.elements:
        widget = element.widget(ll,importSelection)
        self.layout.addWidget(widget)
            
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget


class WaNoItemWidget(QtGui.QDialog):
    #----------------------------------------------------------------------
    def __init__(self,waNoElement,labelSize,importSelection,parent=None):
        super(WaNoItemWidget,self).__init__(parent)
        """
             complex dialog to assign to variable either 
                - a fixed value 
                - a reference to a local variable 
                - a reference to a WF file 
                - a reference to a WF variable
        """
        self.layout = QtGui.QHBoxLayout()
 
        # left top right bottom
        self.layout.setContentsMargins(0,0,0,0)
        
        label = QtGui.QLabel(waNoElement.name)
        label.setFixedWidth(6*labelSize+10)
        self.layout.addWidget(label)
        
        self.typeSelect = QtGui.QComboBox()
     
        
        if len(importSelection) > 0:
            self.typeSelect.addItems(["V","L","W","X"])    
            self.layout.addWidget(self.typeSelect)
            idx = ["V","L","W","X"].index(waNoElement.attrib['sourceType'])
            self.typeSelect.setCurrentIndex(idx)
            print ("sourceType:",waNoElement.attrib['sourceType'],idx)
            self.typeSelect.currentIndexChanged.connect(self.modifyInput)
          
        
            self.importSelection = importSelection
            self.importSelect    = QtGui.QComboBox()
            self.importSelect.addItems(importSelection)
            
            if waNoElement.attrib["importFrom"] != '':
                idx = importSelection.index(waNoElement.attrib["importFrom"])
                self.importSelect.setCurrentIndex(idx)
                print ("importFrom:",waNoElement.attrib['importFrom'],idx)
            self.layout.addWidget(self.importSelect)
            if self.typeSelect.currentText() in ["V","L"]:
                self.importSelect.hide()
        else:
            self.typeSelect.addItems(["V","L"])
            print ("sourceType:",waNoElement.attrib['sourceType'])
            idx = ["V","L","W","X"].index(waNoElement.attrib['sourceType'])
            self.typeSelect.setCurrentIndex(idx)
            self.typeSelect.currentIndexChanged.connect(self.modifyInput)
            self.layout.addWidget(self.typeSelect)
            
            self.importSelection = importSelection  # add but empty
            self.importSelect    = QtGui.QComboBox()
        
        self.editor = QtGui.QLineEdit(str(waNoElement.value))
        self.layout.addWidget(self.editor)
        self.hiddenButton = QtGui.QRadioButton('hide')
        if 'hidden' in waNoElement.attrib:
            if waNoElement.attrib['hidden'] == 'True' or waNoElement.attrib['hidden'] == 'true':
                self.hiddenButton.setChecked(True)
        self.layout.addWidget(self.hiddenButton)
        
        self.setLayout(self.layout) 
    
    def modifyInput(self):
        if len(self.importSelection) > 0:
            sel = self.typeSelect.currentText()
            if sel == 'W' or sel == 'X':
                self.importSelect.show()
            else:
                self.importSelect.hide()
    
def makeSimpleWidget(self,ll,importSelection):    
    self.myWidget  =  WaNoItemWidget(self,ll,importSelection,None)
    return self.myWidget


def WaNoSelectionWidget(self,ll,importSelection):
    self.layout = QtGui.QHBoxLayout()
    # left top right bottom
    self.layout.setContentsMargins(5,1,1,1)
    self.layout.addWidget(QtGui.QLabel(self.name))
    self.editor = QtGui.QListWidget()
  
    for i in self.elements:
        self.editor.addItem(i.value) 
    
    for i in self.selectedItems:
        self.editor.setCurrentRow(i,QtGui.QItemSelectionModel.Select)
    self.layout.addWidget(self.editor)
    self.hiddenbutton = QtGui.QRadioButton('hide')
    self.layout.addWidget(self.hiddenbutton)
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget  

def WaNoSelectionElementWidget(self,ll,importSelection):
    pass

        
def WaNoStringWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection) 
    return widget

def WaNoLocalFileWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection) 
    rx = QtCore.QRegExp("\\S+")
    widget.myValidator = QtGui.QRegExpValidator(rx, widget.editor)
    return widget

def WaNoFileWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection) 
    rx = QtCore.QRegExp("\\S+")
    widget.myValidator = QtGui.QRegExpValidator(rx, widget.editor)
    return widget

def WaNoOutputFileWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection)
    rx = QtCore.QRegExp("\\S+")
    widget.myValidator = QtGui.QRegExpValidator(rx, widget.editor)
    return self.myWidget  

def WaNoFloatWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection)
    widget.myValidator = QtGui.QDoubleValidator(widget.editor)
    return widget

def WaNoIntWidget(self,ll,importSelection):
    widget = makeSimpleWidget(self,ll,importSelection) 
    widget.editor.setValidator(QtGui.QIntValidator(widget.editor))
    return widget
    
