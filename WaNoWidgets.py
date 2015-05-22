#
#  Supply the memberfunctions making the widgets 
#
import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

import logging

#class WaNoElementWidgetFactory:
    #factories = {}
    #def addFactory(id, shapeFactory):
        #WaNoElementWidgetFactory.factories.put[id] = shapeFactory
    #addFactory = staticmethod(addFactory)
    ## A Template Method:
    #def createWaNoE(id,inputData):
        #if not WaNoElementWidgetFactory.factories.has_key(id):    
            #WaNoElementWidgetFactory.factories[id] = \
              #eval(id + '.Factory()')
        #return  WaNoElementWidgetFactory.factories[id].create(inputData)
    #createWaNoEWidget = staticmethod(createWaNoEWidget)
    

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
        widget = element.makeWidget(ll,importSelection)
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
    sig = QtCore.Signal()
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
        self.layout.setContentsMargins(1,1,1,1)
        
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
    
        self.editor.textChanged.connect(self.changed)
        self.hiddenButton.clicked.connect(self.changed)
        from WaNoEditor import WaNoEditor
        self.sig.connect(WaNoEditor.hasChanged)
       
        
    def changed(self):
        self.sig.emit()
        
    def modifyInput(self):
        self.sig.emit()
        if len(self.importSelection) > 0:
            sel = self.typeSelect.currentText()
            if sel == 'W' or sel == 'X':
                self.importSelect.show()
            else:
                self.importSelect.hide()
    
#def makeSimpleWidget(self,ll,importSelection):    
    #self.myWidget  =  WaNoItemWidget(self,ll,importSelection,None)
    #return self.myWidget

class WaNoSelectionWidget(QtGui.QDialog):
    sig = QtCore.Signal()
    #----------------------------------------------------------------------
    def __init__(self,waNoElement,labelSize, importSelection,parent=None):
        super(WaNoSelectionWidget,self).__init__(parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.logger = logging.getLogger("WEFLOG")
        
        # left top right bottom
        self.layout.setContentsMargins(5,1,1,1)
        label = QtGui.QLabel(waNoElement.name)
        self.layout.addWidget(label)
        label.setFixedWidth(6*labelSize+10)
        
        self.editor = QtGui.QListWidget()
      
        for i in waNoElement.elements:
            self.editor.addItem(i.value) 

        if len(waNoElement.elements) == 0:
            self.logger.error("Selection in WaNo Element " + waNoElement.name + " is empty")
            
        if len(waNoElement.selectedItems) == 0:
            self.logger.error("No default item defined for WaNo Element " + waNoElement.name)
            if len(waNoElement.elements) > 0:
                self.editor.setCurrentRow(0,QtGui.QItemSelectionModel.Select)
                
        for i in waNoElement.selectedItems:
            try:
                self.editor.setCurrentRow(i,QtGui.QItemSelectionModel.Select)
            except:
                self.logger.error("Selection Failure WaNo Element " + waNoElement.name)
                
        self.layout.addWidget(self.editor)
        
        self.hiddenButton = QtGui.QRadioButton('hide')
        self.layout.addWidget(self.hiddenButton)
        
        self.setLayout(self.layout)
        
        self.editor.itemClicked.connect(self.changed)
        self.hiddenButton.clicked.connect(self.changed)
        from WaNoEditor import WaNoEditor
        self.sig.connect(WaNoEditor.hasChanged)    
        
    def changed(self):
        self.sig.emit()


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

class WaNoFileWidget(WaNoItemWidget):
    def __init__(self,waNoElement,ll,importSelection):
        super(WaNoFileWidget,self).__init__(waNoElement,ll,importSelection)
        rx = QtCore.QRegExp("\\S+")
        self.myValidator = QtGui.QRegExpValidator(rx, self.editor)
      
class WaNoOutputFileWidget(WaNoItemWidget):
    def __init__(self,waNoElement,ll,importSelection):
        super(WaNoOutputFileWidget,self).__init__(waNoElement,ll,importSelection)
        rx = QtCore.QRegExp("\\S+")
        self.myValidator = QtGui.QRegExpValidator(rx, self.editor)
        

class WaNoFloatWidget(WaNoItemWidget):
    def __init__(self,waNoElement,ll,importSelection):
        super(WaNoFloatWidget,self).__init__(waNoElement,ll,importSelection)
        self.myValidator = QtGui.QDoubleValidator(self.editor)

class WaNoIntWidget(WaNoItemWidget):
    def __init__(self,waNoElement,ll,importSelection):
        super(WaNoIntWidget,self).__init__(waNoElement,ll,importSelection)
        self.myValidator = QtGui.QIntValidator(self.editor)
   
    
