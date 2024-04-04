from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    enrollments = relationship('Enrollment', back_populates='user')

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    enrollments = relationship('Enrollment', back_populates='course')

class Enrollment(Base):
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    enrollment_date = Column(DateTime, server_default=func.now())
    completion_date = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')