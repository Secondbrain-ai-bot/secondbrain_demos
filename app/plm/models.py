"""SQLAlchemy ORM models for the PLM database."""

from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Part(Base):
    """Engineering part / document header record."""

    __tablename__ = "parts"

    part_number = Column(String, primary_key=True)
    part_name = Column(String, nullable=False)
    part_type = Column(String, nullable=False)       # assembly | sub_assembly | component
    revision = Column(String, nullable=False)
    lifecycle_state = Column(String, nullable=False)  # released | in_work | obsolete
    drawing_id = Column(String, nullable=False)


class Drawing(Base):
    """Engineering drawing record — one row per authoritative file."""

    __tablename__ = "drawings"

    drawing_id = Column(String, primary_key=True)
    part_number = Column(String, nullable=False)
    drawing_number = Column(String, nullable=False)
    revision = Column(String, nullable=False)
    drawing_title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)        # relative path from project root
    file_type = Column(String, nullable=False)        # pdf | png
    sheet_count = Column(Integer, default=1)
    drawing_status = Column(String, nullable=False)   # released | in_work | superseded


def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
