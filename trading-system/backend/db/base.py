"""
Declarative base for all SQLAlchemy ORM models.
Import Base from here — never redefine it elsewhere.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
