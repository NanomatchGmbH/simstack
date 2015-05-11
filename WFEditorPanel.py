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
    
    def placeElements(self):
        pass
    
    def mouseMoveEvent(self, e):
        if self.text() == "Start":
            e.ignore()
            return
        if e.buttons() == QtCore.Qt.LeftButton:   
            self.parent().removeElement(self)
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
        self.topWidget  = False
        self.embeddedIn = None
        self.myName     = "AbstractWFWidget"
        self.elementSkip = 20    # distance to skip between elements
       
    def removeElement(self,element):
        # remove element both from the buttons and child list
        try:
            self.buttons.remove(element)
            self.children().remove(element)
            self.placeElements()
            if len(self.buttons) == 0 and \
               hasattr(self.parent(),'removePanel'):  # maybe remove the whole widget ?
                self.parent().removePanel(self)
        except IndexError:
            print ("Removing Element ",element.text()," from WFBaseWidget",self.text())
   
    def sizeHint(self):
        if self.topWidget:            
            s = QtCore.QSize(self.width(),self.height()) 
        else:
            s = QtCore.QSize(self.parent().width()-50,self.height()) 
        return s
        
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
        #print ("Placing Element: %-12s %4i %4i" % (element.text(),posHint.y(),element.height()))
        newb.append(element)
        #
        # move rest of elments down
        #
        while len(self.buttons) > 0: 
            e    = self.buttons.pop(0)
            newb.append(e)
        self.buttons = newb
        self.placeElements()
   
    def dragLeaveEvent(self, e): 
        e.accept()

    def recPlaceElements(self): 
        # redo your own buttons and then do the parent
        ypos = self.placeOwnButtons()
        self.setFixedHeight(ypos+2.25*self.elementSkip) 
        self.update()  
        if not self.topWidget:
            self.parent().recPlaceElements()
        else:
            if self.embeddedIn != None:
                self.embeddedIn.recPlaceElements()    
    
    def placeOwnButtons(self):
        dims        = self.geometry()
        ypos        = self.elementSkip/2
        
        for e in self.buttons:
            xpos  = (dims.width()-e.width())/2
            e.move(xpos,ypos)
            ypos += e.height() + self.elementSkip
        #print ("Computed Widget height: ",self.text(),ypos)
        return ypos
        
    def placeElements(self):
        ypos = self.placeOwnButtons()
        if self.autoResize:
            #print ("autores:",self.text(),ypos)
            ypos = max(ypos,self.elementSkip) # all derived elements have a min wf size 
            self.setFixedHeight(ypos) 
            #self.parent().setFixedHeight(ypos+2.25*self.elementSkip) 
            if not self.topWidget:
                self.parent().recPlaceElements()
            else:
                self.recPlaceElements()
                if self.embeddedIn != None:
                    #print ("resize  ",self.text(),ypos,self.height())
                    hh = max(ypos,self.embeddedIn.height())
                    self.embeddedIn.setFixedHeight(max(ypos,self.height()))              
                    self.embeddedIn.updateGeometry()
                
    def paintEvent(self, event):        
        super(WFBaseWidget,self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
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
        
    def dragEnterEvent(self, e): 
        #print ("DragEnterEvent Window",self.text())
        e.accept()

    def dragLeaveEvent(self, e): 
        super(WFBaseWidget,self).dragLeaveEvent(e)
        #print ("DragLeave Workflow",self.text())
        self.placeElements()
        self.update()
        e.accept()
        
    def dropEvent(self, e):
        #print ("DropEvent Workflow",self.text())
        super(WFBaseWidget,self).dropEvent(e)
        position = e.pos()
        sender   = e.source()
        
        controlWidgetNames = ["While","If","ForEach","For","Parallel"]
        controlWidgetClasses = [ "WF"+a+"Widget" for a in controlWidgetNames]
        if type(sender) is DragButton:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
        elif type(sender).__name__ in controlWidgetClasses:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
            sender.placeElements() # place all the buttons 
        else:
            item     = sender.selectedItems()[0]
            text     = item.text()
        
            # make a new widget
            if text in controlWidgetNames:
                btn = eval("WF"+text+"Widget")(self) #  WFWhileWidget(self) 
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
        return self.myName
    
class WFWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(WFWidget, self).__init__(parent)   
        
        self.acceptDrops()
       
        self.wf = WFMainWidgetArea(self)
      
        dummy  = QtGui.QFrame() # this is needed to resize the scrollbar
        self.wf.embeddedIn = dummy   # this is the widget that needs to be reiszed when the main layout widget resizes
        dummy.setFrameStyle(QtGui.QFrame.Panel)
        dummylayout = QtGui.QVBoxLayout(dummy)
        dummylayout.setContentsMargins(0,0,0,0) # there is only 1 widget inside no margins
        dummylayout.addWidget(self.wf)
        dummy.setLayout(dummylayout) 
    
        self.setMinimumSize(self.wf.width()+50,600) # widget with scrollbar
        
        scroll = QtGui.QScrollArea(self)
        scroll.setMinimumHeight(600)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(dummy)      
        scroll.acceptDrops()      
        scroll.setParent(self)
        
        self.scroll = scroll
    
    
         
class WFMainWidgetArea(WFBaseWidget):
    def __init__(self, parent=None):
        super(WFMainWidgetArea, self).__init__(parent)   
        self.acceptDrops()
        self.topWidget  = True
        self.autoResize = True
        self.myName     = "WFMainWidgetArea"
        self.setMinimumWidth(400)
        self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        #
        #  the start button is always there
        #
        btn = DragButton('Start',self)
        btn.show()
        self.placeElementPosition(btn)
       
    def recPlaceElements(self): 
        # here is min height of main widget
      
        ypos=max(self.placeOwnButtons(),600)
        self.setFixedHeight(ypos)
        self.parent().setFixedHeight(ypos) 

class WFControlWidget(QtGui.QFrame):
    def __init__(self, parent=None):
        super(WFControlWidget, self).__init__(parent)        
        self.setFrameStyle(QtGui.QFrame.Panel)
        self.setAcceptDrops(True)
        self.isVisible = True     # the subwidget are is visible
        self.layout        = QtGui.QVBoxLayout()
        
        noPar=self.makeTopLine()
        self.wf = []
        self.hidden = []
        self.bottomLayout = QtGui.QHBoxLayout()
        self.elementSkip = 0 
        for i in range(noPar):
            wf = WFBaseWidget(self)
            self.elementSkip = max(self.elementSkip,wf.elementSkip)
            wf.myName = self.myName + ("WF%i" % i)
            wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
            wf.autoResize = True
            self.wf.append(wf)
            if self.isVisible:
                self.bottomLayout.addWidget(wf)
            
        self.layout.addLayout(self.topLineLayout)
        self.layout.addLayout(self.bottomLayout)
        
        self.setLayout(self.layout)
        self.show()
    
    def toggleVisible(self):
        print ("Toggle Visible")
        if self.isVisible: # remove widget from bottomlayout
            for w in self.wf:
                self.bottomLayout.takeAt(0)
                w.setParent(None)
            self.hidden = self.wf
            self.wf = []
        else:
            for w in self.hidden:
                self.bottomLayout.addWidget(w)
                w.show()
            self.wf = self.hidden
            self.hidden = []
          
        self.recPlaceElements()
        self.bottomLayout.update()
        self.update()
        self.isVisible = not self.isVisible
        
        
    def text(self):
        return self.myName 
    
    def placeElements(self):
        print ("Place Elements",self.text())
        for w in self.wf:
            w.placeElements()
        
    def recPlaceElements(self): 
        # redo your own buttons and then do the parent
        ypos = 0 
        if len(self.wf) > 0:
            for w in self.wf:
                ypos=max(ypos,w.placeOwnButtons())
            print ("WFControlElement Child Height:",ypos)
            ypos = max(ypos,2*self.elementSkip)
            self.setFixedHeight(ypos+2.25*self.elementSkip) 
            for w in self.wf:
                w.setFixedHeight(ypos) 
        else:
            self.setFixedHeight(50)
        self.update()  
        self.parent().recPlaceElements()
                  
    def sizeHint(self):
        hh = max(self.height(),100)
        s = QtCore.QSize(self.parent().width()-50,hh) 
        return s        
    
    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.LeftButton:   
            self.parent().removeElement(self)
            mimeData = QtCore.QMimeData()
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(e.pos() - self.rect().topLeft())
            self.move( e.globalPos() );
            dropAction = drag.start(QtCore.Qt.MoveAction)

class WFWhileWidget(WFControlWidget):
    def __init__(self, parent=None):
        super(WFWhileWidget, self).__init__(parent)      
        
    def makeTopLine(self):
        self.myName = 'While'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 1
    
class WFIfWidget(WFControlWidget):
    def __init__(self, parent=None):
        super(WFIfWidget, self).__init__(parent)      
        
    def makeTopLine(self):
        self.myName = 'If'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 2

class WFForEachWidget(WFControlWidget):
    def __init__(self, parent=None):
        super(WFForEachWidget, self).__init__(parent)      
        
    def makeTopLine(self):
        self.myName = 'ForEach'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)   
        self.topLineLayout.addWidget(QtGui.QLineEdit('name'))
        self.topLineLayout.addWidget(QtGui.QLineEdit('list'))
        return 1


class WFParallelWidget(WFControlWidget):
    def __init__(self, parent=None):
        super(WFParallelWidget, self).__init__(parent)      
        
    def makeTopLine(self):
        self.myName = 'Parallel'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        a = QtGui.QPushButton('Add')
        a.clicked.connect(self.addWF)
        self.topLineLayout.addWidget(a) 
        return 2
    
    #----------------------------------------------------------------------
    def removePanel(self,panel):
        """"""
        if self.bottomLayout.count() > 2: # 2 panels min
            print ("remove panel",panel.text())
            try:
                index = self.bottomLayout.indexOf(panel)
            except IndexError:
                print ("Error Panel not found",panel.text())
            
            print ("Index",index)
            if self.isVisible:
                self.wf.remove(panel)
            else:
                self.hidden.remove(panel)
            widget = self.bottomLayout.takeAt(index).widget()
            widget.setParent(None)
            if widget is not None: 
                # widget will be None if the item is a layout
                widget.deleteLater()
            
        
    
    def addWF(self):
        if not self.isVisible:
            self.toggleVisible()
        wf = WFBaseWidget(self)
        self.elementSkip = max(self.elementSkip,wf.elementSkip)
        wf.myName = self.myName + "WF" + str(self.bottomLayout.count())
        wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        wf.autoResize = True
        self.wf.append(wf)       
        self.bottomLayout.addWidget(wf)
        self.placeElements()
        
    
class WFEListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(WFEListWidget, self).__init__(parent) 
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        path = os.path.dirname(__file__)
        for image in sorted(os.listdir(os.path.join(path, "images"))):
            if image.endswith(".png"):
                item = QtGui.QListWidgetItem(image.split(".")[0])
                item.setIcon(QtGui.QIcon(os.path.join(path,
                                   "images/{0}".format(image))))
                self.addItem(item)

   
    
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
        #print ("DragEnterEvent ListWidget")
        e.accept()    
        
class Form(QtGui.QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        workflowWidget = WFWidget(self)
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

   
    def resizeEvent(self,e):
        super(Form,self).resizeEvent(e)
        print ("RES")

        
        
app = QtGui.QApplication(sys.argv)
form = Form()
form.show()
app.exec_()

