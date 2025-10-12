from datetime import date, datetime
from typing import List, Optional, Dict, Any
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
	# GPT Analysis fields - temporarily commented out until database migration
	# gpt_summary: Optional[str] = None
	# gpt_key_risks: Optional[str] = None  # JSON string
	# gpt_recommendations: Optional[str] = None  # JSON string
	# gpt_overall_assessment: Optional[str] = None
	# gpt_confidence_score: Optional[str] = None
	# gpt_analysis_date: Optional[datetime] = None
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


class GPTAnalysisResponse(BaseModel):
	summary: str
	key_risks: List[Dict[str, str]]
	recommendations: List[str]
	overall_assessment: str
	confidence_score: float
	analysis_date: Optional[str] = None


class GPTAdviceRequest(BaseModel):
	question: str
	contract_id: Optional[int] = None


class GPTAdviceResponse(BaseModel):
	advice: str 