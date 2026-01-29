from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base

class URLList(Base):
    __tablename__ = "url_lists"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    urls = relationship("URL", back_populates="url_list", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="url_list", cascade="all, delete-orphan")


class URL(Base):
    __tablename__ = "urls"
    id = Column(String, primary_key=True)
    url_list_id = Column(String, ForeignKey("url_lists.id"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

    url_list = relationship("URLList", back_populates="urls")


class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    url_list_id = Column(String, ForeignKey("url_lists.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    count = Column(Integer, nullable=False, default=0)

    url_list = relationship("URLList", back_populates="runs")
    results = relationship("RunResult", back_populates="run", cascade="all, delete-orphan")


class RunResult(Base):
    __tablename__ = "run_results"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)

    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

    ok = Column(Boolean, nullable=False, default=False)
    status_code = Column(Integer, nullable=True)  # puede ser None si falla
    time_ms = Column(Integer, nullable=False)
    error = Column(String, nullable=True)

    run = relationship("Run", back_populates="results")
