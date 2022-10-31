#
# WaNo = Workflow Actice Nodes are the element Workflows are made of 
#
#
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
from   lxml import etree

        
class WorkflowControlElement(object):
    def __init__(self):
        self.logger = logging.getLogger('WFELOG')
        self.wf = []

    def parse(self,xml):
        count = 0
        for c in xml:
            if c.tag != 'Base':
                self.logger.error("Found Tag ",c.tag, " in control block")
            else:
                print("Not implemented yet")
                #w = WorkFlow(c)
                #self.wf[count].parse(c)
                count += 1
                #self.wf.append(e)
        if count != len(self.wf):
            self.logger.error("Not enough base widgets in control element")
#
# Workflow Control Elements
#
class ForEach(WorkflowControlElement):
    def __init__(self, c):
        super(ForEach,self).__init__(self)
        self.parse(c)
        
        
class If(WorkflowControlElement):
    def __init__(self, c):
        super(If,self).__init__(self)
        self.parse(c)
        
        
class While(WorkflowControlElement):
    def __init__(self, c):
        super(While,self).__init__(self)
        self.parse(c)
        
class Parallel(WorkflowControlElement):
    def __init__(self, c):
        super(Parallel, self).__init__()
        self.parse(c)
