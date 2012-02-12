#!/usr/bin/python 

"""Simple listener:
- track and add dns records only for instances boot
- doesn't track terminate of instances
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
flags.DEFINE_list("dns_ns", ["localhost"], "Name servers")

#TODO add flag "dns_create_ptr", and create PTR records

class Listener(AMQPListener):
    def __init__(self):
	self.pending={}
	self.conn=sqlalchemy.engine.create_engine(FLAGS.sql_connection).connect()
	dnsmanager_class=utils.import_class(FLAGS.dns_manager);
	self.dnsmanager=dnsmanager_class()

    def event(self, e):
        method = e.get("method", "<unknown>")
	if not method=="run_instance":
	    LOG.debug("Skip message with method: "+method)
	    return
	#FIXME change pendign to set
	self.pending[id]=1
#	    dict(id = e["args"]["instance_id"],
#            name = e["args"]["request_spec"]["instance_properties"]["display_name"],
#	    project_id = e["args"]["request_spec"]["instance_properties"]["project_id"])
    def _pollip(self):
	#FIXME add protection against raises!! - in zone add, in records add 
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
		del self.pending['r.id']
		#FIXME add normalizing project_id
		zones_list=self.dnsmanager.list()
		if FLAGS.dns_zone not in zones_list:
		    #Lazy create main zone and populate by ns
		    #FIXME raise 
		    self.dnsmanager.add(FLAGS.dns_zone)
		    zone=self.dnsmanager.get(FLAGS.dns_zone)
		    for ns in FLAGS.dns_ns:
			#FIXME raise
			zone.add(DNSRecord(name=ns, type="NS"))
		zonename=r.project_id+'.'+FLAGS.dns_zone
		if zonename not in zones_list:
		    #FIXME raise
		    self.dnsmanager.add(zonename)
		#FIXME raise
		self.dnsmanager.get(zonename).add(DNSRecord(name=r.hostname, 
		    content=r.address))
