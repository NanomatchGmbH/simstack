#
#  Supply the memberfunctions making the widgets 
#
import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

def getWidgetText(myWidget):
    return myWidget.text()

def WaNoESectionWidget(self):
    self.layout = QtGui.QVBoxLayout()
    self.layout.addWidget(QtGui.QLabel(self.name))
    
    for element in self.elements:
        widget = element.widget()
        self.layout.addWidget(widget)
            
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget

def makeSimpleWidget(self):
    self.layout = QtGui.QHBoxLayout()
    # left top right bottom
    self.layout.setContentsMargins(5,1,1,1)
    self.layout.addWidget(QtGui.QLabel(self.name))
    self.editor = QtGui.QLineEdit(str(self.value))
    self.layout.addWidget(self.editor)
    self.hiddenbutton = QtGui.QRadioButton('hide')
    self.layout.addWidget(self.hiddenbutton)
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget  

def WaNoESelectionWidget(self):
    print 'xxx'
    self.layout = QtGui.QHBoxLayout()
    # left top right bottom
    self.layout.setContentsMargins(5,1,1,1)
    self.layout.addWidget(QtGui.QLabel(self.name))
    self.editor = QtGui.QListWidget(self.value)
    
    
    
    self.layout.addWidget(self.editor)
    self.hiddenbutton = QtGui.QRadioButton('hide')
    self.layout.addWidget(self.hiddenbutton)
    self.myWidget = QtGui.QWidget()
    self.myWidget.setLayout(self.layout)
    return self.myWidget  


def WaNoEStringWidget(self):
    widget = makeSimpleWidget(self) 
    return widget

def WaNoEFileWidget(self):
    widget = makeSimpleWidget(self) 
    return widget

def WaNoELocalFileWidget(self):
    widget = makeSimpleWidget(self)
    self.editor.setValidator(QtGui.QDoubleValidator(self.editor))
    return self.myWidget  

def WaNoEFloatWidget(self):
    widget = makeSimpleWidget(self)
    self.editor.setValidator(QtGui.QDoubleValidator(self.editor))
    return widget

def WaNoEIntWidget(self):
    widget = makeSimpleWidget(self) 
    self.editor.setValidator(QtGui.QIntValidator(self.editor))
    return widget
    
def WaNoESelectionWidget(self):
    widget = makeSimpleWidget(self) 
    return widget


