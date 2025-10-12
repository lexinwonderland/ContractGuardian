from dataclasses import dataclass
from typing import List, Optional
import re
import json
from datetime import datetime
from .openai_service import get_openai_service, GPTAnalysisResult


@dataclass
class Rule:
	category: str
	severity: str
	pattern: re.Pattern
	explanation: str
	guidance: str


def _rules() -> List[Rule]:
	return [
		Rule(
			category="Perpetual Rights",
			severity="high",
			pattern=re.compile(r"in perpetuity|perpetual rights|forever irrevocable", re.IGNORECASE),
			explanation="The agreement appears to grant rights forever (perpetual). This can mean you lose control of your work or likeness indefinitely.",
			guidance="Ask to limit the term (e.g., 1-3 years) and specify exactly what rights are granted and where."
		),
		Rule(
			category="Exclusivity / Non-Compete",
			severity="high",
			pattern=re.compile(r"exclusive\s+(services|rights)|non-\s*compete|exclusivity", re.IGNORECASE),
			explanation="Exclusive or non-compete terms can block you from working with others or earning elsewhere.",
			guidance="Ask to remove exclusivity, narrow it to specific projects/brands, or add a short, paid exclusivity window."
		),
		Rule(
			category="Arbitration / Venue",
			severity="medium",
			pattern=re.compile(r"binding arbitration|waive\s+jury|venue\s+shall\s+be|governing law", re.IGNORECASE),
			explanation="Arbitration and venue clauses can limit how and where disputes are resolved, often favoring the company.",
			guidance="Ask for your local venue, the right to bring claims in court, and a mutual choice of law that is neutral."
		),
		Rule(
			category="Indemnification",
			severity="high",
			pattern=re.compile(r"indemnif(y|ication)|hold\s+harmless", re.IGNORECASE),
			explanation="One-sided indemnification can make you responsible for broad legal risks.",
			guidance="Make indemnification mutual and limited to breaches you actually cause, capped at fees received."
		),
		Rule(
			category="Ownership of Content / Likeness",
			severity="high",
			pattern=re.compile(r"work for hire|assign\s+all\s+rights|exclusive\s+license|use of likeness", re.IGNORECASE),
			explanation="Transferring ownership or broad likeness rights can mean you can't control use of your image or content.",
			guidance="Clarify you retain ownership and grant only a narrow, time-limited license for specified uses."
		),
		Rule(
			category="Unilateral Changes",
			severity="medium",
			pattern=re.compile(r"we\s+may\s+modify\s+this\s+agreement|subject to change without notice", re.IGNORECASE),
			explanation="Allows the other party to change terms without your consent.",
			guidance="Require written mutual agreement for changes and notice periods."
		),
		Rule(
			category="Confidentiality / Penalties",
			severity="medium",
			pattern=re.compile(r"non-?disparagement|liquidated damages|confidentiality", re.IGNORECASE),
			explanation="Overbroad confidentiality or penalties can silence you or impose heavy fees.",
			guidance="Limit to legitimate trade secrets; remove punitive liquidated damages; allow safety and legal reporting."
		),
		Rule(
			category="Payment Terms / Chargebacks",
			severity="medium",
			pattern=re.compile(r"chargebacks|net\s*\d+|payment\s+upon\s+acceptance|withhold\s+payment", re.IGNORECASE),
			explanation="Slow or conditional payment terms and chargebacks can delay or reduce your income.",
			guidance="Ask for clear rates, payment on delivery or within 7-14 days, and limit chargebacks to valid, documented issues."
		),
		Rule(
			category="Cancellation / No-Show Fees",
			severity="low",
			pattern=re.compile(r"cancellation fee|no-?show fee|forfeit fee", re.IGNORECASE),
			explanation="Fees for cancellations or no-shows may be excessive or one-sided.",
			guidance="Set fair, mutual cancellation terms with reasonable notice periods."
		),
		Rule(
			category="Ownership of Content / Likeness",
			severity="high",
			pattern=re.compile(r"absolute right and permission to use", re.IGNORECASE),
			explanation="Grants extremely broad rights to use your content or likeness without meaningful limits.",
			guidance="Narrow the grant to specific, necessary uses; limit scope, territory, and duration; retain approval rights for sensitive uses."
		),
		Rule(
			category="Broad Media Rights",
			severity="high",
			pattern=re.compile(r"in any media now known or hereinafter\s+invented", re.IGNORECASE),
			explanation="Allows use across all current and future media, which is unusually broad and risky.",
			guidance="Limit media types to those actually needed today, or require mutual consent for new media in the future."
		),
		Rule(
			category="Perpetual Rights",
			severity="high",
			pattern=re.compile(r"without\s+time", re.IGNORECASE),
			explanation="Suggests no time limit on rights, effectively making them perpetual.",
			guidance="Add a clear term (e.g., 1-3 years) and renewal only by mutual written agreement."
		),
		Rule(
			category="Payment Terms / Compensation",
			severity="medium",
			pattern=re.compile(r"no\s+claim\s+to\s+compensation", re.IGNORECASE),
			explanation="States you have no right to compensation, which can waive payment for your work or likeness.",
			guidance="Ensure express compensation terms are included, or remove any clause waiving compensation rights."
		),
        # Broad, perpetual, and universe-wide rights phrases flagged per user guidance
        Rule(
            category="Broad/Perpetual Rights Language",
            severity="high",
            pattern=re.compile(
                r"(" \
                r"owns\s+all\s+rights|" \
                r"perpetual(?:ly)?\s+in\s+any\s+manner\s+whatsoever|" \
                r"by\s+any\s+present\s+or\s+future\s+devices|" \
                r"perpetual\s+right\s+to\s+use\s+my\s+name|" \
                r"any\s+other\s+person\s+or\s+company\s+who\s+holds\s+or\s+acquires|" \
                r"to\s+alter,?\s+dub,?\s+revise|" \
                r"change\s+in\s+any\s+manner\s+whatsoever|" \
                r"rights?\s+to\s+be\s+worldwide\s+and\s+in\s+perpetuity|" \
                r"including\s+the\s+right\s+to\s+reproduce,?\s+use|" \
                r"by\s+any\s+present\s+or\s+future\s+means\s+and\s+devices|" \
                r"throughout\s+the\s+universe|" \
                r"in\s+perpetuity\s+in\s+all\s+media|" \
                r"whether\s+now\s+known\s+or\s+hereafter\s+devised|" \
                r"for\s+any\s+medium" \
                r")",
                re.IGNORECASE,
            ),
            explanation="Very broad or perpetual rights language detected (e.g., universe-wide, all media, present/future devices, perpetual name/image use). Such terms can permanently transfer or license your rights without limits.",
            guidance="Ask to limit scope (specific uses), territory, and term; remove universe-wide and perpetual language; require approvals for edits (alter/dub/revise) and name/likeness uses; consult union/agent or counsel."
        ),
	]


def analyze_text(text: str):
	flags = []
	for rule in _rules():
		for match in rule.pattern.finditer(text or ""):
			start = match.start()
			end = match.end()
			excerpt = text[max(0, start - 80): min(len(text), end + 80)]
			flags.append({
				"category": rule.category,
				"severity": rule.severity,
				"start_index": start,
				"end_index": end,
				"excerpt": excerpt,
				"explanation": rule.explanation,
				"guidance": rule.guidance,
			})
	return flags


async def analyze_contract_comprehensive(text: str, contract_title: str = "Contract") -> dict:
	"""
	Perform comprehensive contract analysis using both rule-based and GPT analysis
	Returns a dictionary with both rule-based flags and GPT analysis results
	"""
	# Perform rule-based analysis
	rule_flags = analyze_text(text)
	
	# Perform GPT analysis if available
	gpt_analysis = None
	openai_service = get_openai_service()
	if openai_service.is_available():
		try:
			gpt_analysis = await openai_service.analyze_contract_with_gpt(text, contract_title)
		except Exception as e:
			print(f"GPT analysis failed: {e}")
	
	# Prepare result
	result = {
		"rule_based_flags": rule_flags,
		"gpt_analysis": None,
		"analysis_timestamp": datetime.utcnow().isoformat()
	}
	
	# Add GPT analysis if available
	if gpt_analysis:
		result["gpt_analysis"] = {
			"summary": gpt_analysis.summary,
			"key_risks": gpt_analysis.key_risks,
			"recommendations": gpt_analysis.recommendations,
			"overall_assessment": gpt_analysis.overall_assessment,
			"confidence_score": gpt_analysis.confidence_score
		}
	
	return result


def save_gpt_analysis_to_contract(contract, gpt_analysis: GPTAnalysisResult):
	"""
	Save GPT analysis results to a contract model instance
	"""
	if gpt_analysis:
		contract.gpt_summary = gpt_analysis.summary
		contract.gpt_key_risks = json.dumps(gpt_analysis.key_risks)
		contract.gpt_recommendations = json.dumps(gpt_analysis.recommendations)
		contract.gpt_overall_assessment = gpt_analysis.overall_assessment
		contract.gpt_confidence_score = str(gpt_analysis.confidence_score)
		contract.gpt_analysis_date = datetime.utcnow()


def get_gpt_analysis_from_contract(contract) -> Optional[dict]:
	"""
	Retrieve GPT analysis results from a contract model instance
	"""
	if not contract.gpt_summary:
		return None
	
	try:
		return {
			"summary": contract.gpt_summary,
			"key_risks": json.loads(contract.gpt_key_risks) if contract.gpt_key_risks else [],
			"recommendations": json.loads(contract.gpt_recommendations) if contract.gpt_recommendations else [],
			"overall_assessment": contract.gpt_overall_assessment,
			"confidence_score": float(contract.gpt_confidence_score) if contract.gpt_confidence_score else 0.0,
			"analysis_date": contract.gpt_analysis_date.isoformat() if contract.gpt_analysis_date else None
		}
	except (json.JSONDecodeError, ValueError) as e:
		print(f"Error parsing GPT analysis from contract: {e}")
		return None 