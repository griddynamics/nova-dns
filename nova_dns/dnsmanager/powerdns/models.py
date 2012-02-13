"""
SQLAlchemy models for Nova PowerDNS.
"""

from sqlalchemy.orm import relationship, backref, object_mapper
from sqlalchemy import Column, Integer, String, schema
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKeyConstraint

from nova_dns.dnsmanager.powerdns.session import get_session, get_engine


BASE = declarative_base()


class PowerDNSBase(object):
    """Base class for Nova DNS Models."""
    _i = None

    def save(self, session=None):
        """Save this object."""

        if not session:
            session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError:
            raise

    def delete(self, session=None):
        """Delete this object."""
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict"""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class Domains(BASE, PowerDNSBase):
    __tablename__ = 'domains'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    master = Column(String(255), nullable=False)
    last_check = Column(Integer, nullable=False)
    type = Column(String(6), nullable=False)
    notified_serial = Column(Integer, nullable=False)
    account = Column(String(40), nullable=False)

class Records(BASE, PowerDNSBase):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(6), nullable=False)
    content = Column(String(255))
    ttl = Column(Integer)
    prio = Column(Integer)
    change_date = Column(Integer)
    # TODO Index('nametype_index', (`name`, `type`))


def register_models():
    """Register Models and create metadata."""
    models = (Domains, Records)
    engine = get_engine()
    for model in models:
        model.metadata.create_all(engine)

