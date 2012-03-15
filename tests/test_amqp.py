
import os
import sys
import json
import datetime
import unittest
import stubout

from nova_dns import amqp
from nova import flags

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tests

FLAGS = flags.FLAGS

class TestListener():
    def event(self, e):
        self.event = e

class TestCase(tests.TestCase):
    run_instance_body = {
        "_context_roles": [
            "projectmanager"
        ], 
        "_context_request_id": "29615116-ddd0-4a20-8018-ef5f90f8bdf3", 
        "args": {
            "request_spec": {
                "num_instances": 1, 
                "image": {
                    "status": "active", 
                    "deleted": False, 
                    "container_format": "ami", 
                    "updated_at": "2011-12-05 12:15:26.659439", 
                    "is_public": True, 
                    "deleted_at": None, 
                    "properties": {
                        "kernel_id": "2", 
                        "owner": None, 
                        "min_ram": "0", 
                        "ramdisk_id": "1", 
                        "min_disk": "0"
                    }, 
                    "size": 216858624, 
                    "name": "SL61", 
                    "checksum": "ecd1d23a8039b72812db4fee5a11a547", 
                    "created_at": "2011-12-05 12:15:25.541042", 
                    "disk_format": "ami", 
                    "id": 4, 
                    "location": "file:///var/lib/glance/images/4"
                }, 
                "filter": None, 
                "instance_type": {
                    "rxtx_quota": 0, 
                    "deleted": False, 
                    "updated_at": None, 
                    "extra_specs": {}, 
                    "flavorid": 2, 
                    "id": 5, 
                    "local_gb": 20, 
                    "deleted_at": None, 
                    "name": "m1.small", 
                    "created_at": None, 
                    "memory_mb": 2048, 
                    "vcpus": 1, 
                    "rxtx_cap": 0, 
                    "swap": 0
                }, 
                "blob": None, 
                "instance_properties": {
                    "vm_state": "building", 
                    "availability_zone": None, 
                    "ramdisk_id": "1", 
                    "instance_type_id": 5, 
                    "user_data": "", 
                    "vm_mode": None, 
                    "reservation_id": "r-851pambx", 
                    "root_device_name": None, 
                    "user_id": "admin", 
                    "display_description": None, 
                    "key_data": None, 
                    "power_state": 0, 
                    "project_id": "systenant", 
                    "metadata": {}, 
                    "access_ip_v6": None, 
                    "access_ip_v4": None, 
                    "kernel_id": "2", 
                    "key_name": None, 
                    "display_name": None, 
                    "config_drive_id": "", 
                    "local_gb": 20, 
                    "locked": False, 
                    "launch_time": "2011-12-06T19:12:57Z", 
                    "memory_mb": 2048, 
                    "vcpus": 1, 
                    "image_ref": 4, 
                    "architecture": None, 
                    "os_type": None, 
                    "config_drive": ""
                }
            }, 
            "requested_networks": None, 
            "availability_zone": None, 
            "instance_id": 16, 
            "admin_password": None, 
            "injected_files": None
        }, 
        "_context_auth_token": None, 
        "_context_user_id": "admin", 
        "_context_read_deleted": False, 
        "_context_strategy": "noauth", 
        "_context_is_admin": True, 
        "_context_project_id": "systenant", 
        "_context_timestamp": "2011-12-06T19:12:57.805503", 
        "method": "run_instance", 
        "_context_remote_address": "128.107.79.131"
    }

    def test_process_event(self):
        FLAGS.dns_listener = "tests.test_amqp.TestListener"
        service = amqp.Service()
        service.process_event(self.run_instance_body, None)
        self.assertEqual(self.run_instance_body, service.listener.event)

    #TODO test work with actuall rabbit server - start private one for this needs
    
