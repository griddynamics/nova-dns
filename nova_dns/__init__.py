
__version__ = "0.1.0"

try:
    from nova import flags
    FLAGS = flags.FLAGS

    flags.DEFINE_string("dns_manager", "nova_dns.dnsmanager.powerdns.Manager",
                        "DNS manager class")
    flags.DEFINE_string("dns_listener", "nova_dns.listener.simple.Listener",
                        "Class to process AMQP messages")
    flags.DEFINE_string("dns_api_paste_config", "/etc/nova-dns/dns-api-paste.ini",
                        "File name for the paste.deploy config for nova-dns api")

except:
    #make setup.py happy
    pass

