# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova DNS
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Authorization
"""


import ConfigParser

from nova import flags
from keystoneclient.v2_0 import client as keystone_client
from dnsmanager import DNSRecord

FLAGS = flags.FLAGS

flags.DEFINE_enum("dns_auth", "keystone", ["none", "keystone"],     
                    "Auth mode in REST API")
flags.DEFINE_enum("dns_nova_auth", "keystone", ["none", "keystone"],     
                    "Auth mode in Nova")
flags.DEFINE_string("dns_auth_role", "DNS_Admin", "Role name in REST API")
flags.DEFINE_string("dns_zone", "localzone", "Nova DNS base zone")



class NoAuth(object):
    def tenant2zonename(self, project_id):
        return "%s.%s" % (DNSRecord.normname(project_id), FLAGS.dns_zone)
    def can(self, req, zone_name): 
        return {"read":True, "write":True}

class KeystoneAuth(NoAuth):
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read(FLAGS.dns_api_paste_config)
        self.token = config.get("filter:authtoken", "admin_token")
        self.url = "%s://%s:%s/v2.0" % (
            config.get("filter:authtoken", "auth_protocol"),
            config.get("filter:authtoken", "auth_host"),
            config.get("filter:authtoken", "auth_port"))
        self.client = keystone_client.Client(
            endpoint=self.url, token=self.token)
        self.tenants = {}

    def tenant2zonename(self, project_id):
        #project_id is a really project_id :)
        return super(KeystoneAuth, self).tenant2zonename(self._get_tenant(project_id))
    
    def can(self, req, zone_name): 
        roles = [r.strip()
                 for r in req.headers.get('X_ROLE', '').split(',')]
        if "Admin" in roles:
            return {"read":True, "write":True}
        if FLAGS.dns_auth_role not in roles:
            return {"read":True, "write":False}
        # will raise if no X_TENANT_ID header
        name = self.tenant2zonename(req.headers['X_TENANT_ID'])
        can_write = DNSRecord.normname(zone_name) == DNSRecord.normname(name)
        return {"read":True, "write":can_write}


    def _get_tenant(self, id):
        if not self.tenants.has_key(id):
            #probably new tenant, let's re-read cache
            self.tenants={}
            for t in self.client.tenants.list():
                self.tenants[t.id] = t.name
        name = self.tenants.get(id, None)
        if not name:
            #nope, not new
            raise ValueError('Unknown tenant_id: %s' % (str(id)))
        return name

AUTH = NoAuth() if FLAGS.dns_auth == 'none' else KeystoneAuth()

