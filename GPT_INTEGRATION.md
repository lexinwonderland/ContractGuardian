# Contract Guardian GPT Integration

This document explains how to set up and use the GPT integration in your Contract Guardian app.

## Overview

Your Contract Guardian app now includes AI-powered contract analysis using OpenAI's GPT models. This provides:

- **Enhanced Analysis**: Beyond rule-based flagging, GPT provides contextual insights
- **Risk Assessment**: AI identifies potential risks that might be missed by pattern matching
- **Actionable Recommendations**: Specific guidance for contract negotiations
- **Overall Assessment**: High-level evaluation of contract fairness

## Setup Instructions

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 2. Configure Environment Variable

#### For Local Development:
Create a `.env` file in your project root:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

#### For Render Deployment:
1. Go to your Render dashboard
2. Select your Contract Guardian service
3. Go to Environment tab
4. Add new environment variable:
   - Key: `OPENAI_API_KEY`
   - Value: `sk-your-api-key-here`
5. Save and redeploy

### 3. Run Database Migration

If you have an existing database, run the migration script:

```bash
cd /path/to/contract-guardian
python app/scripts/add_gpt_fields.py
```

This adds the necessary database columns for storing GPT analysis results.

## Features

### Automatic GPT Analysis
- New contract uploads automatically trigger GPT analysis (if API key is configured)
- Analysis runs alongside existing rule-based flagging
- Results are stored in the database for future reference

### Manual GPT Analysis
- Click "🤖 Analyze with GPT" button on any contract
- Re-analyze contracts with updated GPT models
- Get fresh insights on existing contracts

### GPT Analysis Results Include:
- **Summary**: Brief overview of the contract
- **Key Risks**: Specific risks identified by AI
- **Recommendations**: Actionable advice for negotiations
- **Overall Assessment**: Fairness evaluation
- **Confidence Score**: AI's confidence in the analysis

## API Endpoints

### New Endpoints Added:

#### `POST /contracts/{contract_id}/analyze-gpt`
Re-analyze a contract with GPT
```json
{
  "success": true,
  "gpt_analysis": {
    "summary": "This is a content creator agreement...",
    "key_risks": [
      {
        "risk": "Perpetual Rights",
        "impact": "Grants unlimited use of content forever"
      }
    ],
    "recommendations": [
      "Limit the term to 2-3 years",
      "Add approval rights for content use"
    ],
    "overall_assessment": "This contract has several concerning terms...",
    "confidence_score": 0.85
  }
}
```

#### `GET /contracts/{contract_id}/gpt-analysis`
Retrieve existing GPT analysis for a contract

#### `POST /contracts/ask-gpt`
Ask GPT questions about contracts
```json
{
  "question": "What should I negotiate in this contract?",
  "contract_id": 123
}
```

## Database Schema Changes

New columns added to `contracts` table:
- `gpt_summary` (TEXT)
- `gpt_key_risks` (TEXT, JSON)
- `gpt_recommendations` (TEXT, JSON)
- `gpt_overall_assessment` (TEXT)
- `gpt_confidence_score` (TEXT)
- `gpt_analysis_date` (DATETIME)

## Cost Considerations

- GPT-4 API calls cost approximately $0.03 per 1K input tokens and $0.06 per 1K output tokens
- Typical contract analysis uses ~2K-4K tokens total
- Cost per analysis: ~$0.10-$0.20
- Consider implementing usage limits for production use

## Error Handling

The app gracefully handles GPT service unavailability:
- If API key is missing, GPT features are disabled
- If API calls fail, users see helpful error messages
- Rule-based analysis continues to work regardless of GPT status

## Security Notes

- API key is stored as environment variable (never in code)
- GPT analysis is performed server-side
- Contract text is sent to OpenAI (ensure compliance with your data policies)
- Consider data retention policies for contract text

## Troubleshooting

### GPT Analysis Not Working
1. Check that `OPENAI_API_KEY` is set correctly
2. Verify API key has sufficient credits
3. Check Render logs for error messages
4. Ensure database migration was run

### High API Costs
1. Implement rate limiting
2. Add user quotas
3. Consider caching analysis results
4. Use GPT-3.5-turbo for lower costs (modify in `openai_service.py`)

### Performance Issues
1. GPT analysis has 60-second timeout
2. Large contracts are truncated to 50K characters
3. Consider async processing for better UX

## Customization

### Modify GPT Prompts
Edit the system prompt in `app/openai_service.py` to customize analysis focus.

### Change Model
Replace `"gpt-4"` with `"gpt-3.5-turbo"` in `openai_service.py` for lower costs.

### Add Custom Analysis
Extend the `GPTAnalysisResult` dataclass and update the frontend to display additional fields.

## Support

For issues with GPT integration:
1. Check the logs in Render dashboard
2. Verify API key configuration
3. Test with a simple contract first
4. Review OpenAI API documentation for rate limits and errors

---

Your Contract Guardian app is now powered by both rule-based analysis and AI insights, providing comprehensive contract protection for creators and content producers!
