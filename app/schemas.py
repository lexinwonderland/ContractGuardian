from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class ClauseFlagBase(BaseModel):
	category: str
	severity: str
	start_index: int | None = None
	end_index: int | None = None
	excerpt: str | None = None
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
	created_at: datetime
	stored_filename: Optional[str] = None

	class Config:
		from_attributes = True 