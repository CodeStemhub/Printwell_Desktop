"""
Export Service - Handles document data export in various formats.

WHAT IT IS: Exports extracted data to Excel, CSV, JSON, or accounting software formats.
WHY IT EXISTS: Accountants need to move data into other systems or share with clients.
WHAT IT DOES:
    - Exports to Excel with proper formatting
    - Generates CSV for import into other systems
    - Creates JSON for API integrations
    - Formats for specific accounting software (Sage, QuickBooks, etc.)
"""

import io
import json
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session


async def export_to_excel(documents: List[Dict], output_type: str = "summary") -> bytes:
    """
    Export document data to Excel format.

    Args:
        documents: List of document data dictionaries
        output_type: 'summary' for overview, 'detailed' for full extraction

    Returns:
        Excel file as bytes
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    except ImportError:
        raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")

    wb = Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"

    # Headers
    headers = ["Document", "Type", "Status", "Period", "Key Amount", "Issues"]
    ws_summary.append(headers)

    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1A7F5A", end_color="1A7F5A", fill_type="solid")
    for cell in ws_summary[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Add data rows
    for doc in documents:
        key_amount = extract_key_amount(doc)
        issues_count = len(doc.get("flags", []))
        issues_text = f"{issues_count} issue{'s' if issues_count != 1 else ''}" if issues_count > 0 else "None"

        row = [
            doc.get("filename", ""),
            (doc.get("classified_type") or "Unknown").replace("_", " "),
            doc.get("validation_status", "pending"),
            doc.get("document_period", ""),
            f"GHS {key_amount:.2f}" if key_amount else "N/A",
            issues_text
        ]
        ws_summary.append(row)

    # Adjust column widths
    for col in ws_summary.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws_summary.column_dimensions[column].width = adjusted_width

    # Detailed sheets per document type
    if output_type == "detailed":
        by_type = {}
        for doc in documents:
            doc_type = doc.get("classified_type", "Unknown")
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)

        for doc_type, docs in by_type.items():
            if docs and docs[0].get("extracted_data"):
                ws_detail = wb.create_sheet(title=doc_type[:31])  # Excel limit: 31 chars
                add_detailed_sheet(ws_detail, docs, doc_type)

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return output.read()


def add_detailed_sheet(ws, documents: List[Dict], doc_type: str):
    """
    Add detailed data for a specific document type.
    """
    if not documents:
        return

    # Get all possible fields from extracted data
    all_fields = set()
    for doc in documents:
        if doc.get("extracted_data"):
            all_fields.update(doc["extracted_data"].keys())

    # Headers
    headers = ["Document", "Period"] + list(all_fields)
    ws.append(headers)

    # Style headers
    from openpyxl.styles import Font, PatternFill
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2D3B4E", end_color="2D3B4E", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Data rows
    for doc in documents:
        row = [
            doc.get("filename", ""),
            doc.get("document_period", "")
        ]
        extracted = doc.get("extracted_data", {})
        for field in all_fields:
            value = extracted.get(field, "")
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            row.append(value if value is not None else "")
        ws.append(row)


async def export_to_csv(documents: List[Dict]) -> str:
    """
    Export document summary to CSV format.

    Args:
        documents: List of document data dictionaries

    Returns:
        CSV string
    """
    import csv
    output = io.StringIO()

    writer = csv.writer(output)
    writer.writerow(["Document", "Type", "Status", "Period", "Key Amount", "Issues"])

    for doc in documents:
        key_amount = extract_key_amount(doc)
        issues_count = len(doc.get("flags", []))

        writer.writerow([
            doc.get("filename", ""),
            (doc.get("classified_type") or "Unknown").replace("_", " "),
            doc.get("validation_status", ""),
            doc.get("document_period", ""),
            f"{key_amount:.2f}" if key_amount else "",
            issues_count
        ])

    return output.getvalue()


async def export_to_json(documents: List[Dict], pretty: bool = True) -> str:
    """
    Export document data to JSON format.

    Args:
        documents: List of document data dictionaries
        pretty: Whether to format with indentation

    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(documents, indent=2, default=str)
    else:
        return json.dumps(documents, default=str)


async def export_for_accounting_software(
    documents: List[Dict],
    software: str = "generic"
) -> Dict[str, Any]:
    """
    Export data formatted for specific accounting software.

    Args:
        documents: List of document data dictionaries
        software: Target software ('quickbooks', 'sage', 'xero', 'generic')

    Returns:
        Formatted data dictionary
    """
    if software == "quickbooks":
        return format_for_quickbooks(documents)
    elif software == "sage":
        return format_for_sage(documents)
    elif software == "xero":
        return format_for_xero(documents)
    else:
        return format_for_generic(documents)


def format_for_quickbooks(documents: List[Dict]) -> Dict:
    """Format for QuickBooks import."""
    transactions = []

    for doc in documents:
        if doc.get("classified_type") == "SUPPLIER_INVOICE":
            data = doc.get("extracted_data", {})
            transactions.append({
                "VendorName": data.get("supplier_name", ""),
                "InvoiceDate": data.get("invoice_date", ""),
                "BillRef": data.get("invoice_number", ""),
                "Memo": f"Imported from ClearDesk - {doc.get('filename')}",
                "LineItems": format_line_items(data.get("line_items", []))
            })

    return {
        "format": "QuickBooks IIF",
        "version": "2023",
        "transactions": transactions
    }


def format_for_sage(documents: List[Dict]) -> Dict:
    """Format for Sage import."""
    entries = []

    for doc in documents:
        data = doc.get("extracted_data", {})
        if doc.get("classified_type") == "SUPPLIER_INVOICE":
            entries.append({
                "NOMINAL_CODE": "5000",  # Purchases
                "DATE": data.get("invoice_date", ""),
                "TYPE": "SI",
                "REF_NUMBER": data.get("invoice_number", ""),
                "DETAILS": data.get("supplier_name", ""),
                "NET": data.get("subtotal", 0),
                "TAX": data.get("vat_amount", 0),
                "GROSS": data.get("total_amount", 0)
            })

    return {
        "format": "Sage Import",
        "entries": entries
    }


def format_for_xero(documents: List[Dict]) -> Dict:
    """Format for Xero CSV import."""
    bills = []

    for doc in documents:
        if doc.get("classified_type") == "SUPPLIER_INVOICE":
            data = doc.get("extracted_data", {})
            bills.append({
                "ContactName": data.get("supplier_name", ""),
                "InvoiceDate": data.get("invoice_date", ""),
                "DueDate": "",  # Would need to calculate
                "InvoiceNumber": data.get("invoice_number", ""),
                "Description": f"Supplier Invoice - {doc.get('filename')}",
                "TotalAmount": data.get("total_amount", 0),
                "TaxAmount": data.get("vat_amount", 0)
            })

    return {
        "format": "Xero Bills CSV",
        "bills": bills
    }


def format_for_generic(documents: List[Dict]) -> Dict:
    """Generic format suitable for most systems."""
    return {
        "exported_at": datetime.now().isoformat(),
        "document_count": len(documents),
        "documents": documents
    }


def extract_key_amount(doc: Dict) -> float:
    """Extract the primary monetary amount from a document."""
    extracted = doc.get("extracted_data", {})

    # Map document types to their key amount field
    amount_map = {
        "GRA_VAT_RETURN": "net_vat_payable",
        "SSNIT_CONTRIBUTION": "total_contribution_amount",
        "SUPPLIER_INVOICE": "total_amount",
        "PURCHASE_ORDER": "total_amount",
        "PAYROLL_SHEET": "total_net_salary",
        "BANK_STATEMENT": "closing_balance"
    }

    doc_type = doc.get("classified_type")
    field = amount_map.get(doc_type)

    if field and field in extracted:
        try:
            return float(extracted[field])
        except (TypeError, ValueError):
            return 0.0

    return 0.0


def format_line_items(line_items: List[Dict]) -> List[Dict]:
    """Format line items for accounting software."""
    formatted = []
    for item in line_items:
        formatted.append({
            "Description": item.get("description", ""),
            "Quantity": item.get("quantity", 1),
            "UnitPrice": item.get("unit_price", 0),
            "Amount": item.get("total", 0)
        })
    return formatted
