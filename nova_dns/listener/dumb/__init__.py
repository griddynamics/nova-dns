#!/usr/bin/python 

"""Dumb listener - only log events """

from nova import log as logging
from nova_dns.listener import AMQPListener

LOG = logging.getLogger("nova_dns.listener.dumb")

methods=set(("run_instance", "terminate_instance", "stop_instance", 
    "start_instance", "pause_instance", "unpause_instance",
    "resume_instance", "suspend_instance"))

class Listener(AMQPListener):
    def event(self, e):
        method = e.get("method", "<unknown>")
        if method not in methods:
            LOG.debug("Skip message with method: "+method)
            return
        contextproject_id = e["_context_project_id"]
        id = e["args"]["instance_id"]
        try: 
            name = e["args"]["request_spec"]["instance_properties"]["display_name"]
        except: 
            name = "<unknown>" 
        LOG.warning("Method %s instance_id '%s' project_id '%s' instance name '%s'" % 
            (method, str(id), str(contextproject_id), name))
