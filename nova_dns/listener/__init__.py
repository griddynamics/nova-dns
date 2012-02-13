#!/usr/bin/python

from nova import log as logging
from nova import flags

from abc import ABCMeta, abstractmethod

LOG = logging.getLogger("nova_dns.listener")
FLAGS = flags.FLAGS



class AMQPListener:
    """abstract class"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def event(self, event):
        """process event"""
        pass
