from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	email = Column(String(255), unique=True, nullable=False, index=True)
	password_hash = Column(String(255), nullable=False)
	password_salt = Column(String(255), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	contracts = relationship("Contract", back_populates="user")


class Contract(Base):
	__tablename__ = "contracts"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(255), nullable=False)
	counterparty = Column(String(255), nullable=True)
	production = Column(String(255), nullable=True)
	contract_date = Column(Date, nullable=True)
	stored_filename = Column(String(512), nullable=True)
	text = Column(Text, nullable=False)
	status = Column(String(20), nullable=True, default="hold")  # hold, negotiating, signed
	consent_notes = Column(Text, nullable=True)  # Notes about consent/usage categories
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

	user = relationship("User", back_populates="contracts")
	flags = relationship("ClauseFlag", back_populates="contract", cascade="all, delete-orphan")


class ClauseFlag(Base):
	__tablename__ = "clause_flags"

	id = Column(Integer, primary_key=True, index=True)
	contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
	category = Column(String(100), nullable=False)
	severity = Column(String(20), nullable=False)
	start_index = Column(Integer, nullable=True)
	end_index = Column(Integer, nullable=True)
	excerpt = Column(Text, nullable=True)
	explanation = Column(Text, nullable=False)
	guidance = Column(Text, nullable=False)

	contract = relationship("Contract", back_populates="flags") 