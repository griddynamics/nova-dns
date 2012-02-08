#!/usr/bin/python 

import time

from nova import flags
from nova import log as logging
from nova_dns.backend import DNSManager, DNSZone, DNSRecord, DNSSOARecord
from nova_dns.backend.powerdns.session import get_session
from nova_dns.backend.powerdns.models import Domains, Records
LOG = logging.getLogger("nova_dns.backend.powerdns")

models.register_models()

class Manager(DNSManager):
    def __init__(self):
	self.session=get_session()
    def list(self): 
	return [name[0] for name in self.session.query(Domains.name).all()]
    def add(self, zone_name, soa):
	if zone_name in self.list():
	    raise Exception('Zone already exists')
	self.session.add(Domains(name=zone_name, type="NATIVE"))
	self.session.flush()
	soa=DNSSOARecord(**soa)
	# PowerDNS-specific. TODO make this more pytonish - with objects
	# and bells
	soa.content=" ".join((str(f) for f in (soa.primary, soa.hostmaster, soa.serial, 
	    soa.refresh, soa.retry, soa.expire, soa.ttl)))
	PowerDNSZone(zone_name).add(soa)
	return "ok"
    def drop(self, zone_name, force=False):
	domains=self.session.query(Domains).filter(Domains.name.like('%'+zone_name)).all()
	if not domains:
	    raise Exception('Zone not exists')
	elif len(domains)>1 and not force:
	    raise Exception("Subzones exists: " + " ".join([d.name for d in domains]))
	for domain in domains:
	    PowerDNSZone(domain.name).drop()
	    self.session.delete(domain)
	self.session.flush()
	return "ok"
    def get(self, zone_name):
	if zone_name in self.list():
	    return PowerDNSZone(zone_name)
	else:
	    raise Exception('Zone does not exist')

class PowerDNSZone(DNSZone):
    def __init__(self, zone_name):
	self.zone_name=zone_name
	self.session=get_session()
	domain=self.session.query(Domains).filter(Domains.name==zone_name).first()
	if not domain:
	    raise Exception("Unknown zone: "+zone_name)
	self.domain_id=domain.id
    def get_soa(self):
	content=self._q().filter(Records.type=='SOA').first().content
	#content format is "primary hostmaster serial refresh retry expire ttl"
	#so we can magically pass it to consrtuctor
	return DNSSOARecord(*content.split())
    def drop(self):
	self._q().delete()
    def add(self, v):
	rec=Records()
	rec.domain_id=self.domain_id
	rec.name=rec.name=v.name+"."+self.zone_name if v.name else self.zone_name
	rec.type=v.type
	rec.content=v.content
	rec.ttl=v.ttl
	rec.prio=v.priority
	rec.change_date=int(time.time())
	#check uniq()
	self.session.add(rec)
	self.session.flush()
	self._update_serial(rec.change_date)
	return "ok"
    def get(self, name='', type=None):
	q=self._q();
	if name:
	    self._qname(q,name)
	if type:
	    self._qtype(q,type)
	res=[]
	for r in q.all():
	    if r.type=='SOA':
		res.append(DNSSOARecord(*r.content.split()))
	    else:
		res.append(DNSRecord(name=r.name, content=r.content,
		    priority=r.prio, ttl=r.ttl))
	return res
    def set(self, name, type, content="", priority="", ttl=""):
	q=self._q(); 
	self._qname(q, name); 
	self._qtype(q, type);
	rec=q.first()
	if not rec:
	    raise Exception("Not found record (%s,%s)" % (name, type))
	if content:
	    rec.content=content
	if ttl:
	    rec.ttl=ttl
	if priority:
	    rec.prio=priority
	rec.change_date=int(time.time())
	self.session.merge(rec)
	self._update_serial(rec.change_date)
	self.session.flush()
    def delete(self, name, type=None):
	q=self._q()
	self._qname(q, name)
	if type:
	    self._qtype(q, type)
	if q.delete():
	    return "ok"
	else:
	    raise Exception("No records was deleted")	
    def _update_serial(self, serial):
	#TODO change to get_soa
	soa=self._q().filter(Records.type=='SOA').first()
	v=soa.content.split()
	#TODO change this to ordinar set()
	v[2]=serial
	content=" ".join((str(f) for f in v))
	soa.update({"content":content})
    def _q(self):
	return self.session.query(Records).filter(Records.domain_id==self.domain_id)
    def _qtype(self,q,type):
	q=q.filter(Records.type==type.upper())
    def _qname(self,q,name):
	q=q.filter(Records.name==name+"."+self.zone_name)
	

