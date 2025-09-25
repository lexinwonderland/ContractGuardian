from dataclasses import dataclass
from typing import List
import re


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