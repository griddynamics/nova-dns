#!/usr/bin/python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova DNS
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 2.1 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import json
import unittest

import webob
import urllib

from nova_dns import dns 

from nova import flags
FLAGS = flags.FLAGS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests

zones = ['test']
soa =   dict(retry="1", primary="ns.localhost", refresh="3", expire="4", ttl="5", 
    hostmaster="me@localhost", serial="5")
add =   dict(content="1", ttl=2, priority=3)

class TestManager():
    def list(self):
        return zones

    def add(self, zone_name, soa):
        if zone_name == 'error':
            raise Exception('test error')
        return (zone_name, soa)

    def drop(self, zone_name, force=False):
        return [zone_name, force]

    def get(self, zone_name):
        return TestZone(zone_name)


class TestZone():
    def __init__(self, zone_name):
        self.zone_name = zone_name
    def drop(self):
        pass
    def add(self, v):
        return [self.zone_name, v.__dict__]
    def get(self, name, type=None):
        self.name = name
        self.type = type 
        return [self]
    def set(self, name, type, content, priority, ttl):
        return [self.zone_name, name, type, content, priority, ttl] 
    def delete(self, name, type):
        return [self.zone_name, name, type] 

class TestAuth():
    read = False
    write = False
    def can(self, req, zone_name):
        return {"read": self.read, "write": self.write}

class TestCase(tests.TestCase):
    def req(self, path, status=200, error=None, method='GET', params=None):
        #FIXME - hardcoded api-paste chain
        query = "%s?%s" % (path, urllib.urlencode(params)) if params else path
        print query
        request = webob.Request.blank(query)
        request.method = method
        res = request.get_response(dns.VersionFilter(dns.App()))
        self.assertEqual(res.status_int, status, "path %s: status %d != %d" % 
            (path, res.status_int, status))
        #special case for version
        if path == '/':
            return res.body
        if res.status_int != 200:
            return
        res = json.loads(res.body)
        self.assertEqual(error, res['error'])
        return res['result']

    def test_app(self):
        FLAGS.dns_manager = "tests.test_dns.TestManager"
        AUTH = TestAuth()
        dns.AUTH = AUTH

        self.req('/')
        self.req('/incorrect_path', status=404)

        AUTH.read = False
        self.req('/zone/', error='unauthorized')
        AUTH.read = True
        self.assertEqual(self.req('/zone/'), zones)
        
        #TODO add more tests with AUTH - delayed with this as auth model
        #will change
        AUTH.write = True

        self.assertEqual(self.req('/zone/testadd', method='PUT', params=soa), ['testadd', soa])
        self.req('/zone/error', method='PUT', error="test error")

        self.assertEqual(self.req('/zone/testdel', method='DELETE', params={"force": True}), 
            ['testdel', 'True'])
        self.assertEqual(self.req('/zone/testdel', method='DELETE'), ['testdel', None])

        self.assertEqual(self.req('/record/testzone', params={'type':'A', 'name': '@'}),
            [dict(zone_name='testzone',  type='A', name='')])
        self.assertEqual(self.req('/record/testzone'), 
            [dict(zone_name='testzone',  type=None, name=None)])

        self.assertEqual(self.req('/record/testzone/@/A', method='POST', params=add), 
            ['testzone', '', 'A',  add['content'], str(add['priority']), str(add['ttl'])])

        self.assertEqual(self.req('/record/testzone/some/MX/'+add['content'], method='PUT', 
            params=add), ['testzone', dict(add.items(), name='some', type='MX')])
        self.assertEqual(self.req('/record/testzone/@/A/'+add['content'], method='PUT', 
            params=add), ['testzone', dict(add.items(), name='', type='A')])
        self.assertEqual(self.req('/record/testzone/@/A/'+add['content'], method='PUT'), 
            ['testzone', dict(name='', type='A', content=add['content'],
            priority=0, ttl=7200)])
        self.req('/record/testzone/@/INCORRECT/'+add['content'], method='PUT', 
            params=add, error='Incorrect type: INCORRECT')

        self.assertEqual(self.req('/record/testzone/@/A', method='DELETE'),
            ['testzone', '', 'A'])
        self.assertEqual(self.req('/record/testzone/some/MX', method='DELETE'),
            ['testzone', 'some', 'MX'])


