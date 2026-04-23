"""
Report Builder - Generates comprehensive compliance reports.

WHAT IT IS: Creates summary reports of all processed documents and their status.
WHY IT EXISTS: Accountants need overview reports for clients, management, or audits.
WHAT IT DOES:
    - Summarizes all documents in a session
    - Lists all flagged issues by severity
    - Provides action items and recommendations
    - Exports to PDF or structured JSON
"""

from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from models import Document, Flag


async def build_session_report(
    session_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Build a comprehensive report for a chat session.

    Args:
        session_id: The session to report on
        db: Database session

    Returns:
        Complete report dictionary
    """
    # Get all documents in session
    documents = db.query(Document).filter(
        Document.session_id == session_id
    ).all()

    # Categorize by status
    valid_docs = [d for d in documents if d.validation_status == "valid"]
    flagged_docs = [d for d in documents if d.validation_status == "has_flags"]
    needs_review = [d for d in documents if d.validation_status == "needs_review"]
    processing = [d for d in documents if d.status == "processing"]

    # Get all flags
    all_flags = []
    for doc in documents:
        if doc.flags:
            all_flags.extend(doc.flags)

    # Categorize flags by severity
    critical_flags = [f for f in all_flags if f.get("severity") == "critical"]
    high_flags = [f for f in all_flags if f.get("severity") == "high"]
    medium_flags = [f for f in all_flags if f.get("severity") == "medium"]
    low_flags = [f for f in all_flags if f.get("severity") == "low"]

    # Build document summaries
    document_summaries = []
    for doc in documents:
        summary = {
            "id": doc.id,
            "filename": doc.filename,
            "type": doc.classified_type,
            "status": doc.status,
            "validation_status": doc.validation_status,
            "confidence": doc.classification_confidence,
            "flags_count": len(doc.flags) if doc.flags else 0,
            "key_data": extract_key_data(doc)
        }
        document_summaries.append(summary)

    # Generate action items
    action_items = generate_action_items(documents, all_flags)

    report = {
        "report_id": f"rpt_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
        "session_id": session_id,
        "summary": {
            "total_documents": len(documents),
            "valid": len(valid_docs),
            "flagged": len(flagged_docs),
            "needs_review": len(needs_review),
            "processing": len(processing)
        },
        "flags_summary": {
            "total": len(all_flags),
            "critical": len(critical_flags),
            "high": len(high_flags),
            "medium": len(medium_flags),
            "low": len(low_flags)
        },
        "documents": document_summaries,
        "action_items": action_items,
        "recommendations": generate_recommendations(documents, all_flags)
    }

    return report


def extract_key_data(document: Document) -> Dict[str, Any]:
    """
    Extract key identifying data from a document based on its type.
    """
    if not document.extracted_data:
        return {}

    data = document.extracted_data

    if document.classified_type == "GRA_VAT_RETURN":
        return {
            "tax_period": data.get("tax_period"),
            "tin": data.get("tin_number"),
            "output_vat": data.get("output_vat"),
            "input_vat": data.get("input_vat"),
            "net_vat": data.get("net_vat_payable")
        }

    elif document.classified_type == "SSNIT_CONTRIBUTION":
        return {
            "period": data.get("contribution_month"),
            "employer": data.get("employer_name"),
            "employee_count": data.get("employee_count"),
            "total_amount": data.get("total_contribution_amount")
        }

    elif document.classified_type == "SUPPLIER_INVOICE":
        return {
            "invoice_number": data.get("invoice_number"),
            "date": data.get("invoice_date"),
            "supplier": data.get("supplier_name"),
            "total": data.get("total_amount")
        }

    elif document.classified_type == "BANK_STATEMENT":
        return {
            "bank": data.get("bank_name"),
            "account": data.get("account_number"),
            "period": data.get("statement_period"),
            "closing_balance": data.get("closing_balance")
        }

    return {"data_available": bool(data)}


def generate_action_items(
    documents: List[Document],
    flags: List[Dict]
) -> List[Dict[str, str]]:
    """
    Generate prioritized action items based on document status and flags.
    """
    actions = []

    # Critical flags first
    critical_docs = set()
    for flag in flags:
        if flag.get("severity") == "critical":
            critical_docs.add(flag.get("field_name", "Unknown"))

    for doc in documents:
        if doc.validation_status == "has_flags":
            for flag in (doc.flags or []):
                priority = "HIGH" if flag.get("severity") in ["critical", "high"] else "MEDIUM"
                actions.append({
                    "priority": priority,
                    "document": doc.filename,
                    "issue": flag.get("message"),
                    "action": get_suggested_action(flag, doc)
                })

        elif doc.status == "processing":
            actions.append({
                "priority": "LOW",
                "document": doc.filename,
                "issue": "Document still processing",
                "action": "Wait for processing to complete"
            })

    # Sort by priority
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    actions.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return actions


def get_suggested_action(flag: Dict, document: Document) -> str:
    """
    Suggest specific action based on flag type.
    """
    flag_type = flag.get("type")

    if flag_type == "calculation_error":
        return "Review calculations and correct the figures. Request amended document from issuer if necessary."

    elif flag_type == "missing_field":
        return "Obtain missing information from the document issuer or source."

    elif flag_type == "anomaly_detected":
        return "Investigate the anomaly. Verify with supporting documentation."

    elif flag_type == "reconciliation_error":
        return "Reconcile transactions and identify discrepancies. Check for missing entries."

    elif flag_type == "low_confidence":
        return "Manual review recommended due to low OCR confidence. Verify extracted data."

    else:
        return "Review and resolve the identified issue."


def generate_recommendations(
    documents: List[Document],
    flags: List[Dict]
) -> List[str]:
    """
    Generate high-level recommendations based on overall document health.
    """
    recommendations = []

    total_docs = len(documents)
    flagged_count = sum(1 for d in documents if d.validation_status in ["has_flags", "needs_review"])

    if total_docs > 0:
        flag_rate = flagged_count / total_docs

        if flag_rate > 0.5:
            recommendations.append(
                "High error rate detected (>50%). Consider implementing pre-submission quality checks with document providers."
            )
        elif flag_rate > 0.25:
            recommendations.append(
                "Moderate error rate. Review common issues and provide feedback to frequent document sources."
            )

    # Check for specific patterns
    vat_issues = sum(1 for f in flags if "VAT" in f.get("message", ""))
    if vat_issues >= 2:
        recommendations.append(
            "Multiple VAT calculation errors found. Consider implementing automated VAT validation before filing."
        )

    missing_fields = sum(1 for f in flags if f.get("type") == "missing_field")
    if missing_fields >= 3:
        recommendations.append(
            "Several documents have missing fields. Create a checklist for required information when requesting documents."
        )

    if not recommendations:
        recommendations.append(
            "Overall document quality is good. Continue current verification processes."
        )

    return recommendations


async def export_report_json(report: Dict[str, Any]) -> str:
    """
    Export report as formatted JSON string.
    """
    import json
    return json.dumps(report, indent=2, default=str)


async def export_report_pdf(report: Dict[str, Any]) -> bytes:
    """
    Export report as PDF (placeholder - would use a library like reportlab or weasyprint).
    """
    # TODO: Implement PDF generation
    # This would create a professional PDF report with:
    # - Company branding
    # - Executive summary
    # - Document tables
    # - Flag details
    # - Action items
    raise NotImplementedError("PDF export not yet implemented")
