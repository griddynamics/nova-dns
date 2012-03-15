
import os
import sys
import json
import datetime
import unittest
import stubout

from nova_dns import auth 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests

class TestCase(tests.TestCase):
    pass
    #TODO to be done after changing auth model to acl 
    
