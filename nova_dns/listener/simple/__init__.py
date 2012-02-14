#!/usr/bin/python

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




LOG = logging.getLogger("nova_dns.listener.simple")
FLAGS = flags.FLAGS
SLEEP = 60

#TODO make own zone for every instance
flags.DEFINE_string("dns_zone", "localzone", "Nova DNS base zone")
flags.DEFINE_list("dns_ns", [("ns1","127.0.0.1"),], "Name servers")

#TODO add flag "dns_create_ptr", and create PTR records

class Listener(AMQPListener):
    def __init__(self):
        self.pending={}
        self.conn=sqlalchemy.engine.create_engine(FLAGS.sql_connection).connect()
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
                    zone=self.dnsmanager.get(rec.project_id+'.'+FLAGS.dns_zone)
                    zone.delete(rec.hostname, 'A')
                except:
                    pass
        else:
            LOG.debug("Skip message with method: "+method)
    def _pollip(self):
        while True:
            time.sleep(SLEEP)
            if not len(self.pending):
                LOG.debug('empty pending queue - continue')
                continue
            for r in self.conn.execute("""
                select i.hostname, i.id, i.project_id, f.address
                from instances i, fixed_ips f
                where i.id=f.instance_id"""):
                if r.id not in self.pending: continue
                LOG.info("Instance %s hostname %s adding ip %s" %
                    (r.id, r.hostname, r.address))
                del self.pending['r.id']
                zones_list=self.dnsmanager.list()
                if FLAGS.dns_zone not in zones_list:
                    #Lazy create main zone and populate by ns
                    try:
                        self.dnsmanager.add(FLAGS.dns_zone)
                        zone=self.dnsmanager.get(FLAGS.dns_zone)
                        for ns in FLAGS.dns_ns:
                            zone.add(DNSRecord(name=ns[0], type="NS",
                                content=ns[1]))
                    except ValueError as e:
                        LOG.warn(str(e))
                    except:
                        pass
                zonename=r.project_id+'.'+FLAGS.dns_zone
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
