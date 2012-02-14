
__version__ = "0.0.4"

try: 
    from nova import flags
    FLAGS = flags.FLAGS

    flags.DEFINE_string("dns_manager", "nova_dns.dnsmanager.powerdns.Manager",
                        "DNS manager class")
    flags.DEFINE_string("dns_listener", "nova_dns.listener.simple.Listener",
                        "Class to process AMQP messages")
except:
    #make setup.py happy
    pass

