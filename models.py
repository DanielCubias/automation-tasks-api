from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class URLList(Base):
    __tablename__ = "url_lists"
    id = Column(String, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    urls = relationship("URL", back_populates="url_list")

class URL(Base):
    __tablename__ = "urls"
    id = Column(String, primary_key=True)
    url_list_id = Column(String, ForeignKey("url_lists.id"))
    name = Column(String)
    url = Column(String)
    url_list = relationship("URLList", back_populates="urls")

class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    url_list_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
