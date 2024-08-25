# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function
from sqlite3 import dbapi2 as sqlite
import logging

from sqlalchemy import create_engine, asc, desc, text
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import and_, func
import os.path

Base = declarative_base(cls=DeferredReflection)

log = logging.getLogger(__name__)


def flush(session):
    session.flush()

def commit(session):
    session.flush()
    session.commit()
    return True


# http://alextechrants.blogspot.co.uk/2013/11/10-common-stumbling-blocks-for.html

def column_windows(session, column, windowsize):
    """Return a series of WHERE clauses against 
    a given column that break it into windows.

    Result is an iterable of tuples, consisting of
    ((start, end), whereclause), where (start, end) are the ids.

    Requires a database that supports window functions, 
    i.e. Postgresql, SQL Server, Oracle.

    Enhance this yourself !  Add a "where" argument
    so that windows of just a subset of rows can
    be computed.

    """

    def int_for_range(start_id, end_id):
        if end_id:
            return and_(
                column >= start_id,
                column < end_id
            )
        else:
            return column >= start_id

    q = session.query(
        column,
        func.row_number(). \
            over(order_by=column). \
            label('rownum')
    ). \
        from_self(column)
    if windowsize > 1:
        q = q.filter(text("rownum %% %d=1" % windowsize))

    intervals = [id for id, in q]

    while intervals:
        start = intervals.pop(0)
        if intervals:
            end = intervals[0]
        else:
            end = None
        yield int_for_range(start, end)


def _yield_limit(qry, pk_attr, maxrq=100, order='asc'):
    """Specialized windowed query generator (using LIMIT/OFFSET)

    Note:
        Modified version of from https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/WindowedRangeQuery

        This recipe is to select through a large number of rows thats too
        large to fetch at once. The technique depends on the primary key
        of the FROM clause being an integer value, and selects items
        using LIMIT.

    Args:
        qry : The Query
        | pk_attr : column that holds the primary_key (int)
        | maxrq : the number of records/rows per yeild
        | order: asc if order != 'desc'

    """

    firstid = None
    while True:
        if order == 'desc':
            q = qry.order_by(desc(pk_attr))
        else:
            q = qry.order_by(asc(pk_attr))
        if firstid is not None:
            if order == 'desc':
                q = qry.filter(pk_attr < firstid).order_by(desc(pk_attr))
            else:
                q = qry.filter(pk_attr > firstid).order_by(asc(pk_attr))
        rec = None
        for rec in q.order_by(pk_attr).limit(maxrq):
            yield rec
        if rec is None:
            break
        firstid = pk_attr.__get__(rec, pk_attr) if rec else None


def setup_db(connection_string, echo=False):
    # TODO: app.config['SQLALCHEMY_POOL_SIZE'] = 100 and app.config['SQLALCHEMY_POOL_RECYCLE'] = 280 for fixed max connection times
    # http://stackoverflow.com/questions/6471549/avoiding-mysql-server-has-gone-away-on-infrequently-used-python-flask-server
    engine = setup_engine(connection_string, echo)
    prepare_engine(Base, engine)
    create_metadata(engine)
    return create_session(engine)

def construct_connection_string(config_root_dir, db_cofnig_dict):
    if db_cofnig_dict.has_key('pyconnector'):
        db_cofnig_dict['pyconnector'] = u'+{0}'.format(db_cofnig_dict['pyconnector'])
    else:
        db_cofnig_dict['pyconnector'] = '+pymysql'
    if db_cofnig_dict.has_key('port'):
        db_cofnig_dict['port'] = u':{0}'.format(db_cofnig_dict['port'])
    else:
        db_cofnig_dict['port'] = ''

    if not db_cofnig_dict.has_key('host'):
        db_cofnig_dict['host'] = 'localhost'
    if db_cofnig_dict.has_key('echo'):
        if db_cofnig_dict['echo'].lower() == 'false':
            db_cofnig_dict['echo'] = False
        elif db_cofnig_dict['echo'].lower() == 'true':
            db_cofnig_dict['echo'] = True
        else:
            db_cofnig_dict['echo'] = False
    else:
        db_cofnig_dict['echo'] = False

    if not db_cofnig_dict.has_key('charset'):
        db_cofnig_dict['charset'] = 'utf8'
    if db_cofnig_dict['dialect'] == 'sqlite':
        return "sqlite://%s" % os.path.join(config_root_dir, 'zerrphix.db')
    else:
        return '{dialect}{pyconnector}://{username}:{password}@{host}{port}/{database}?charset={charset}'.format(
                dialect=db_cofnig_dict['dialect'],
                pyconnector=db_cofnig_dict['pyconnector'],
                username=db_cofnig_dict['username'],
                password=db_cofnig_dict['password'],
                host=db_cofnig_dict['host'],
                port=db_cofnig_dict['port'],
                database=db_cofnig_dict['database'],
                charset=db_cofnig_dict['charset'],
            )

def setup_engine(connection_string, echo=False):
    if connection_string.startswith('sqlite'):
        engine = create_engine(connection_string)
    else:
        engine = create_engine(connection_string, echo=echo, pool_recycle=3200)
    return engine


def prepare_engine(Base, engine):
    # auto load all tables
    Base.prepare(engine)


def create_metadata(engine):
    # get metdata for all tables
    Base.metadata.create_all(engine)


def create_session(engine):
    # http://stackoverflow.com/questions/6471549/avoiding-mysql-server-has-gone-away-on-infrequently-used-python-flask-server
    # bind engine to Session
    Session = scoped_session(sessionmaker(bind=engine))
    # create a session to use
    # session = Session()
    return Session

    # Taken from https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/WindowedRangeQuery might be usefull in the future
    # def windowed_query(q, column, windowsize):
    #    """"Break a Query into windows on a given column."""
    #
    #    for whereclause in column_windows(
    #                                        q.session,
    #                                        column, windowsize):
    #        for row in q.filter(whereclause).order_by(column):
    #            yield row
    #
    # if __name__ == '__main__':
    #    from sqlalchemy import Column, Integer, create_engine
    #    from sqlalchemy.orm import Session
    #    from sqlalchemy.ext.declarative import declarative_base
    #    import random
    #
    #    Base = declarative_base()
    #
    #    class Widget(Base):
    #        __tablename__ = 'widget'
    #        id = Column(Integer, primary_key=True)
    #        data = Column(Integer)
    #
    #    e = create_engine('postgresql://scott:tiger@localhost/test', echo='debug')
    #
    #    Base.metadata.drop_all(e)
    #    Base.metadata.create_all(e)
    #
    #    # get some random list of unique values
    #    data = set([random.randint(1, 1000000) for i in xrange(10000)])
    #
    #    s = Session(e)
    #    s.add_all([Widget(id=i, data=j) for i, j in enumerate(data)])
    #    s.commit()
    #
    #    q = s.query(Widget)
    #
    #    for widget in windowed_query(q, Widget.data, 1000):
    #        print "data:", widget.data
    #
