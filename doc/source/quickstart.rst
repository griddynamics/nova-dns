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
   echo "--dns_ns=$LOCALIP" >> $NOVA 

start service: 

.. code-block:: bash

   service nova-dns start
