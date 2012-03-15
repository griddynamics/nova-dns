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

"""Simple listener:
- doesn't sync state with dns after restart
- stateless"""

import time
import eventlet
import sqlalchemy.engine

from nova import log as logging
from nova import utils
from nova import flags

from nova_dns.dnsmanager import DNSRecord
from nova_dns.listener import AMQPListener
from nova_dns import auth



LOG = logging.getLogger("nova_dns.listener.simple")
FLAGS = flags.FLAGS
SLEEP = 60 

AUTH = auth.AUTH

#TODO make own zone for every instance
#TODO add flag "dns_create_ptr", and create PTR records
flags.DEFINE_list("dns_ns", "ns1:127.0.0.1", "Name servers, in format ns1:ip1, ns2:ip2")

class Listener(AMQPListener):
    def __init__(self):
        self.pending={}
        self.conn=sqlalchemy.engine.create_engine(FLAGS.sql_connection)
        dnsmanager_class=utils.import_class(FLAGS.dns_manager);
        self.dnsmanager=dnsmanager_class()
        self.eventlet = eventlet.spawn(self._pollip)

    def event(self, e):
        method = e.get("method", "<unknown>")
        id = e["args"].get("instance_id", None)
        #name = e["args"]["request_spec"]["instance_properties"]["display_name"]
        # project_id = e["args"]["request_spec"]["instance_properties"]["project_id"])
        if method=="run_instance":
            LOG.info("Run instance %s. Waiting on assing ip address" % (str(id),))
            self.pending[id]=1
        elif method=="terminate_instance":
            if self.pending.has_key(id): del self.pending[id]
            rec = self.conn.execute("select hostname, project_id "+
                "from instances where id=%s", id).first()
            if not rec:
                LOG.error('Unknown id: '+id)
            else:
                try:
                    LOG.info("Instance %s hostname '%s' was terminated" %
                        (id, rec.hostname))
                    #TODO check if record was added/changed by admin
                    zonename = AUTH.tenant2zonename(rec.project_id)
                    zone=self.dnsmanager.get(zonename)
                    zone.delete(rec.hostname, 'A')
                except:
                    pass
        else:
            LOG.debug("Skip message with method: "+method)
    def _pollip(self):
        while True:
            time.sleep(SLEEP)
            if not len(self.pending):
                continue
            #TODO change select to i.id in ( pendings ) to speed up
            for r in self.conn.execute("""
                select i.hostname, i.id, i.project_id, f.address
                from instances i, fixed_ips f
                where i.id=f.instance_id"""):
                if r.id not in self.pending: continue
                LOG.info("Instance %s hostname %s adding ip %s" %
                    (r.id, r.hostname, r.address))
                del self.pending[r.id]
                zones_list=self.dnsmanager.list()
                if FLAGS.dns_zone not in zones_list:
                    #Lazy create main zone and populate by ns
                    try:
                        self.dnsmanager.add(FLAGS.dns_zone)
                        zone=self.dnsmanager.get(FLAGS.dns_zone)
                        for ns in FLAGS.dns_ns:
                            (name,content)=ns.split(':',2)
                            zone.add(DNSRecord(name=name, type="NS",
                                content=content))
                    except ValueError as e:
                        LOG.warn(str(e))
                    except:
                        pass
                zonename = AUTH.tenant2zonename(r.project_id)
                if zonename not in zones_list:
                    #TODO add exception ZoneExists and pass only it
                    try:
                        self.dnsmanager.add(zonename)
                    except ValueError as e:
                        LOG.warn(str(e))
                    except:
                        pass
                try:
                    self.dnsmanager.get(zonename).add(
                        DNSRecord(name=r.hostname, type='A', content=r.address))
                except ValueError as e:
                    LOG.warn(str(e))
                except:
                    pass
