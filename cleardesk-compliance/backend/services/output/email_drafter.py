"""
Email Drafter - Creates professional email drafts based on document issues.

WHAT IT IS: Generates ready-to-send emails for common compliance scenarios.
WHY IT EXISTS: Accountants need to communicate issues to clients or authorities quickly.
WHAT IT DOES:
    - Drafts correction emails for flagged documents
    - Creates follow-up messages for missing information
    - Generates professional correspondence templates
"""

from typing import Dict, Any, List
from config import settings


EMAIL_TEMPLATES = {
    "vat_correction": """
Subject: Correction Required - GRA VAT Return {tax_period}

Dear {recipient_name},

I hope this email finds you well.

While reviewing your VAT return for {tax_period}, I identified a calculation discrepancy that requires attention:

{issue_description}

Current figures:
- Output VAT: GHS {output_vat:.2f}
- Input VAT: GHS {input_vat:.2f}
- Net VAT Payable (stated): GHS {stated_net:.2f}
- Net VAT Payable (calculated): GHS {calculated_net:.2f}

Please review the attached documents and provide clarification or corrected figures at your earliest convenience. The filing deadline is {due_date}, so prompt attention would be appreciated.

Should you have any questions, please don't hesitate to contact me.

Best regards,
{sender_name}
{sender_organization}
""",

    "missing_information": """
Subject: Additional Information Required - {document_type}

Dear {recipient_name},

I hope you're doing well.

While processing your {document_type}, I noticed some missing information that we need to complete the filing:

{missing_items_list}

Could you please provide the above details by {deadline}? This will ensure we meet the compliance deadline without any penalties.

If you have any questions or need clarification, please let me know.

Thank you for your prompt attention to this matter.

Best regards,
{sender_name}
{sender_organization}
""",

    "invoice_discrepancy": """
Subject: Query Regarding Invoice {invoice_number}

Dear {supplier_name},

I hope this email finds you well.

We are currently processing invoice {invoice_number} dated {invoice_date} for the amount of GHS {total_amount:.2f}.

During our review, we noted the following discrepancy:

{discrepancy_description}

Could you please clarify this matter or provide a corrected invoice if necessary?

We value our business relationship and appreciate your prompt response.

Best regards,
{sender_name}
{sender_organization}
""",

    "ssnit_follow_up": """
Subject: SSNIT Contribution Follow-Up - {contribution_month}

Dear {recipient_name},

I hope you're well.

This is a friendly reminder regarding the SSNIT contribution for {contribution_month}.

Current status:
- Number of employees listed: {employee_count}
- Total contribution amount: GHS {total_amount:.2f}
- Payment deadline: {due_date}

{action_required}

Please confirm that all employee details are accurate and that the payment will be made before the deadline to avoid penalties.

If you need any assistance with this, please don't hesitate to reach out.

Best regards,
{sender_name}
{sender_organization}
"""
}


async def draft_email(
    template_type: str,
    context: Dict[str, Any],
    sender_info: Dict[str, str]
) -> str:
    """
    Generate a professional email draft.

    Args:
        template_type: Type of email template to use
        context: Context-specific data for the email
        sender_info: Information about the sender (name, organization)

    Returns:
        Formatted email text
    """
    template = EMAIL_TEMPLATES.get(template_type)

    if not template:
        return "Template not found"

    # Merge sender info into context
    full_context = {
        **context,
        "sender_name": sender_info.get("name", ""),
        "sender_organization": sender_info.get("organization", "")
    }

    # Format the template
    email_draft = template.format(**full_context)

    return email_draft.strip()


async def generate_custom_email(
    document_type: str,
    issues: List[Dict[str, Any]],
    recipient_name: str,
    sender_info: Dict[str, str]
) -> str:
    """
    Generate a custom email using Groq API for complex scenarios.

    Args:
        document_type: Type of document with issues
        issues: List of flagged issues
        recipient_name: Name of email recipient
        sender_info: Sender information

    Returns:
        Custom-generated email text
    """
    import httpx
    from services.agent.prompt_library import EMAIL_DRAFT_PROMPT

    issues_str = "\n".join([f"- {issue['message']}" for issue in issues])

    prompt = EMAIL_DRAFT_PROMPT.format(
        document_type=document_type.replace("_", " "),
        issues_list=issues_str,
        recipient_name=recipient_name
    )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional business communication assistant. Write clear, polite, and effective emails."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 400
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )

        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code}")

        result = response.json()

    email_content = result["choices"][0]["message"]["content"]

    # Add signature
    signature = f"\n\nBest regards,\n{sender_info.get('name', '')}\n{sender_info.get('organization', '')}"

    return email_content.strip() + signature
