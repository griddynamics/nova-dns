#!/usr/bin/python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova DNS
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 2.1 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
