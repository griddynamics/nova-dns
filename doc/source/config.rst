Configuration
=============

Nova DNS uses the same configuration file ``nova.conf`` as nova
daemons and utilities. This file is usually located at ``/etc/nova`` directory.

Options, introduced by Nova DNS
-------------------------------

Core options
++++++++++++
* ``dns_manager``
  DNS manager class 
  (string, *nova_dns.dnsmanager.powerdns.Manager* by default)
* ``dns_listener``
  Class to process AMQP messages
  (string, *nova_dns.listener.simple.Listener* by default)
* ``dns_api_paste_config``, 
  File name for the paste.deploy config for nova-dns api
  (string, */etc/nova-dns/dns-api-paste.ini* by default)
* ``dns_listen``
  IP address for DNS API to listen
  (string, *0.0.0.0* by default)
* ``dns_listen_port``
  DNS API port
  (integer, *15353* by default)
* ``dns_default_ttl``
  Default record ttl
  (integer, *7200*  by default)
* ``dns_soa_primary``
  Name server that will respond authoritatively for the domain by default)
  (string, *ns1*  by default)
* ``dns_soa_email``
  (string,  *hostmaster*  by default)
  Email address of the person responsible for this zone  by default)
* ``dns_soa_refresh``
  The time when the slave will try to refresh the zone from the master  by default)
  (integer,  *10800*  by default)
* ``dns_soa_retry``
  Time between retries if the slave fails to contact the master
  (integer,  *3600*  by default)
* ``dns_soa_expire``
  Indicates when the zone data is no longer authoritative 
  (integer, *604800*  by default)
* ``dns_zone`` 
  Nova DNS base zone
  (string, *localzone* by default)
* ``dns_auth``
  "Auth mode in REST API"
  (enum ("none", "keystone"), *keystone* by default)
* ``dns_nova_auth``
  "Auth mode in Nova"
  (enum ("none", "keystone"), *keystone* by defautl)
* ``dns_auth_role``
  "Role name in REST API"
  (string, *DNS_Admin* by default)


nova_dns.dnsmanager.powerdns
++++++++++++++++++++++++++++
* ``dns_sql_connection``
  Connection string for powerdns sql database
  (string ``mysql://pdns:pdns@localhost/pdns``, by default)

nova_dns.listener.simple
++++++++++++++++++++++++
* ``dns_ns``
  Name servers, in format ns1:ip1, ns2:ip2
  (list, *ns1:127.0.0.1* by default)
* ``dns_ptr``
  Manage PTR records
  (boolean, False by default)
* ``dns_ptr_zones``
  Classless delegation networks in format ip_addr/network
  (list, '' by default)


Options, used by Nova DNS to connect to rabbit
----------------------------------------------

* ``rabbit_host``
* ``rabbit_port``
* ``rabbit_userid``
* ``rabbit_password``
* ``rabbit_virtual_host``

Logs
----

The daemon saves logs to ``nova-dns.log`` file in nova logs
directory (e.g., ``/var/log/nova``).



