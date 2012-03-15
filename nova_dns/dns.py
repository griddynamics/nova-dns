# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova DNS
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
DNS rest service
"""

import eventlet
import json

from nova import flags
from nova import log as logging
from nova import utils

import webob
import routes
import routes.middleware

from nova import wsgi
from nova import service
from nova_dns import __version__
from nova_dns.dnsmanager import DNSRecord, DNSSOARecord
from nova_dns.auth import AUTH

LOG = logging.getLogger("nova_dns.dns")
FLAGS = flags.FLAGS


flags.DEFINE_string("dns_listen", "0.0.0.0",
                    "IP address for DNS API to listen")
flags.DEFINE_integer("dns_listen_port", 15353,
                    "DNS API port")

class Service(service.WSGIService):
    """
    """
    def __init__(self):
        service.WSGIService.__init__(self, name="dns",
            loader=wsgi.Loader(config_path=FLAGS.dns_api_paste_config))


class VersionFilter(object):
    """
    Filter returning version for "/" request
    """
    def __init__(self, application):
        self.application = application

    @webob.dec.wsgify
    def __call__(self, req):
        if req.environ.get("PATH_INFO", "/") == "/":
            version = json.dumps({
                "version": __version__,
                "application": "nova-dns",
                "links": [{ 
                    "href": "http://%s:%s/zone" %
                      (req.environ["SERVER_NAME"], req.environ["SERVER_PORT"]),
                    "rel": "self"},
                    { "href": "http://%s:%s/record" %
                      (req.environ["SERVER_NAME"], req.environ["SERVER_PORT"]),
                    "rel": "self"}]
                })
            return webob.Response(version, content_type='application/json')
        return req.get_response(self.application)

    @classmethod
    def factory(cls, global_config, **local_config):
        def filter(app):
            return cls(app)
        return filter


class Controller(object):
    """
    WSGI application that reads routing information supplied by ``RoutesMiddleware``
    and returns a report.
    """

    def __init__(self):
        manager_class=utils.import_class(FLAGS.dns_manager);
        self.manager=manager_class()

    @webob.dec.wsgify
    def __call__(self, req):
        """
        """
        try:
            args = req.environ["wsgiorg.routing_args"][1]
            action = args["action"]
            if action in ('index', 'zone_get', 'list'):
                action_type = "read"
            else:
                action_type = "write"
            #TODO remove keystone middleware and directly authenticate
            #with keystoneclient.tokens.authneticate - right now this is
            #buggy - if token incorect, keystonectlient return amazing
            #error 'maximum recursion depth exceeded in cmp'
            if not AUTH.can(req, args.get('zonename', None))[action_type]:
                raise Exception('unauthorized')
            result={}

            if action=="index":
                result=self.manager.list()
            elif action=="zone_get":
                result=self.manager.get(args['zonename']).get_soa().__dict__
            elif action=="zone_del":
                result=self.manager.drop(args['zonename'], req.GET.get('force', None))
            elif action=="zone_add":
                soa={}
                for p in ("primary", "hostmaster", "serial", "refresh",
                    "retry", "expire", "ttl"):
                    soa[p]=req.GET.get(p, None)
                result=self.manager.add(args['zonename'], soa)
            elif action=="list":
                name=req.GET.get('name', None)
                name="" if name=='@' else name
                type=req.GET.get('type', None)
                records=self.manager.get(args['zonename']).get(name=name, type=type)
                result=[r.__dict__ for r in records] 
            elif action=="record_add":
                rec=DNSRecord(
                    name="" if args['name']=='@' else args['name'],
                    content=args['content'], type=args['type'],
                    ttl=req.GET.get('ttl', None),
                    priority=req.GET.get('priority', None))
                result=self.manager.get(args['zonename']).add(rec)
            elif action=="record_del":
                name="" if args['name']=='@' else args['name']
                result=self.manager.get(args['zonename']).delete(name, args['type'])
            elif action=="record_edit":
                name="" if args['name']=='@' else args['name']
                result=self.manager.get(args['zonename']).set(
                    name=name,
                    type=args['type'],
                    content=req.GET.get('content', None),
                    ttl=req.GET.get('ttl', None),
                    priority=req.GET.get('priority', None)
                )
            else:
                raise Exception("Incorrect action: "+action)
            return webob.Response(json.dumps({"result":result, "error":None}),
                content_type='application/json')
        except Exception as e:
            return webob.Response(json.dumps({"result":None, "error":str(e)}),
                content_type='application/json')

class App(wsgi.Router):
    """
    This application parses HTTP requests and calls ``Controller``.
    """

    def __init__(self):
        """
        GET /
            return version info and links
        GET /zone
            return list of all zones
        GET /zone/name
            return JSON for SOA if zone exists
        PUT /zone/name[?soa_params]
            create new zone. if no params for SOA provided, backend
            _has_to_ use reasonable defaults. Return 'ok' on success
        DELETE /zone/name[?force]
            drop zone and all records in zone.
            if "force" param provided, will delete all sub-zones
            if not - will refuse to delete if there are any sub-zone for
                this zone
            return "ok" on success
        GET /record/zonename[?name=&type=]
            return JSON (array of objects). Will return 'err' if zone or
                or (name, type) not exists
        PUT /record/zonename/name/type/content[?ttl&priority]
            add record. return 'ok' on success. set name to '@' if empty
        POST /record/zonename/name/type?[params]
            return 'ok' on success, 'err' if zonename or (name, type) not exists
        DELETE /record/zonename/name/type
        """
        #FIXME rewrite dict(controller=Controller(), action="...") to
        #controller=Controller
        #....controller=conntroller.index
        map = routes.Mapper()
        map.connect(None, "/zone/",
            controller=Controller(), action="index")
        map.connect(None, "/zone/{zonename}", conditions=dict(method=["GET"]),
            controller=Controller(), action="zone_get")
        map.connect(None, "/zone/{zonename}", conditions=dict(method=["PUT"]),
            controller=Controller(), action="zone_add")
        map.connect(None, "/zone/{zonename}", conditions=dict(method=["DELETE"]),
            controller=Controller(), action="zone_del")
        map.connect(None, "/record/{zonename}", conditions=dict(method=["GET"]),
            controller=Controller(), action="list")
        map.connect(None, "/record/{zonename}/{name}/{type}/{content}",
            conditions=dict(method=["PUT"]), controller=Controller(),
            action="record_add")
        map.connect(None, "/record/{zonename}/{name}/{type}",
            conditions=dict(method=["POST"]), controller=Controller(),
            action="record_edit")
        map.connect(None, "/record/{zonename}/{name}/{type}",
            conditions=dict(method=["DELETE"]), controller=Controller(),
            action="record_del")
        super(App, self).__init__(map)

    @classmethod
    def factory(cls, global_config, **local_config):
        return cls()
