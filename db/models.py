from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer,DateTime,String,Text,Float


from datetime import datetime
Base=declarative_base()
class Log(Base):

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime)
    ingested_at = Column(DateTime)

    service = Column(String)
    host = Column(String)

    client_ip = Column(String)
    method = Column(String)
    endpoint = Column(String)

    status_code = Column(Integer)

    response_time_ms = Column(Integer)
    bytes_in=Column(Integer)
    bytes_out=Column(Integer)

    user_agent = Column(Text)


class Feature(Base):

    __tablename__ = "features"

    id = Column(Integer, primary_key=True)

    window_start = Column(DateTime)
    window_end = Column(DateTime)

    request_count = Column(Integer)
    error_count = Column(Integer)
    error_ratio = Column(Float)

    unique_ips = Column(Integer)

    avg_response_time = Column(Float)
    unique_endpoints=Column(Integer)
    unique_user_agents=Column(Integer)

