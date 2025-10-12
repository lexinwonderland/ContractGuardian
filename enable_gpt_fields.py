#!/usr/bin/env python3
"""
Script to re-enable GPT fields in the models after database migration.
Run this after successfully running the database migration.
"""

import os
import sys
from pathlib import Path

def enable_gpt_fields():
    """Re-enable GPT fields in models.py and schemas.py"""
    
    # Paths to the files
    models_path = Path("app/models.py")
    schemas_path = Path("app/schemas.py")
    analyzer_path = Path("app/analyzer.py")
    
    if not models_path.exists():
        print("❌ app/models.py not found")
        return False
    
    if not schemas_path.exists():
        print("❌ app/schemas.py not found")
        return False
    
    if not analyzer_path.exists():
        print("❌ app/analyzer.py not found")
        return False
    
    try:
        # Update models.py
        with open(models_path, 'r') as f:
            models_content = f.read()
        
        # Uncomment GPT fields
        models_content = models_content.replace(
            "# gpt_summary = Column(Text, nullable=True, default=None)  # GPT-generated summary",
            "gpt_summary = Column(Text, nullable=True, default=None)  # GPT-generated summary"
        )
        models_content = models_content.replace(
            "# gpt_key_risks = Column(Text, nullable=True, default=None)  # JSON string of key risks",
            "gpt_key_risks = Column(Text, nullable=True, default=None)  # JSON string of key risks"
        )
        models_content = models_content.replace(
            "# gpt_recommendations = Column(Text, nullable=True, default=None)  # JSON string of recommendations",
            "gpt_recommendations = Column(Text, nullable=True, default=None)  # JSON string of recommendations"
        )
        models_content = models_content.replace(
            "# gpt_overall_assessment = Column(Text, nullable=True, default=None)  # Overall assessment",
            "gpt_overall_assessment = Column(Text, nullable=True, default=None)  # Overall assessment"
        )
        models_content = models_content.replace(
            "# gpt_confidence_score = Column(String(10), nullable=True, default=None)  # Confidence score",
            "gpt_confidence_score = Column(String(10), nullable=True, default=None)  # Confidence score"
        )
        models_content = models_content.replace(
            "# gpt_analysis_date = Column(DateTime, nullable=True, default=None)  # When GPT analysis was performed",
            "gpt_analysis_date = Column(DateTime, nullable=True, default=None)  # When GPT analysis was performed"
        )
        
        with open(models_path, 'w') as f:
            f.write(models_content)
        
        # Update schemas.py
        with open(schemas_path, 'r') as f:
            schemas_content = f.read()
        
        # Uncomment GPT fields
        schemas_content = schemas_content.replace(
            "# gpt_summary: Optional[str] = None",
            "gpt_summary: Optional[str] = None"
        )
        schemas_content = schemas_content.replace(
            "# gpt_key_risks: Optional[str] = None  # JSON string",
            "gpt_key_risks: Optional[str] = None  # JSON string"
        )
        schemas_content = schemas_content.replace(
            "# gpt_recommendations: Optional[str] = None  # JSON string",
            "gpt_recommendations: Optional[str] = None  # JSON string"
        )
        schemas_content = schemas_content.replace(
            "# gpt_overall_assessment: Optional[str] = None",
            "gpt_overall_assessment: Optional[str] = None"
        )
        schemas_content = schemas_content.replace(
            "# gpt_confidence_score: Optional[str] = None",
            "gpt_confidence_score: Optional[str] = None"
        )
        schemas_content = schemas_content.replace(
            "# gpt_analysis_date: Optional[datetime] = None",
            "gpt_analysis_date: Optional[datetime] = None"
        )
        
        with open(schemas_path, 'w') as f:
            f.write(schemas_content)
        
        # Update analyzer.py
        with open(analyzer_path, 'r') as f:
            analyzer_content = f.read()
        
        # Restore GPT functions
        save_function = '''def save_gpt_analysis_to_contract(contract, gpt_analysis: GPTAnalysisResult):
	"""
	Save GPT analysis results to a contract model instance
	"""
	if gpt_analysis:
		contract.gpt_summary = gpt_analysis.summary
		contract.gpt_key_risks = json.dumps(gpt_analysis.key_risks)
		contract.gpt_recommendations = json.dumps(gpt_analysis.recommendations)
		contract.gpt_overall_assessment = gpt_analysis.overall_assessment
		contract.gpt_confidence_score = str(gpt_analysis.confidence_score)
		contract.gpt_analysis_date = datetime.utcnow()'''
        
        get_function = '''def get_gpt_analysis_from_contract(contract) -> Optional[dict]:
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
		return None'''
        
        # Replace the disabled functions
        analyzer_content = analyzer_content.replace(
            '''def save_gpt_analysis_to_contract(contract, gpt_analysis: GPTAnalysisResult):
	"""
	Save GPT analysis results to a contract model instance
	Note: This function is temporarily disabled until database migration is complete
	"""
	if gpt_analysis:
		# GPT columns are temporarily commented out in the model
		# This function will work again after running the database migration
		print("Warning: GPT analysis saving is temporarily disabled until database migration")
		pass''',
            save_function
        )
        
        analyzer_content = analyzer_content.replace(
            '''def get_gpt_analysis_from_contract(contract) -> Optional[dict]:
	"""
	Retrieve GPT analysis results from a contract model instance
	Note: This function is temporarily disabled until database migration is complete
	"""
	# GPT columns are temporarily commented out in the model
	# This function will work again after running the database migration
	print("Warning: GPT analysis retrieval is temporarily disabled until database migration")
	return None''',
            get_function
        )
        
        with open(analyzer_path, 'w') as f:
            f.write(analyzer_content)
        
        print("✅ GPT fields have been re-enabled in all files!")
        print("\nNext steps:")
        print("1. Commit and push these changes")
        print("2. Your app will now have full GPT integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating files: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Re-enabling GPT fields after database migration...")
    if enable_gpt_fields():
        print("\n🎉 GPT integration is now fully enabled!")
    else:
        print("\n💥 Failed to enable GPT fields")
        sys.exit(1)
