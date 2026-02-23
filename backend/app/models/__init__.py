from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime, timezone
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    boundary = Column(Geometry("MULTIPOLYGON", srid=4326))
    area_sq_miles = Column(Numeric(8, 4))
    population = Column(Integer)
    created_at = Column(DateTime, default=utcnow)

    scores = relationship("NeighborhoodScore", back_populates="neighborhood")
    crime_incidents = relationship("CrimeIncident", back_populates="neighborhood")
    service_requests = relationship("ServiceRequest", back_populates="neighborhood")
    building_permits = relationship("BuildingPermit", back_populates="neighborhood")
    traffic_incidents = relationship("TrafficIncident", back_populates="neighborhood")
    ems_incidents = relationship("EmsIncident", back_populates="neighborhood")


class CrimeIncident(Base):
    __tablename__ = "crime_incidents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(200), unique=True, nullable=False)
    offense_type = Column(String(200))
    category = Column(String(100))
    severity = Column(String(50))
    location = Column(Geometry("POINT", srid=4326))
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    occurred_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)

    neighborhood = relationship("Neighborhood", back_populates="crime_incidents")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(200), unique=True, nullable=False)
    complaint_type = Column(String(200))
    category = Column(String(100))
    location = Column(Geometry("POINT", srid=4326))
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    opened_at = Column(DateTime)
    closed_at = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, default=utcnow)

    neighborhood = relationship("Neighborhood", back_populates="service_requests")


class BuildingPermit(Base):
    __tablename__ = "building_permits"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(200), unique=True, nullable=False)
    permit_type = Column(String(200))
    work_type = Column(String(100))
    location = Column(Geometry("POINT", srid=4326))
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    issued_at = Column(DateTime)
    permit_value = Column(Numeric(14, 2))
    created_at = Column(DateTime, default=utcnow)

    neighborhood = relationship("Neighborhood", back_populates="building_permits")


class TrafficIncident(Base):
    __tablename__ = "traffic_incidents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(200), unique=True, nullable=False)
    incident_type = Column(String(200))
    location = Column(Geometry("POINT", srid=4326))
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    occurred_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)

    neighborhood = relationship("Neighborhood", back_populates="traffic_incidents")


class EmsIncident(Base):
    __tablename__ = "ems_incidents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(200), unique=True, nullable=False)
    problem_description = Column(String(200))
    location = Column(Geometry("POINT", srid=4326))
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    occurred_at = Column(DateTime)
    response_time_secs = Column(Integer)
    created_at = Column(DateTime, default=utcnow)

    neighborhood = relationship("Neighborhood", back_populates="ems_incidents")


class NeighborhoodScore(Base):
    __tablename__ = "neighborhood_scores"

    id = Column(Integer, primary_key=True, index=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    computed_at = Column(DateTime, default=utcnow)
    overall_score = Column(Numeric(5, 2))
    safety_score = Column(Numeric(5, 2))
    infrastructure_score = Column(Numeric(5, 2))
    emergency_response_score = Column(Numeric(5, 2))
    development_score = Column(Numeric(5, 2))
    score_version = Column(String(20), default="1.0")

    neighborhood = relationship("Neighborhood", back_populates="scores")


class MonthlyAggregate(Base):
    __tablename__ = "monthly_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    dataset = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    record_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utcnow)


class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id = Column(Integer, primary_key=True, index=True)
    dataset = Column(String(50), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    records_ingested = Column(Integer)
    records_rejected = Column(Integer)
    last_ingested_at = Column(DateTime)
    status = Column(String(20))


class BlockGroupNeighborhood(Base):
    __tablename__ = "block_group_neighborhood"

    block_group_id = Column(String(20), primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    neighborhood_name = Column(String(100))