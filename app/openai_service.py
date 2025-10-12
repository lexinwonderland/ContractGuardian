import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class GPTAnalysisResult:
    """Result from GPT analysis of a contract"""
    summary: str
    key_risks: List[Dict[str, str]]
    recommendations: List[str]
    overall_assessment: str
    confidence_score: float

class OpenAIService:
    """Service for interacting with OpenAI GPT models"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
    async def analyze_contract_with_gpt(self, contract_text: str, contract_title: str = "Contract") -> Optional[GPTAnalysisResult]:
        """
        Analyze a contract using GPT for additional insights beyond rule-based analysis
        """
        if not self.is_available():
            logger.warning("OpenAI service not available - API key missing")
            return None
        
        try:
            # Truncate text if too long to stay within token limits
            max_chars = 8000  # Conservative limit for GPT-4
            if len(contract_text) > max_chars:
                contract_text = contract_text[:max_chars] + "\n\n[Text truncated for analysis...]"
            
            system_prompt = """You are Contract Guardian, an expert contract analyst specializing in protecting creators, influencers, and content producers from unfair contract terms. 

Your role is to:
1. Identify potential risks and unfair terms that could harm the signer
2. Provide clear, actionable recommendations
3. Assess the overall fairness of the contract
4. Focus on protecting the signer's rights, income, and creative control

Analyze the contract text and provide a structured response in JSON format with the following fields:
- summary: A brief 2-3 sentence overview of what this contract is about
- key_risks: Array of objects with "risk" and "impact" fields describing major concerns
- recommendations: Array of specific, actionable recommendations for the signer
- overall_assessment: A brief assessment of whether this contract is fair, concerning, or needs significant changes
- confidence_score: A number between 0-1 indicating your confidence in this analysis

Be thorough but concise. Focus on the most important issues that could significantly impact the signer."""

            user_prompt = f"""Please analyze this contract titled "{contract_title}":

{contract_text}

Provide your analysis in the JSON format specified above."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            try:
                analysis_data = json.loads(content)
                return GPTAnalysisResult(
                    summary=analysis_data.get("summary", ""),
                    key_risks=analysis_data.get("key_risks", []),
                    recommendations=analysis_data.get("recommendations", []),
                    overall_assessment=analysis_data.get("overall_assessment", ""),
                    confidence_score=float(analysis_data.get("confidence_score", 0.5))
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {e}")
                logger.error(f"Response content: {content}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    async def get_contract_advice(self, question: str, contract_context: str = "") -> Optional[str]:
        """
        Get specific advice about a contract question using GPT
        """
        if not self.is_available():
            return None
        
        try:
            system_prompt = """You are Contract Guardian, a helpful assistant for contract-related questions. Provide clear, practical advice focused on protecting the signer's interests. Keep responses concise and actionable."""
            
            user_prompt = f"""Question: {question}
            
            {f"Contract context: {contract_context}" if contract_context else ""}
            
            Please provide helpful advice."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting contract advice: {e}")
            return None

# Global instance
openai_service = OpenAIService()
