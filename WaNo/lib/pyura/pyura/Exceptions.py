#import Exception

class DeletedResourceRequested(Exception):
    """This exception is raised when a resource is requested that has been
    deleted on the server but was not (yet) deleted on the client.
    """
    pass
