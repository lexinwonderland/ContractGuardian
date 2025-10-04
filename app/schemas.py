from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class ClauseFlagBase(BaseModel):
	category: str
	severity: str
	start_index: Optional[int] = None
	end_index: Optional[int] = None
	excerpt: Optional[str] = None
	explanation: str
	guidance: str


class ClauseFlagRead(ClauseFlagBase):
	id: int

	class Config:
		from_attributes = True


class ContractBase(BaseModel):
	title: str
	counterparty: Optional[str] = None
	production: Optional[str] = None
	contract_date: Optional[date] = None


class ContractCreate(ContractBase):
	text: str
	stored_filename: Optional[str] = None


class ContractRead(ContractBase):
	id: int
	stored_filename: Optional[str] = None
	text: str
	status: Optional[str] = None
	consent_notes: Optional[str] = None
	created_at: datetime
	flags: List[ClauseFlagRead] = []

	class Config:
		from_attributes = True


class ContractListItem(BaseModel):
	id: int
	title: str
	counterparty: Optional[str]
	production: Optional[str]
	contract_date: Optional[date]
	status: Optional[str] = None
	consent_notes: Optional[str] = None
	created_at: datetime
	stored_filename: Optional[str] = None

	class Config:
		from_attributes = True


class ContractStatusUpdate(BaseModel):
	status: str
	consent_notes: Optional[str] = None 