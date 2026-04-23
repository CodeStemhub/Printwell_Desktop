"""
Validator - Quality control for extracted data.

WHAT IT IS: The quality control and intelligence engine.
WHY IT EXISTS: Extracted data may be incomplete, incorrect, or inconsistent.
               This is the CORE VALUE ENGINE that moves from document-level 
               to workflow-level intelligence.
WHAT IT DOES:
    - Checks required fields are present
    - Validates calculations (e.g., VAT math)
    - Cross-references related documents
    - Detects historical anomalies (vs past filings)
    - Flags compliance timeline issues (missed deadlines)
    - Provides threshold alerts (unusual values)
    - Creates audit trail with traceability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import statistics

from models import Document, Flag
from config import settings


# Required fields for each document type
REQUIRED_FIELDS = {
    "GRA_VAT_RETURN": ["taxpayer_name", "tin_number", "tax_period", "output_vat", "input_vat", "net_vat_payable"],
    "SSNIT_CONTRIBUTION": ["employer_name", "ssnit_employer_number", "contribution_month", "total_contribution_amount"],
    "SUPPLIER_INVOICE": ["supplier_name", "invoice_number", "invoice_date", "total_amount"],
    "PAYROLL_SHEET": ["company_name", "payroll_period", "employee_records"],
    "BANK_STATEMENT": ["account_name", "account_number", "bank_name", "opening_balance", "closing_balance"],
    "PURCHASE_ORDER": ["po_number", "po_date", "buyer_name", "supplier_name", "total_amount"],
    "TAX_CLEARANCE": ["taxpayer_name", "tin_number", "clearance_number", "issue_date", "expiry_date"]
}

# Ghana tax compliance deadlines
COMPLIANCE_DEADLINES = {
    "GRA_VAT_RETURN": {"day": 21, "frequency": "monthly"},  # Due 21st of following month
    "GRA_PAYE": {"day": 15, "frequency": "monthly"},  # Due 15th of following month
    "SSNIT_CONTRIBUTION": {"day": 10, "frequency": "monthly"}  # Due 10th of following month
}


def validate_document(
    extracted_data: Dict[str, Any],
    document_type: str,
    document_id: str,
    db: Session,
    user_id: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Validate extracted data and create flags for issues.
    
    Enhanced to include:
    - Historical anomaly detection
    - Compliance deadline tracking
    - Threshold alerts
    - Full audit trail
    
    Args:
        extracted_data: The extracted data dictionary (includes _extraction_audit)
        document_type: The classified document type
        document_id: ID of the document
        db: Database session
        user_id: User ID for historical lookups
        metadata: Additional context (classification confidence, etc.)
        
    Returns:
        List of flag dictionaries with full traceability
    """
    flags = []
    
    # STEP 1: Check extraction confidence from audit trail
    audit_trail = extracted_data.get("_extraction_audit", {})
    if audit_trail:
        confidence = audit_trail.get("confidence", 1.0)
        if confidence < 0.85:
            flags.append({
                "type": "low_confidence_extraction",
                "field": "multiple",
                "message": f"Data extraction confidence is low ({confidence:.0%}). Manual review recommended.",
                "severity": "medium",
                "metadata": {
                    "confidence_score": confidence,
                    "extraction_method": audit_trail.get("method"),
                    "fields_by_method": audit_trail.get("fields_by_method", {})
                }
            })
    
    # STEP 2: Check required fields
    required = REQUIRED_FIELDS.get(document_type, [])
    for field in required:
        if field not in extracted_data or extracted_data[field] is None:
            flags.append({
                "type": "missing_field",
                "field": field,
                "message": f"Required field '{field}' is missing",
                "severity": "high",
                "metadata": {
                    "extraction_method": audit_trail.get("fields_by_method", {}).get(field, "unknown")
                }
            })
    
    # STEP 3: Type-specific validation rules
    if document_type == "GRA_VAT_RETURN":
        flags.extend(validate_vat_return(extracted_data, document_id, db, user_id))
    
    elif document_type == "SUPPLIER_INVOICE":
        flags.extend(validate_invoice(extracted_data))
    
    elif document_type == "BANK_STATEMENT":
        flags.extend(validate_bank_statement(extracted_data))
    
    elif document_type == "PAYROLL_SHEET":
        flags.extend(validate_payroll(extracted_data))
    
    # STEP 4: Historical anomaly detection and deadline tracking (if user_id provided)
    if user_id:
        flags.extend(detect_anomalies(document_type, extracted_data, user_id, db))
        flags.extend(check_compliance_deadlines(document_type, extracted_data, user_id, db))
    
    # Save flags to database with full metadata
    for flag_data in flags:
        flag = Flag(
            document_id=document_id,
            flag_type=flag_data["type"],
            field_name=flag_data.get("field"),
            message=flag_data["message"],
            severity=flag_data.get("severity", "medium"),
            metadata=flag_data.get("metadata", {})
        )
        db.add(flag)
    
    # Update document validation status
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        document.flags = flags
        document.validation_status = determine_validation_status(flags)
        db.commit()
    
    return flags


def determine_validation_status(flags: List[Dict]) -> str:
    """Determine overall validation status based on flags."""
    if not flags:
        return "valid"
    
    severities = [f.get("severity", "medium") for f in flags]
    
    if "critical" in severities:
        return "critical_issues"
    elif "high" in severities:
        return "has_flags"
    elif "medium" in severities:
        return "needs_review"
    else:
        return "minor_issues"


def validate_vat_return(
    data: Dict[str, Any],
    document_id: str,
    db: Session,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Validate VAT return calculations with historical comparison."""
    flags = []
    
    # Basic calculation validation
    try:
        output_vat = float(data.get("output_vat") or 0)
        input_vat = float(data.get("input_vat") or 0)
        net_vat = float(data.get("net_vat_payable") or 0)
        
        expected_net = output_vat - input_vat
        
        # Allow small rounding differences
        if abs(expected_net - net_vat) > 1.0:
            flags.append({
                "type": "calculation_error",
                "field": "net_vat_payable",
                "message": f"VAT calculation does not balance. Expected: {expected_net:.2f}, Got: {net_vat:.2f}",
                "severity": "critical",
                "metadata": {
                    "expected_value": expected_net,
                    "actual_value": net_vat,
                    "variance": abs(expected_net - net_vat)
                }
            })
    except (TypeError, ValueError):
        pass
    
    # ENHANCED HISTORICAL ANOMALY DETECTION (Z-score based, seasonal-aware)
    if user_id:
        historical_flags = detect_anomalies("GRA_VAT_RETURN", data, user_id, db)
        flags.extend(historical_flags)
    
    # THRESHOLD ALERTS - Unusually high input VAT
    try:
        output_vat = float(data.get("output_vat") or 0)
        input_vat = float(data.get("input_vat") or 0)
        
        if output_vat > 0 and input_vat > output_vat * 0.9:
            flags.append({
                "type": "threshold_alert",
                "field": "input_vat",
                "message": "Input VAT is unusually high relative to output VAT (>90%). Review for accuracy or potential fraud indicator.",
                "severity": "medium",
                "user_message": "⚠ Review needed: High input VAT ratio",
                "metadata": {
                    "output_vat": output_vat,
                    "input_vat": input_vat,
                    "ratio": input_vat / output_vat if output_vat > 0 else None,
                    "threshold": 0.9
                },
                "audit_trail": {
                    "detection_method": "threshold_check",
                    "confidence": 0.95
                }
            })
    except (TypeError, ValueError):
        pass
    
    return flags


def check_historical_vat_anomalies(
    data: Dict[str, Any],
    user_id: str,
    current_doc_id: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Compare current VAT return against historical filings.
    Detects unusual patterns that might indicate errors or fraud.
    """
    flags = []
    
    try:
        # Get last 6 months of VAT returns for this user
        from models import Document
        historical_docs = db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.classified_type == "GRA_VAT_RETURN",
                Document.id != current_doc_id,
                Document.status == "validated"
            )
        ).order_by(Document.created_at.desc()).limit(6).all()
        
        if len(historical_docs) < 3:
            return flags  # Not enough history
        
        # Calculate historical averages
        output_vats = []
        input_vats = []
        net_vats = []
        
        for doc in historical_docs:
            ext_data = doc.extracted_data or {}
            if ext_data.get("output_vat"):
                output_vats.append(float(ext_data["output_vat"]))
            if ext_data.get("input_vat"):
                input_vats.append(float(ext_data["input_vat"]))
            if ext_data.get("net_vat_payable"):
                net_vats.append(float(ext_data["net_vat_payable"]))
        
        if not all([output_vats, input_vats, net_vats]):
            return flags
        
        avg_output = sum(output_vats) / len(output_vats)
        avg_input = sum(input_vats) / len(input_vats)
        avg_net = sum(net_vats) / len(net_vats)
        
        # Check current values against historical averages
        current_output = float(data.get("output_vat") or 0)
        current_input = float(data.get("input_vat") or 0)
        current_net = float(data.get("net_vat_payable") or 0)
        
        # Alert if >50% deviation from average
        if avg_output > 0:
            output_deviation = abs(current_output - avg_output) / avg_output
            if output_deviation > 0.5:
                flags.append({
                    "type": "historical_anomaly",
                    "field": "output_vat",
                    "message": f"Output VAT deviates {output_deviation:.0%} from 6-month average ({avg_output:,.2f}). Verify this is correct.",
                    "severity": "medium",
                    "metadata": {
                        "current_value": current_output,
                        "historical_average": avg_output,
                        "deviation_percentage": output_deviation,
                        "months_compared": len(output_vats)
                    }
                })
        
        if avg_input > 0:
            input_deviation = abs(current_input - avg_input) / avg_input
            if input_deviation > 0.5:
                flags.append({
                    "type": "historical_anomaly",
                    "field": "input_vat",
                    "message": f"Input VAT deviates {input_deviation:.0%} from 6-month average ({avg_input:,.2f}). Verify this is correct.",
                    "severity": "medium",
                    "metadata": {
                        "current_value": current_input,
                        "historical_average": avg_input,
                        "deviation_percentage": input_deviation,
                        "months_compared": len(input_vats)
                    }
                })
    
    except Exception as e:
        # Don't fail validation if historical check fails
        pass
    
    return flags


def check_compliance_deadline(
    data: Dict[str, Any],
    document_type: str,
    user_id: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Check if document was filed/submitted by compliance deadline.
    Alerts for missed deadlines and potential penalties.
    """
    flags = []
    
    deadline_info = COMPLIANCE_DEADLINES.get(document_type)
    if not deadline_info:
        return flags
    
    # Extract period from data
    tax_period = data.get("tax_period") or data.get("contribution_month")
    if not tax_period:
        return flags
    
    try:
        # Parse period (simplified - production would use dateutil)
        # Assume format like "Q1 2025" or "January 2025"
        period_year = int(tax_period.split()[-1])
        
        # Calculate deadline date
        deadline_day = deadline_info["day"]
        
        # For monthly filings, deadline is day X of following month
        # Simplified logic here
        from datetime import date
        current_date = date.today()
        
        # Check if we're past the deadline
        # (Production would calculate exact deadline based on period)
        days_overdue = (current_date - date(period_year, 1, 1)).days
        
        if days_overdue > 30:  # Simplified check
            flags.append({
                "type": "compliance_deadline",
                "field": "filing_date",
                "message": f"This {document_type.replace('_', ' ').title()} may be overdue. Verify filing date to avoid penalties.",
                "severity": "high",
                "metadata": {
                    "document_type": document_type,
                    "period": tax_period,
                    "deadline_day": deadline_day,
                    "potential_penalty": "Contact GRA/SSNIT for penalty calculation"
                }
            })
    
    except Exception:
        pass
    
    return flags


def validate_invoice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate invoice data."""
    flags = []
    
    try:
        subtotal = float(data.get("subtotal") or 0)
        vat_amount = float(data.get("vat_amount") or 0)
        total = float(data.get("total_amount") or 0)
        
        # Standard Ghana VAT rate is 12.5%
        expected_vat = subtotal * 0.125
        expected_total = subtotal + vat_amount
        
        # Check VAT calculation
        if abs(expected_vat - vat_amount) > 1.0:
            flags.append({
                "type": "calculation_error",
                "field": "vat_amount",
                "message": f"VAT amount appears incorrect. Expected ~{expected_vat:.2f} (12.5%), Got: {vat_amount:.2f}",
                "severity": "high",
                "metadata": {
                    "expected_vat": expected_vat,
                    "actual_vat": vat_amount,
                    "variance": abs(expected_vat - vat_amount),
                    "implied_rate": (vat_amount / subtotal * 100) if subtotal > 0 else None
                }
            })
        
        # Check total calculation
        if abs(expected_total - total) > 1.0:
            flags.append({
                "type": "calculation_error",
                "field": "total_amount",
                "message": f"Total does not match subtotal + VAT. Expected: {expected_total:.2f}, Got: {total:.2f}",
                "severity": "critical",
                "metadata": {
                    "expected_total": expected_total,
                    "actual_total": total,
                    "variance": abs(expected_total - total)
                }
            })
    except (TypeError, ValueError):
        pass
    
    return flags


def validate_bank_statement(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate bank statement data."""
    flags = []
    
    # Check that closing balance makes sense
    try:
        opening = float(data.get("opening_balance") or 0)
        closing = float(data.get("closing_balance") or 0)
        transactions = data.get("transactions", [])
        
        if transactions:
            # Calculate expected closing balance
            total_debits = sum(float(t.get("debit", 0) or 0) for t in transactions)
            total_credits = sum(float(t.get("credit", 0) or 0) for t in transactions)
            
            expected_closing = opening - total_debits + total_credits
            
            if abs(expected_closing - closing) > 1.0:
                flags.append({
                    "type": "reconciliation_error",
                    "field": "closing_balance",
                    "message": f"Statement does not reconcile. Expected: {expected_closing:.2f}, Got: {closing:.2f}",
                    "severity": "high",
                    "metadata": {
                        "opening_balance": opening,
                        "total_debits": total_debits,
                        "total_credits": total_credits,
                        "expected_closing": expected_closing,
                        "actual_closing": closing,
                        "variance": abs(expected_closing - closing)
                    }
                })
    except (TypeError, ValueError):
        pass
    
    return flags


def validate_payroll(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate payroll sheet data."""
    flags = []
    
    try:
        employee_records = data.get("employee_records", [])
        
        if not employee_records:
            flags.append({
                "type": "missing_data",
                "field": "employee_records",
                "message": "No employee records found in payroll",
                "severity": "critical",
                "metadata": {
                    "employee_count": 0
                }
            })
            return flags
        
        # Verify totals match sum of individual records
        total_gross = sum(float(e.get("gross_salary", 0) or 0) for e in employee_records)
        total_net = sum(float(e.get("net_salary", 0) or 0) for e in employee_records)
        
        reported_gross = float(data.get("total_gross_salary") or 0)
        reported_net = float(data.get("total_net_salary") or 0)
        
        if abs(total_gross - reported_gross) > 1.0:
            flags.append({
                "type": "calculation_error",
                "field": "total_gross_salary",
                "message": f"Gross salary total mismatch. Calculated: {total_gross:.2f}, Reported: {reported_gross:.2f}",
                "severity": "high",
                "metadata": {
                    "calculated_total": total_gross,
                    "reported_total": reported_gross,
                    "variance": abs(total_gross - reported_gross),
                    "employee_count": len(employee_records)
                }
            })
        
        if abs(total_net - reported_net) > 1.0:
            flags.append({
                "type": "calculation_error",
                "field": "total_net_salary",
                "message": f"Net salary total mismatch. Calculated: {total_net:.2f}, Reported: {reported_net:.2f}",
                "severity": "high",
                "metadata": {
                    "calculated_total": total_net,
                    "reported_total": reported_net,
                    "variance": abs(total_net - reported_net),
                    "employee_count": len(employee_records)
                }
            })
    except (TypeError, ValueError):
        pass
    
    return flags


def detect_anomalies(document_type: str, extracted_data: dict, user_id: str, db: Session) -> list:
    """
    WHAT IT IS: Intelligent anomaly detection that learns business patterns.
    WHY IT EXISTS: Fixed thresholds cause false positives for seasonal businesses.
                   We need context-aware detection that adapts to each client.
    WHAT IT DOES:
        1. Retrieves historical data for this user/document type
        2. Calculates rolling averages and standard deviations
        3. Detects outliers using Z-score (configurable threshold)
        4. Flags seasonal patterns vs genuine anomalies
        5. Allows user feedback to refine future detection
    """
    flags = []
    
    if document_type != "GRA_VAT_RETURN":
        return flags
    
    # Get historical VAT returns (last 12 months)
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    history = db.query(Document).filter(
        and_(
            Document.user_id == user_id,
            Document.classified_type == "GRA_VAT_RETURN",
            Document.created_at >= twelve_months_ago,
            Document.status == "complete"
        )
    ).order_by(Document.created_at.desc()).limit(12).all()
    
    if len(history) < 3:
        return flags  # Not enough data for pattern detection
    
    current_output_vat = extracted_data.get("output_vat")
    current_input_vat = extracted_data.get("input_vat")
    
    if not current_output_vat or not current_input_vat:
        return flags
    
    # Calculate historical metrics
    output_vat_values = [doc.extracted_data.get("output_vat", 0) for doc in history if doc.extracted_data and doc.extracted_data.get("output_vat")]
    input_vat_values = [doc.extracted_data.get("input_vat", 0) for doc in history if doc.extracted_data and doc.extracted_data.get("input_vat")]
    
    if not output_vat_values or not input_vat_values:
        return flags
    
    # Statistical analysis with Z-score
    output_mean = statistics.mean(output_vat_values)
    output_std = statistics.stdev(output_vat_values) if len(output_vat_values) > 1 else 0
    input_mean = statistics.mean(input_vat_values)
    input_std = statistics.stdev(input_vat_values) if len(input_vat_values) > 1 else 0
    
    # Dynamic threshold: 2.5 standard deviations (adjustable based on user feedback)
    z_threshold = 2.5
    
    # Check output VAT anomaly
    if output_std > 0:
        output_z_score = abs(current_output_vat - output_mean) / output_std
        if output_z_score > z_threshold:
            variance_pct = ((current_output_vat - output_mean) / output_mean * 100) if output_mean != 0 else 0
            is_seasonal = detect_seasonal_pattern(user_id, "output_vat", history, db)
            
            flags.append({
                "type": "anomaly_detected",
                "field": "output_vat",
                "severity": "medium" if output_z_score < 3.0 else "high",
                "message": f"Output VAT is {variance_pct:+.1f}% from 12-month average",
                "user_message": "⚠ Needs review" if not is_seasonal else "ℹ️ Seasonal pattern detected",
                "details": {
                    "current_value": current_output_vat,
                    "historical_average": round(output_mean, 2),
                    "standard_deviations": round(output_z_score, 2),
                    "data_points": len(output_vat_values),
                    "is_seasonal_pattern": is_seasonal,
                    "user_feedback_status": "pending"
                },
                "audit_trail": {
                    "detection_method": "statistical_z_score",
                    "threshold_used": z_threshold,
                    "confidence": 0.85 if output_z_score < 3.0 else 0.95
                }
            })
    
    # Check input VAT anomaly
    if input_std > 0:
        input_z_score = abs(current_input_vat - input_mean) / input_std
        if input_z_score > z_threshold:
            variance_pct = ((current_input_vat - input_mean) / input_mean * 100) if input_mean != 0 else 0
            is_seasonal = detect_seasonal_pattern(user_id, "input_vat", history, db)
            
            flags.append({
                "type": "anomaly_detected",
                "field": "input_vat",
                "severity": "medium" if input_z_score < 3.0 else "high",
                "message": f"Input VAT is {variance_pct:+.1f}% from 12-month average",
                "user_message": "⚠ Needs review" if not is_seasonal else "ℹ️ Seasonal pattern detected",
                "details": {
                    "current_value": current_input_vat,
                    "historical_average": round(input_mean, 2),
                    "standard_deviations": round(input_z_score, 2),
                    "data_points": len(input_vat_values),
                    "is_seasonal_pattern": is_seasonal,
                    "user_feedback_status": "pending"
                },
                "audit_trail": {
                    "detection_method": "statistical_z_score",
                    "threshold_used": z_threshold,
                    "confidence": 0.85 if input_z_score < 3.0 else 0.95
                }
            })
    
    # Ratio analysis: Input VAT vs Output VAT
    if current_output_vat > 0:
        current_ratio = current_input_vat / current_output_vat
        historical_ratios = []
        for doc in history:
            if doc.extracted_data:
                out_vat = doc.extracted_data.get("output_vat", 0)
                in_vat = doc.extracted_data.get("input_vat", 0)
                if out_vat > 0:
                    historical_ratios.append(in_vat / out_vat)
        
        if len(historical_ratios) >= 3:
            ratio_mean = statistics.mean(historical_ratios)
            ratio_std = statistics.stdev(historical_ratios) if len(historical_ratios) > 1 else 0
            
            if ratio_std > 0:
                ratio_z_score = abs(current_ratio - ratio_mean) / ratio_std
                if ratio_z_score > z_threshold:
                    flags.append({
                        "type": "ratio_anomaly",
                        "field": "vat_ratio",
                        "severity": "high",
                        "message": f"Input/Output VAT ratio ({current_ratio:.2f}) deviates significantly from normal ({ratio_mean:.2f})",
                        "user_message": "⚠ High priority review needed",
                        "details": {
                            "current_ratio": round(current_ratio, 3),
                            "historical_average_ratio": round(ratio_mean, 3),
                            "standard_deviations": round(ratio_z_score, 2),
                            "typical_range": f"{round(ratio_mean - 2*ratio_std, 3)} - {round(ratio_mean + 2*ratio_std, 3)}"
                        },
                        "audit_trail": {
                            "detection_method": "ratio_analysis",
                            "confidence": 0.90
                        }
                    })
    
    return flags


def detect_seasonal_pattern(user_id: str, field: str, history: list, db: Session) -> bool:
    """
    WHAT IT IS: Detects if current value fits a seasonal pattern.
    WHY IT EXISTS: Some businesses have predictable spikes (e.g., retail in December).
    """
    current_month = datetime.now().month
    
    monthly_values = {}
    for doc in history:
        doc_month = doc.created_at.month
        value = doc.extracted_data.get(field, 0) if doc.extracted_data else 0
        if doc_month not in monthly_values:
            monthly_values[doc_month] = []
        monthly_values[doc_month].append(value)
    
    if current_month not in monthly_values or len(monthly_values[current_month]) < 2:
        return False
    
    # Check if current month typically has higher variance
    current_month_std = statistics.stdev(monthly_values[current_month])
    all_values = [v for values in monthly_values.values() for v in values]
    overall_std = statistics.stdev(all_values) if len(all_values) > 1 else 0
    
    return current_month_std > (overall_std * 1.5) if overall_std > 0 else False


def check_compliance_deadlines(document_type: str, extracted_data: dict, user_id: str, db: Session) -> list:
    """
    WHAT IT IS: Proactive deadline tracking for Ghana Revenue Authority and SSNIT.
    WHY IT EXISTS: Missing deadlines results in penalties. This prevents costly mistakes.
    WHAT IT DOES:
        1. Checks filing deadlines for document type
        2. Compares against today's date
        3. Warns about upcoming or overdue filings
    """
    flags = []
    
    if document_type not in COMPLIANCE_DEADLINES:
        return flags
    
    deadline_info = COMPLIANCE_DEADLINES[document_type]
    period = extracted_data.get("tax_period") or extracted_data.get("contribution_month")
    
    if not period:
        return flags
    
    # Parse period (e.g., "Q1 2025" or "January 2025")
    try:
        # Simplified parsing - enhance for production
        if "Q" in period:
            # Quarter format: Q1 2025
            quarter = int(period.split("Q")[1].split()[0])
            year = int(period.split()[-1])
            # VAT due 21st of month after quarter ends
            due_month = quarter * 3 + 1
            due_date = datetime(year, due_month, deadline_info["day"])
        else:
            # Month format: January 2025
            from datetime import datetime
            period_date = datetime.strptime(f"01 {period}", "%d %B %Y")
            if deadline_info["frequency"] == "monthly":
                due_month = period_date.month + 1
                due_year = period_date.year
                if due_month > 12:
                    due_month = 1
                    due_year += 1
                due_date = datetime(due_year, due_month, deadline_info["day"])
            else:
                due_date = period_date
        
        days_until_due = (due_date - datetime.utcnow()).days
        
        if days_until_due < 0:
            flags.append({
                "type": "deadline_missed",
                "field": "filing_date",
                "severity": "critical",
                "message": f"Filing is {abs(days_until_due)} days OVERDUE (was due {due_date.strftime('%d %B %Y')})",
                "user_message": "🚨 Urgent: File immediately to avoid penalties",
                "details": {
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "days_overdue": abs(days_until_due),
                    "penalty_risk": "high"
                },
                "audit_trail": {
                    "detection_method": "deadline_check",
                    "confidence": 1.0
                }
            })
        elif days_until_due <= 3:
            flags.append({
                "type": "deadline_approaching",
                "field": "filing_date",
                "severity": "high",
                "message": f"Filing due in {days_until_due} days ({due_date.strftime('%d %B %Y')})",
                "user_message": "⏰ Due soon: Complete filing within 3 days",
                "details": {
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "days_remaining": days_until_due,
                    "recommended_action": "File within 48 hours"
                },
                "audit_trail": {
                    "detection_method": "deadline_check",
                    "confidence": 1.0
                }
            })
    except (ValueError, IndexError):
        pass  # Could not parse period, skip deadline check
    
    return flags
