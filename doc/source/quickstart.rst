Quickstart
===========================

Environment
***********

Quick installation of nova-dns with:

* use **PowerDNS** as DNS backend (with
  *nova_dns.dnsmanager.powerdns.Manager* **dns_manager**) 
* use **MySQL** database as storage for **PowerDNS**
* use *nova_dns.listener.simple.Listener* as AMQP listener

Installation
************

.. code-block:: bash

   yum install nova-dns

.. note:: installation from *epel* repository

.. code-block:: bash

   yum install pdns pdns-backend-mysql


Configuration
*************

Create database
---------------

.. code-block:: bash

   export DBNAME="pdns"
   export DBUSER="pdns"
   export DBPASS="pdns"
   export DBROOTPASS="nova"
   echo "create database $DBNAME; grant all on $DBNAME.* " \
          " to $DBUSER@localhost identified by '$DBPASS'" \
     | mysql -u root -p"$DBROOTPASS"

Configure PowerDNS
------------------

Choose local ip addresses to bind, comma separated:

.. warning:: if you run nova-dns on same server with nova-compute, 
   there are already started one or several dnsmasq on 53 port on local
   interfaces

.. code-block:: bash

   export LOCALIP="127.0.0.1"
   echo "launch=gmysql
   gmysql-host=127.0.0.1
   gmysql-dbname=$DBNAME
   gmysql-user=$DBUSER
   gmysql-password=$DBPASS
   local-address=$LOCALIP" > /etc/pdns/pdns.conf
   
Start the server and add it to autostart:

.. code-block:: bash

    service pdns start
    chkconfig pdns on

.. warning:: quick setup of slave PowerDNS

Configure nova-dns 
------------------

locate nova.conf (usually in /etc/nova/nova.conf):

.. code-block:: bash

   export NOVA=/etc/nova/nova.conf

add credentials for SQL connection:

.. code-block:: bash

   echo "--dns_sql_connection=mysql://$DBUSER:$DBPASS@localhost/$DBNAME" >> $NOVA

setup defaults for SOA:

.. code-block:: bash

   echo "--dns_default_ttl=7200
   --dns_soa_primary=ns1@my_host.com
   --dns_soa_email=hostmaster@my_host.com" >> $NOVA

setup zone for fixed_ip records: 

.. code-block:: bash

   echo "--dns_zone=cloud.my_host.com" >> $NOVA

setup ns servers: 

.. code-block:: bash 

   LOCALDNS=`perl -e '$ns=1; print join(",", map {sprintf "ns%d:%s", $ns++, $_} split /\s*,\s*/,$ARGV[0])' "$LOCALIP"
   echo "--dns_ns=$LOCALDNS" >> $NOVA 

^^^^^^^^^^^^^^^^^^^^^
Configure PTR support
^^^^^^^^^^^^^^^^^^^^^

Turn on managing PTR records:

.. code-block:: bash

   echo "--dns_ptr" >> $NOVA

PTR records will be created for C class network, *octet3.octet2.octet1.id-addr.arpa* zone will be created automatically if not exists

Turn on classless delegation (Sub-delegate less than a class C (< 256 IP
addresses)):

.. code-block:: bash

   export ZONES="192.168.1.0/28, 192.168.2.0/24" #just example
   echo "--dns_ptr_zones=$PTR_ZONES" >> $NOVA

For examples above PTR records will be added in zones
*0-28.1.168.192.in-addr.arpa* and *0-24.2.168.192.in-addr.arpa*


add service in keystone

.. code-block:: bash

   keystone-manage service add nova_dns nova_dns "DNS for OpenStack"
   keystone-manage endpointTemplates add RegionOne nova_dns http://$LOCALIP:15353 http://$LOCALIP:15353 http://$LOCALIP:15353 1 1

start service: 

.. code-block:: bash

   service nova-dns start
