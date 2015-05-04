from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import os
import sys
import WFELicense

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

class DragButton(QtGui.QPushButton):

    def __init__(self, text, parent=None):
        super(DragButton, self).__init__(text,parent)        
        self.moved  = False
  
    def parentElementList(self):
        return self.parent().buttons
    
    def mouseMoveEvent(self, e):
        if self.text() == "Start":
            e.ignore()
            return
        if e.buttons() == QtCore.Qt.LeftButton:   
            self.parentElementList().remove(self)
            mimeData = QtCore.QMimeData()
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(e.pos() - self.rect().topLeft())
            self.move( e.globalPos() );
            dropAction = drag.start(QtCore.Qt.MoveAction)

    def mouseDoubleClickEvent(self,e):
        print ('clicked',self.text())


        
class WFBaseWidget(QtGui.QFrame):
    def __init__(self, parent=None):
        super(WFBaseWidget, self).__init__(parent)    
        self.setAcceptDrops(True)
        self.buttons = []
        self.autoResize = False
            
    def placeElementPosition(self,element):
        # this function computes the position of the next button
        newb  = []
        count = 0
        element.show()
        posHint = element.pos()
       
        while len(self.buttons) > 0:
            e    = self.buttons[0]
            ypos = e.pos().y()+e.height()/2
            if posHint.y() > ypos or count < 1:
                newb.append(self.buttons.pop(0))
                count += 1
            else:
                break
        #
        #  now add the new element
        #
        print ("Placing Element: %-12s %4i %4i" % (element.text(),posHint.y(),element.height()))
        newb.append(element)
        #
        # move rest of elments down
        #
        while len(self.buttons) > 0: 
            e    = self.buttons.pop(0)
            newb.append(e)
        self.buttons = newb
        self.placeButtons()
   
    def dragLeaveEvent(self, e): 
        e.accept()
    
    def placeButtons(self):
        dims        = self.geometry()
        elementSkip = 20    # distance to skip between elements
        ypos        = elementSkip/2
        
        for e in self.buttons:
            xpos  = (dims.width()-e.width())/2
            e.move(xpos,ypos)
            ypos += e.height() + elementSkip
            
        
    def paintEvent(self, event):
        super(WFBaseWidget,self).paintEvent(event)
        
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = 20
        if len(self.buttons)>1:
            e  = self.buttons[0]
            sx = e.pos().x() + e.width()/2
            sy = e.pos().y() + e.height()
        for b in self.buttons[1:]:
            ey  = b.pos().y() 
            line = QtCore.QLine(sx,sy,sx,ey)
            painter.drawLine(line) 
            sy  = b.pos().y() + b.height()         
        painter.end()     
        if self.autoResize:
            self.setFixedHeight(sy + 20)
           
  

    def dragEnterEvent(self, e): 
        print ("DragEnterEvent Window",self.text())
        e.accept()

    def dragLeaveEvent(self, e): 
        super(WFBaseWidget,self).dragLeaveEvent(e)
        print ("DragLeave Workflow",self.text())
        self.placeButtons()
        self.update()
        e.accept()
        
    def dropEvent(self, e):
        print ("DropEvent Workflow",self.text())
        super(WFBaseWidget,self).dropEvent(e)
        position = e.pos()
        sender   = e.source()
        if type(sender) is DragButton:
            sender.move(e.pos())
            self.placeElementPosition(sender)
        elif type(sender) is WFWhileWidget:
            sender.move(e.pos())
            self.placeElementPosition(sender)
        else:
            item     = sender.selectedItems()[0]
            text     = item.text()
        
            # make a new widget
            if text=='While':
                btn = WFWhileWidget(self) 
                btn.move(e.pos())
                btn.show()
            else:
                btn = DragButton(text,self)
                btn.move(e.pos())
                btn.show()
            self.placeElementPosition(btn)
        e.accept()
        self.update()
    def text(self):
        return 'Abstract WFWindow Class'
    
class WFWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(WFWidget, self).__init__(parent)   
        
        self.acceptDrops()
        self.setDragEnabled(True)
        self.wf = WFWidgetArea(self)
        scroll = QtGui.QScrollArea()
        scroll.setMinimumSize(400, 600)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(False)
        scroll.setWidget(self.wf)
        scroll.acceptDrops()
        
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(scroll)
        self.setLayout(vLayout)
         
       
    def text(self):
        return 'Main WF Window'
    
class WFWidgetArea(WFBaseWidget):
    def __init__(self, parent=None):
        super(WFWidgetArea, self).__init__(parent)   
        self.acceptDrops()
       
        self.setMinimumSize(400, 600)
        self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        #
        #  the start button is always there
        #
        btn = DragButton('Start',self)
        self.placeElementPosition(btn)
        self.show()
    def text(self):
        return 'Main WF Window'
    
class WFWhileWidget(QtGui.QFrame):
    def __init__(self, parent=None):
        super(WFWhileWidget, self).__init__(parent)        
        self.setFrameStyle(QtGui.QFrame.Panel)
        self.setAcceptDrops(True)
        #self.setDragEnabled(True)
        
        layout        = QtGui.QVBoxLayout()
        
        topLineLayout = QtGui.QHBoxLayout()
        topLineLayout.addWidget(QtGui.QPushButton('While'))  
        topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        
        self.wf = WFBaseWidget(self)
        self.wf.setMinimumSize(parent.width()-50,100)
        self.wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        self.wf.autoResize = True
        self.wf.show()
        
        layout.addLayout(topLineLayout)
        layout.addWidget(self.wf)
        
        self.setLayout(layout)
    
    def parentElementList(self):
        return self.parent().buttons
    
    def text(self):
        return 'While'
    
    def mouseMoveEvent(self, e):
        print ("moving whole widget")
        if e.buttons() == QtCore.Qt.LeftButton:   
            self.parentElementList().remove(self)
            mimeData = QtCore.QMimeData()
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(e.pos() - self.rect().topLeft())
            self.move( e.globalPos() );
            dropAction = drag.start(QtCore.Qt.MoveAction)
            
class WFEListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(WFEListWidget, self).__init__(parent) 
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        path = os.path.dirname(__file__)
        for image in sorted(os.listdir(os.path.join(path, "images"))):
            if image.endswith(".png"):
                item = QtGui.QListWidgetItem(image.split(".")[0].capitalize())
                item.setIcon(QtGui.QIcon(os.path.join(path,
                                   "images/{0}".format(image))))
                self.addItem(item)
 
        
    def dragEnterEvent(self, e): 
        print ("DragEnterEvent ListWidget")
        e.accept()
        
    def dragEvent(self, e): 
        e.accept()
        
    def dropEvent(self, e):
        position = e.pos()
        sender   = e.source()
        print ("DE:",e.source())
        e.accept()
    
  
    
class Test(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Test, self).__init__(parent)     
        self.setMinimumSize(200,200)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.darkCyan)
        self.setPalette(p)
        self.setAutoFillBackground(True)
        self.acceptDrops()
        self.show()
    def dragEnterEvent(self, e): 
        print ("DragEnterEvent ListWidget")
        e.accept()    
        
class Form(QtGui.QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        
        workflowWidget = WFWidgetArea(self)
        workflowWidget.setAcceptDrops(True)
        
        listWidget = WFEListWidget()
       
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(listWidget)
        splitter.addWidget(workflowWidget)
        splitter.addWidget(Test())
        
        layout = QtGui.QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.setWindowTitle("Workflow Panel")

   
        
        
app = QtGui.QApplication(sys.argv)
form = Form()
form.show()
app.exec_()

