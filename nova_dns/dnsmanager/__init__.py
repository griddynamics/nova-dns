#!/usr/bin/python

import re 

from nova import flags
from nova import log as logging

from abc import ABCMeta, abstractmethod

LOG = logging.getLogger("nova_dns.dnsmanager")
FLAGS = flags.FLAGS


flags.DEFINE_integer("dns_default_ttl", 7200,
                    "Default record ttl")
flags.DEFINE_string("dns_soa_primary", "ns1",
                    "Name server that will respond authoritatively for the domain")
flags.DEFINE_string("dns_soa_email", "hostmaster",
                    "Email address of the person responsible for this zone ")
flags.DEFINE_integer("dns_soa_refresh", 10800,
                    "The time when the slave will try to refresh the zone from the master")
flags.DEFINE_integer("dns_soa_retry", 3600,
                    "time between retries if the slave fails to contact the master")
flags.DEFINE_integer("dns_soa_expire", 604800,
                    "Indicates when the zone data is no longer authoritative")
record_types=set(('A', 'AAAA', 'MX', 'SOA', 'CNAME', 'PTR', 'SPF', 'SRV', 'TXT', 'NS', 
          'AFSDB', 'CERT', 'DNSKEY', 'DS', 'HINFO', 'KEY', 'LOC', 'NAPTR', 'RP', 'RRSIG', 
          'SSHFP'))


class DNSManager:
    """abstract class"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def list(self):
        """ should return list of DNSZone objects for all zones"""
        pass

    @abstractmethod
    def add(self, zone_name, soa):
        pass

    @abstractmethod
    def drop(self, zone_name, force=False):
        """ drop zone with all records. return True if was deleted """
        pass

    @abstractmethod
    def get(self, zone_name):
        """ return DNSZone object for zone_name. 
        If zone not exist, raise exception 
         """
        pass



class DNSZone:
    @abstractmethod
    def __init__(self, zone_name):
        pass
    @abstractmethod
    def drop(self):
        pass
    @abstractmethod
    def add(self, v):
        pass
    @abstractmethod
    def get(self, name, type=None):
        pass
    @abstractmethod
    def set(self, name, type, content, priority, ttl):
        pass
    @abstractmethod
    def delete(self, name, type):
        pass

class DNSRecord:
    def __init__(self, name, type, content, priority=None, ttl=None):
        self.name=DNSRecord.normname(name)
        self.type=DNSRecord.normtype(type)
        self.content=content
        self.priority=int(priority) if priority else 0
        self.ttl=int(ttl) if ttl else FLAGS.dns_default_ttl
    @staticmethod
    def normtype(type):
        t=type.upper()
        if t not in record_types:
            raise ValueError("Incorrect type: " + type)
        return t
    @staticmethod
    def normname(n):
        name = n.lower()
        if name=="" or re.match(r'\A(?:[\w\d_].)*(?:[\w\d_])\Z', name):
            return name
        else:
            raise ValueError("Incorrect DNS name: " + name)

class DNSSOARecord(DNSRecord):
    def __init__(self, primary, hostmaster, serial=None, refresh=None, retry=None, expire=None, ttl=None):
        self.primary=primary if primary else FLAGS.dns_soa_primary
        self.hostmaster=hostmaster if hostmaster else FLAGS.dns_soa_email
        self.serial=serial if serial else 0
        self.refresh=int(refresh) if refresh else FLAGS.dns_soa_refresh
        self.retry=int(retry) if retry else FLAGS.dns_soa_retry
        self.expire=int(expire) if expire else FLAGS.dns_soa_expire
        DNSRecord.__init__(self, '', 'SOA', '', None, ttl)

