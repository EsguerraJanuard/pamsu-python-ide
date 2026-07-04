from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

    tasks = relationship("Task", back_populates="instructor")
    submissions = relationship("Submission", back_populates="student")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=False)
    required_ast_rules = Column(JSON, nullable=False)

    instructor = relationship("User", back_populates="tasks")
    submissions = relationship("Submission", back_populates="task")


class Submission(Base):
    __tablename__ = "submissions"

    sub_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    raw_code = Column(Text, nullable=False)
    jaccard_score = Column(Float, nullable=True)
    ast_pass_fail = Column(Boolean, nullable=True)

    student = relationship("User", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")

    behavioral_log = relationship(
        "BehavioralLog", back_populates="submission", uselist=False
    )


class BehavioralLog(Base):
    __tablename__ = "behavioral_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    sub_id = Column(
        Integer, ForeignKey("submissions.sub_id"), unique=True, nullable=False
    )
    tab_switches_count = Column(Integer, default=0, nullable=False)

    submission = relationship("Submission", back_populates="behavioral_log")
