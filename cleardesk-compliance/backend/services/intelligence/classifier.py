"""
Document Classifier - Identifies document types using Groq API.

WHAT IT IS: Sends extracted text to Groq and gets back structured document type identification.
WHY IT EXISTS: The agent must know what it is dealing with before it knows what data to extract.
WHAT IT DOES:
    Sends text to Groq with all possible document types listed.
    Gets back JSON classification. Stores result in database.
"""

import json
from typing import Dict, Any
from sqlalchemy.orm import Session

from config import settings
from models import Document


# Comprehensive list of Ghanaian/West African business documents
DOCUMENT_TYPES = {
    # Tax & Revenue
    "GRA_VAT_RETURN": "Ghana Revenue Authority VAT Return",
    "GRA_INCOME_TAX": "GRA Income Tax Return",
    "GRA_PAYE": "Pay As You Earn Monthly Filing",
    "GRA_WITHHOLDING_TAX": "Withholding Tax Certificate",
    "GRA_TAX_CLEARANCE": "Tax Clearance Certificate",
    "GRA_CORPORATE_TAX": "Corporate Tax Self-Assessment",
    # Customs
    "CUSTOMS_IMPORT_DECL": "Import Declaration Form",
    "CUSTOMS_EXPORT_DECL": "Export Declaration Form",
    "CUSTOMS_BILL_OF_ENTRY": "Bill of Entry",
    "CUSTOMS_PACKING_LIST": "Packing List",
    "CUSTOMS_COMM_INVOICE": "Commercial Invoice for Customs",
    # HR & Labour
    "SSNIT_CONTRIBUTION": "SSNIT Contribution Form",
    "SSNIT_EMPLOYEE_REG": "SSNIT Employee Registration",
    "PAYROLL_SHEET": "Payroll Sheet",
    "EMPLOYMENT_CONTRACT": "Employment Contract",
    # Finance
    "SUPPLIER_INVOICE": "Supplier Invoice",
    "PURCHASE_ORDER": "Purchase Order",
    "BANK_STATEMENT": "Bank Statement",
    "BANK_RECONCILIATION": "Bank Reconciliation Statement",
    "EXPENSE_REPORT": "Expense Report",
    # Procurement
    "TENDER_DOCUMENT": "Tender Document",
    "RFQ_FORM": "Request for Quotation",
    "SUPPLIER_REGISTRATION": "Supplier Registration Form",
    # General
    "DELIVERY_NOTE": "Delivery Note / GRN",
    "RECEIPT": "Payment Receipt",
    "BOARD_RESOLUTION": "Board Resolution",
    "UNKNOWN": "Document type could not be identified"
}


CLASSIFICATION_PROMPT = """
You are a document classification expert specialising in Ghanaian and West African business documents.

Analyze the document text and identify:
1. document_type: Choose EXACTLY ONE from this list:
{document_types_list}

2. issuing_organization: Organisation that issued this document
3. document_period: Time period covered (e.g. Q1 2025, January 2025)
4. key_identifiers: TIN numbers, reference numbers, account numbers
5. confidence: How confident you are (0.0 to 1.0)
6. classification_reason: One sentence explaining your choice

RULES:
- If genuinely unclear, use UNKNOWN — do not guess
- Return ONLY valid JSON, no extra text
- Format: {{ "document_type": "...", "issuing_organization": "...", "document_period": "...", "key_identifiers": {{...}}, "confidence": 0.0, "classification_reason": "..." }}

Document text:
---
{document_text}
---
"""


async def classify_document(
    document_text: str,
    document_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Classify a document using Groq API.
    
    Args:
        document_text: Extracted text from the document
        document_id: ID of the document to update
        db: Database session
        
    Returns:
        Classification result dictionary
    """
    # Build document types list for the prompt
    types_list = "\n".join([f"- {k}: {v}" for k, v in DOCUMENT_TYPES.items()])
    
    # Truncate text if too long (Groq has token limits)
    truncated_text = document_text[:4000] if len(document_text) > 4000 else document_text
    
    prompt = CLASSIFICATION_PROMPT.format(
        document_types_list=types_list,
        document_text=truncated_text
    )
    
    # Call Groq API
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # Low temperature for consistent classification
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
    
    # Parse the response
    content = result["choices"][0]["message"]["content"]
    
    try:
        classification = json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract JSON from the response
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            classification = json.loads(content[start_idx:end_idx])
        else:
            raise ValueError("Failed to parse classification response as JSON")
    
    # Update document in database
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        document.classified_type = classification.get("document_type", "UNKNOWN")
        document.classification_confidence = classification.get("confidence", 0.0)
        document.issuing_organization = classification.get("issuing_organization")
        document.document_period = classification.get("document_period")
        document.key_identifiers = classification.get("key_identifiers", {})
        db.commit()
    
    return classification
