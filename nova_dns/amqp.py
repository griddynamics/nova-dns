"""
AMQP listener
"""

import time
import socket

import eventlet
import json

import kombu
import kombu.entity
import kombu.messaging
import kombu.connection

from nova import exception
from nova import utils
from nova import flags
from nova import log as logging


LOG = logging.getLogger("nova_dns.listener")
FLAGS = flags.FLAGS

class Service(object):
    """
    listens for ``compute.#`` routing keys.
    """
    def __init__(self):
        self.params = dict(hostname=FLAGS.rabbit_host,
                          port=FLAGS.rabbit_port,
                          userid=FLAGS.rabbit_userid,
                          password=FLAGS.rabbit_password,
                          virtual_host=FLAGS.rabbit_virtual_host)
        self.connection = None
	self.eventlet = None
	listener_class = utils.import_class(FLAGS.dns_listener);
	self.listener = listener_class()

    def reconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except self.connection.connection_errors:
                pass
            time.sleep(1)

        self.connection = kombu.connection.BrokerConnection(**self.params)

        options = {
            "durable": FLAGS.rabbit_durable_queues,
            "auto_delete": False,
            "exclusive": False
        }

        exchange = kombu.entity.Exchange(
                name=FLAGS.control_exchange,
                type="topic",
                durable=options["durable"],
                auto_delete=options["auto_delete"])
        self.channel = self.connection.channel()

        self.queue = kombu.entity.Queue(
            name="nova_dns",
            exchange=exchange,
            routing_key="compute.#",
            channel=self.channel,
            **options)
        LOG.debug("created kombu connection: %s" % self.params)

    def process_message(self, body, message):
        try:
            self.process_event(body, message)
        except KeyError, ex:
            LOG.exception("cannot handle message")
        message.ack()

    def process_event(self, body, message):
        """
        This function receive ``body`` and pass it to listener manager
        """
	self.listener.event(body)

        try:
            routing_key = message.delivery_info["routing_key"]
        except AttributeError, KeyError:
            routing_key = "<unknown>"
        LOG.debug("routing_key=%s method=%s" % (routing_key, body["method"]))

    def consume(self):
        """
        Get messages in an infinite loop. This is the main function of service's green thread.
        """
        while True:
            try:
                self.reconnect()
                with kombu.messaging.Consumer(
                    channel=self.channel,
                    queues=self.queue,
                    callbacks=[self.process_message]) as consumer:
                    while True:
                        self.connection.drain_events()
            except socket.error:
                pass
            except Exception, e:
                LOG.exception(_('Failed to consume message from queue: '
                        '%s' % str(e)))

    def start(self):
        self.eventlet = eventlet.spawn(self.consume)

    def stop(self):
        self.eventlet.stop()

    def wait(self):
        self.eventlet.wait()
