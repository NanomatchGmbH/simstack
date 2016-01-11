# python < 3.3: requires enum34 package
from enum import Enum


class Constants(object):
    Protocols = Enum("Protocols",
                     """
                     BFT
                     RBYTEIO
                     SBYTEIO
                     """,
                     module=__name__
                     )

    JobStatus = Enum("JobStatus",
                     """
                     QUEUED
                     RUNNING
                     FAILED
                     SUCCESSFUL
                     """,
                     module=__name__
                     )

    ResourceStatus = Enum("ResourceStatus",
                          """
                          READY
                          UNAVAILABLE
                          """,
                          module=__name__
                          )
