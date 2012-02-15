REST API
===============================

.. contents::
      :depth: 3


Reply format
------------

All commands return JSON, all except *Version* return json in *JSON RPC* format: 

.. code-block:: javascript

    {        
        "error": "",
        "result": ""
    }

* **result** - The Object that was returned by the invoked method. This must be
  null in case there was an error invoking the method.
* **error** - An Error object if there was an error invoking the method. It must
  be null if there was no error. 




Version info and links
----------------------

**GET /**

return version info and links

.. code-block:: javascript

    # curl "localhost:15353/" | python -m json.tool
    {
        "application": "nova-dns",
        "links": [
            {
                "href": "http://127.0.0.1:15353/zone",
                "rel": "self"
            },
            {
                "href": "http://127.0.0.1:15353/record",
                "rel": "self"
            }
        ],
        "version": "0.0.5"
    }

Work with zones
---------------

List of all zones
+++++++++++++++++

**GET /zone**

return list of registered zones 

.. code-block:: javascript

    # curl "localhost:15353/zone/" | python -m json.tool
    {
        "error": null,
        "result": [
            "example.test.com",
            "test.com"
        ]
    }



Get zone's SOA
++++++++++++++

**GET /zone/name**

return SOA record if zone exists or "*Zone does not exist*" error otherwise 

.. code-block:: javascript

    # curl "localhost:15353/zone/test.com" | python -m json.tool
    {
        "error": null,
        "result": {
            "content": "",
            "expire": 604800,
            "hostmaster": "hostmaster",
            "name": "",
            "primary": "ns1",
            "priority": 0,
            "refresh": 10800,
            "retry": 3600,
            "serial": "1329317890",
            "ttl": 7200,
            "type": "SOA"
        }
    }


Create zone
+++++++++++

**PUT /zone/name[?soa_params]**

Create new zone. if any SOA  param omitted, backend has to use reasonable default. 

SOA params: 

* primary
* hostmaster
* refresh
* retry
* expire
* ttl

Return 'ok' on success or "*"Zone already exists*" error

.. code-block:: javascript 

    # curl "localhost:15353/zone/some.test.com" -X PUT | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }


Delete zone
+++++++++++

**DELETE /zone/name[?force=1]**

Drop zone and all records in zone.

If "force" param provided, will delete all sub-zones

If not - will refuse to delete if there are any sub-zone for this zone
with "*Subzones exists: (list of zones)*" error

Return "ok" on success

.. code-block:: javascript

    # curl "localhost:15353/zone/test.com" -X DELETE | python -m json.tool
    {
        "error": "Subzones exists: test.com example.test.com some.test.com",
        "result": null
    }

    # curl "localhost:15353/zone/some.test.com" -X DELETE | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }

    # curl "localhost:15353/zone/test.com?force=1" -X DELETE | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }


Work with records
-----------------

Aceptable record type
+++++++++++++++++++++

Record type can be any from

.. code-block:: bash

   'A', 'AAAA', 'MX', 'SOA', 'CNAME', 'PTR', 'SPF', 'SRV', 'TXT', 'NS',
   'AFSDB', 'CERT', 'DNSKEY', 'DS', 'HINFO', 'KEY', 'LOC', 'NAPTR', 'RP', 
   'RRSIG', 'SSHFP'

in case of invalid type of record error "*Incorrect type: your_value*"
will be generated

List records
++++++++++++

**GET /record/zonename[?name=&type=]**

On success return JSON in format TODO: 
 
.. code-block:: javascript

    {
        "content": "",
        "name": "",
        "priority": 0,
        "ttl": ,
        "type": ""
    },

If *name* or *type* params provided, results will be filtered to specified
names and/or types

.. code-block:: javascript

    # curl "localhost:15353/record/test.com" | python -m json.tool
    {
        "error": null,
        "result": [
            {
                "content": "2.2.2.2",
                "name": "dynamic.test.com",
                "priority": 0,
                "ttl": 120,
                "type": "A"
            },
            {
                "content": "",
                "expire": 604800,
                "hostmaster": "hostmaster",
                "name": "",
                "primary": "ns1",
                "priority": 0,
                "refresh": 10800,
                "retry": 3600,
                "serial": "1329319594",
                "ttl": 7200,
                "type": "SOA"
            },
            {
                "content": "1.1.1.1",
                "name": "test.com",
                "priority": 0,
                "ttl": 7200,
                "type": "A"
            },
            {
                "content": "1.1.1.1",
                "name": "mx1.test.com",
                "priority": 10,
                "ttl": 7200,
                "type": "MX"
            }
        ]
    }



Add record
++++++++++

**PUT /record/zonename/name/type/content[?ttl&priority]**

Add record 

.. warning:: *SOA* record can't be added thru this intreface
.. note:: *SOA* serial will be updated automatically
.. note:: If name empty, provide **@**. 


.. code-block:: javascript

    # curl "localhost:15353/record/test.com/@/a/1.1.1.1" -X PUT | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }
    # curl "localhost:15353/record/test.com/mx1/mx/1.1.1.1?priority=10" -X PUT | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }
    # curl "localhost:15353/record/test.com/dynamic/a/2.2.2.2?ttl=120" -X PUT | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }


Edit record
+++++++++++

**POST /record/zonename/name/type?[params]**

Editable params: 

* **content**
* **ttl**
* **priority**

Update record. Return 'ok' on success

.. note:: *SOA* serial will be updated automatically

.. code-block:: javascript

    # curl "localhost:15353/record/test.com/@/A?content=3.3.3.3" -X POST | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }

    
Delete record
+++++++++++++

**DELETE /record/zonename/name/type**

Delete record. Return 'ok' on success

.. code-block:: javascript

    # curl "localhost:15353/record/test.com/dynamic/a" -X DELETE | python -m json.tool
    {
        "error": null,
        "result": "ok"
    }

