

class Foo:
    def __init__(self,string):
        self.string = string
    def set(self):
        self.string = 'New'
        
s   = 'hello world'
foo = Foo(s)
print s
foo.set()
print s 


