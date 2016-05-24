from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import os

import logging
from   lxml import etree

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

import WaNo.WaNoFactory as WaNoFactory


def mapClassToTag(name):
    xx = name.replace('Widget','')
    return xx[2:]
    
widgetColors = {'MainEditor' : '#F5FFF5' , 'Control': '#EBFFD6' , 'Base': '#F5FFEB' ,
               'WaNo' : '#FF00FF', 'ButtonColor':'#D4FF7F' }
#widgetColors = {'MainEditor': '#77B395', 'Control': '#003C1D', 'Base': '#28774F',
#                'WaNo': '#28536C', 'ButtonColor': '#477087'}

    
class WFWaNoWidget(QtGui.QToolButton):
    def __init__(self, text, wano, parent=None):
        #super(WFWaNoWidget, self).__init__(text,parent)
        super(WFWaNoWidget, self).__init__(parent)
        self.logger = logging.getLogger('WFELOG')
        self.moved  = False
        #
        #  here we make a deep copy of the WaNo, but deep copy does not work. Do it via XMLK
        #
        lvl = self.logger.getEffectiveLevel() # switch off too many infos
        self.logger.setLevel(logging.ERROR)

        self.logger.setLevel(lvl)
        stylesheet ="""
        background-color: %s;
        border: 3px solid black;
        border-radius: 12px;
        color: black;
        font-size: 24px;
        padding: 4px;
        padding-left: 6px;
        padding-right: 6px;
        icon-size: 64px;

        """ %widgetColors["ButtonColor"]
        self.setStyleSheet(stylesheet) # + widgetColors['WaNo'])
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setText(text)
        self.setIcon(wano[3])
        #self.setAutoFillBackground(True)
        #self.setColor(QtCore.Qt.lightGray)
        self.wano = None
        self.wano_instance = None
  
    def parentElementList(self):
        return self.parent().buttons
    
    def placeElements(self):
        pass

    def setColor(self,color):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Button,color)
        self.setPalette(p)

    def parse(self,r):
        self.wano = WaNo(r)
        
    def xml(self):
        if self.text() != "Start":
            return self.wano.xml() 
   
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
            self.move( e.globalPos() )
            dropAction = drag.start(QtCore.Qt.MoveAction)

    def clear(self):
        pass 

    def construct_wano(self):
        self.wano_model,self.wano_view = WaNoFactory.wano_constructor_helper(self.wano[0],self)


    def mouseDoubleClickEvent(self,e):
        if self.wano_instance is not None:
            self.parent().openWaNoEditor(self) # pass the widget to remember it
        else:
            self.construct_wano()
    
    def gatherExports(self,wano,varExp,filExp,waNoNames):
        if wano == self.wano:
            return True
        if self.wano is not None:
            self.wano_instance.gatherExports(varExp,filExp,waNoNames)
        return False
    
class WFBaseWidget(QtGui.QFrame):
    def __init__(self, editor, parent=None):
        super(WFBaseWidget, self).__init__(parent)    
        
        self.setStyleSheet("background: " + widgetColors['Base'])
        self.logger = logging.getLogger('WFELOG')
        self.editor = editor
        self.setAcceptDrops(True)
        self.buttons = []
        self.autoResize = False
        self.topWidget = False
        self.embeddedIn = None
        self.myName = "AbstractWFTabsWidget"
        self.elementSkip = 20    # distance to skip between elements
     
    def clear(self):
        for e in self.buttons:
            e.clear()
        
        for c in self.children():
            c.deleteLater()
            
        self.buttons = []
            
    def removeElement(self,element):
        # remove element both from the buttons and child list
        try:
            self.buttons.remove(element)
            self.children().remove(element)
            self.placeElements()
            if len(self.buttons) == 0 and \
                hasattr(self.parent,'removePanel'):  # maybe remove the whole widget ?
                self.parent().removePanel(self)
        except IndexError:
            print ("Removing Element ",element.text()," from WFBaseWidget",self.text())
  
    def openWaNoEditor(self,wanoWidget):
        if wanoWidget.isWorkFlow:
            print ("open Workflow")
            self.editor.openWorkFlow(wanoWidget.wano)
        else:
            varEx = {}
            filEx = {}
            waNoNames = []
            if not self.gatherExports(wanoWidget.wano,varEx,filEx,waNoNames):
                self.logger.error("Error gathering exports for Wano:",wanoWidget.name)
            self.editor.openWaNoEditor(wanoWidget,varEx,filEx,waNoNames)
        
    def sizeHint(self):
        if self.topWidget:            
            s = QtCore.QSize(self.width(),self.height()) 
        else:
            s = QtCore.QSize(self.parent().width()-50,self.height()) 
        return s
    
    def xml(self,name="Untitled"):
        ee =  etree.Element(mapClassToTag(self.__class__.__name__),name=name)
        for e in self.buttons:
            if e.text() != "Start":
                ee.append(e.xml())
        return ee 
            
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
            e = self.buttons.pop(0)
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
            if self.embeddedIn is not None:
                self.embeddedIn.recPlaceElements()    
    
    def placeOwnButtons(self):
        dims = self.geometry()
        ypos = self.elementSkip/2
        
        for e in self.buttons:
            xpos = (dims.width()-e.width())/2
            e.move(xpos,ypos)
            ypos += e.height() + self.elementSkip
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
        e.accept()

    def dragLeaveEvent(self, e): 
        super(WFBaseWidget,self).dragLeaveEvent(e)
        self.placeElements()
        self.update()
        e.accept()
        
    def dropEvent(self, e):
        super(WFBaseWidget,self).dropEvent(e)
        WFWorkflowWidget.hasChanged()
        position = e.pos()
        sender   = e.source()
        
        controlWidgetNames = ["While","If","ForEach","For","Parallel"]
        controlWidgetClasses = [ "WF"+a+"Widget" for a in controlWidgetNames]
        if type(sender) is WFWaNoWidget:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
        elif type(sender).__name__ in controlWidgetClasses:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
            sender.placeElements() # place all the buttons 
        else:
            item = sender.selectedItems()[0]
            text = item.text()
        
            # make a new widget
            if text in controlWidgetNames:
                btn = eval("WF"+text+"Widget")(self.editor,self) #  WFWhileWidget(self) 
                btn.move(e.pos())
                btn.show()
            else:
                if hasattr(item,'WaNo'):
                    print("here1")
                    print(item.WaNo)
                    btn = WFWaNoWidget(text,item.WaNo,self)
                else:
                    print("here2")
                    btn = WFWaNoWidget(text,None,self)
                btn.move(e.pos())
                btn.show()
            self.placeElementPosition(btn)
        e.accept()
        self.update()
        
    def parse(self,xml):
        for c in xml:
            self.logger.debug("WFBaseWidget parse" +c.tag)
            if c.tag == 'WaNo':
                w = WaNo(c)
                e = WFWaNoWidget(w.name,w,self)
            else:
                e = eval("WF"+c.tag+"Widget")(self.editor,self)
                e.parse(c)
            self.buttons.append(e)
            e.show()
        self.placeElements()
            
    
    def gatherExports(self,wano,varExp,filExp,waNoNames):
        for b in self.buttons:
            if b.gatherExports(wano,varExp,filExp,waNoNames):
                return True 
        return False 
                
    def text(self):
        return self.myName

class WFTabsWidget(QtGui.QTabWidget):
    def __init__(self, parent):
        super(WFTabsWidget, self).__init__(parent)

        self.logger = logging.getLogger('WFELOG')

        self.acceptDrops()
        self.curFile = WFFileName()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        self.wf = WFWorkflowWidget(parent,self)

        #####self.wf.embeddedIn = self   # this is the widget that needs to be reiszed when the main layout widget resizes
        #####self.addTab(self.wf,self.curFile.name)
        #####self.setMinimumSize(self.wf.width()+25,600) # widget with scrollbar

        scroll = QtGui.QScrollArea(self)
        scroll.setWidget(self.wf)
        scroll.setMinimumWidth(300)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        self.addTab(scroll, self.curFile.name)

        ####bb = self.tabBar().tabButton(0, QtGui.QTabBar.RightSide)
        ####bb.resize(0, 0)


    def clear(self):
        print ("Workflow has changed ? ",WFWorkflowWidget.changedFlag)
        if WFWorkflowWidget.changedFlag:
            reply = QtGui.QMessageBox(self)
            reply.setText("The document has been modified.")
            reply.setInformativeText("Do you want to save your changes?")
            reply.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            reply.setDefaultButton(QtGui.QMessageBox.Save)
            ret = reply.exec_()

            if ret == QtGui.QMessageBox.Cancel:
                return
            if ret == QtGui.QMessageBox.Save:
                self.save()
        self.wf.clear()
        WFWorkflowWidget.changedFlag = False
        self.tabWidget.setTabText(0,'Untitled')

    def markWFasChanged(self):
        print ("mark as changed")

    def save(self):
        if self.curFile.name == 'Untitled':
            return self.saveAs()
        else:
            return self.saveFile(self.curFile.fullName())

    def saveAs(self):
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(self, 'Save Workflow',self.curFile.name,'xml (*.xml *.xm)')
        if not fileName:
            return False
        return self.saveFile(fileName)

    def open(self):
        fileName, filtr = QtGui.QFileDialog(self).getOpenFileName(self,'Open Workflow','.','xml (*.xml *.xm)')
        if fileName:
            print ("Loading Workflow from File:",fileName)
            self.clear()
            self.loadFile(fileName)

    def openWorkFlow(self,workFlow):
        if not workFlow.isOpen:
            wf = WFWorkflowWidget(self.parent(),self)
            wf.sourceWF = workFlow
            wf.parse(workFlow.xml())
            self.tabWidget.addTab(wf,workFlow.name)

    def closeTab(self,e):
        # this works recursively
        if self.parent().lastActive != None:
            # close wano editor
            self.parent().wanoEditor.deleteClose()

        nn = self.tabWidget.count()-1
        for i in range(nn,e-1,-1):
            self.logger.info("Removing Tab: " + str(e))
            wf  = self.tabWidget.widget(e)
            xml = wf.xml()
            wf.sourceWF.setToXML(xml)
            wf.sourceWF.isOpen = False
            self.tabWidget.removeTab(e)


    def saveFile(self,fileName):
        xml = self.wf.xml(os.path.basename(fileName).split('.')[0])
        self.curFile.dirName, tail = os.path.split(fileName)
        tt =  tail.split('.')
        self.curFile.name = tt[0]
        if len(tt) > 1:
            self.curFile.ext  = tail.split('.')[1]
        else:
            self.curFile.ext = 'xml'

        self.logger.info("Saving Workflow to: " + self.curFile.dirName + " t: " + self.curFile.name + ' x: ' + self.curFile.ext)

        textFile = open(fileName,"w")
        textFile.write(etree.tostring(xml,pretty_print=True))
        textFile.close()
        self.tabWidget.setTabText(0,self.curFile.name)
        WFWorkflowWidget.changedFlag = False

    def loadFile(self,fileName):
        self.logger.info('Loading Workflow from: ',fileName)
        try:
            self.inputData = etree.parse(fileName)
        except:
            self.logger.error('File not found: ' + fileName)
            raise
        r = self.inputData.getroot()
        if r.tag == 'Workflow':
            self.wf.parse(r)
        else:
            print ("Could not Parse Workflow in ",fileName)
        WFWorkflowWidget.changedFlag = False

    def sizeHint(self):
        return QtCore.QSize(500,500)


#
#  editor is the workflow editor that can open/close the WaNo editor
#   
class WFFileName:
    def __init__(self):
        self.dirName = '.'
        self.name    = "Untitled"
        self.ext     = 'xml'
    def fullName(self):
        return self.dirName + '/' + self.name + '.' + self.ext
    
class WFWorkflowWidget(WFBaseWidget):
    changedFlag     = False
    activeTabWidget = None
  
    
    def __init__(self, editor,  parent):
        super(WFWorkflowWidget, self).__init__(editor,parent)   
        self.acceptDrops()
        self.topWidget  = True
        self.autoResize = True
        self.parent = parent
        self.myName = "WFWorkflowWidget"
        self.style_sheet_without_background = "background-color: " + widgetColors['MainEditor'] + """ ;
                              %s
                              background-repeat: no-repeat;
                              background-attachment: fixed;
                              background-position: center;  """
        self.background_drawn = True

        self.setStyleSheet(self.style_sheet_without_background % "background-image: url('./WaNo/Media/Logo_NanoMatch200.png') ;")
          
        self.setMinimumWidth(400)
        self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)

    def recPlaceElements(self):
        if self.background_drawn:
            self.setStyleSheet(self.style_sheet_without_background %"")
            self.background_drawn = False
        ypos = max(self.placeOwnButtons(), self.parent.height())
        self.setFixedHeight(ypos)

    @staticmethod  
    def hasChanged():
        logger = logging.getLogger('WFELOG')
        logger.info("WorkFlow has changed")
        WFWorkflowWidget.changedFlag=True
        if WFWorkflowWidget.activeTabWidget != None:
            tt = WFWorkflowWidget.activeTabWidget.tabText(0)
            if tt[-1] != '*':
                tt += '*'
                WFWorkflowWidget.activeTabWidget.setTabText(0,tt)
        
    @staticmethod
    def unChanged():
        logger = logging.getLogger('WFELOG')
        logger.info("WorkFlow has changed")
        WFWorkflowWidget.changedFlag=True
      

class WFControlWidget(QtGui.QFrame):
    def __init__(self, editor, parent=None):
        super(WFControlWidget, self).__init__(parent) 
        self.logger = logging.getLogger('WFELOG')
        self.editor = editor
      
        
        self.setFrameStyle(QtGui.QFrame.Panel)
        self.setStyleSheet("background: " + widgetColors['Control'])
        self.setAcceptDrops(True)
        self.isVisible = True     # the subwidget are is visible
        self.layout    = QtGui.QVBoxLayout()
        
        noPar=self.makeTopLine()
        self.wf = []
        self.hidden = []
        self.bottomLayout = QtGui.QHBoxLayout()
        self.elementSkip = 0 
        for i in range(noPar):
            wf = WFBaseWidget(editor,self)
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
    
    def clear(self):
        for w in self.wf:
            w.clear()
            w.deleteLater()
    
    def gatherExports(self,wano,varExp,filExp,waNoNames):
        self.logger.error('gather exports for control elements not implemented')
        pass
    
    def parse(self,xml):
        print ("Unknown FunctionXXX")
        pass 
            
    def xml(self):
        ee =  etree.Element(mapClassToTag(self.__class__.__name__))
        for e in self.wf:
            ee.append(e.xml())
        return ee 
    
    def toggleVisible(self):
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
            #print ("WFControlElement Child Height:",ypos)
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
            self.move(e.globalPos())
            dropAction = drag.start(QtCore.Qt.MoveAction)

class WFWhileWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFWhileWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'While'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 1
    
class WFIfWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFIfWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'If'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 2

class WFForEachWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFForEachWidget, self).__init__(editor,  parent)      
        
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
    def __init__(self, editor, parent=None):
        super(WFParallelWidget, self).__init__(editor,  parent)      
        
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
        wf = WFBaseWidget(self.editor,self)
        self.elementSkip = max(self.elementSkip,wf.elementSkip)
        wf.myName = self.myName + "WF" + str(self.bottomLayout.count())
        wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        wf.autoResize = True
        self.wf.append(wf)       
        self.bottomLayout.addWidget(wf)
        self.placeElements()
        
 
    def parse(self,xml):
        count = 0
        for c in xml:      
            if c.tag != 'Base':
                self.logger.error("Found Tag ",c.tag, " in control block")
            else:
                if count > 2:
                    self.addWF() 
                self.wf[count].parse(c)
                count += 1
        if count != len(self.wf):
            self.logger.error("Not enough base widgets in control element")
