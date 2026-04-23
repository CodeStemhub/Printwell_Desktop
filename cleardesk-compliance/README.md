# ClearDesk Compliance Agent

**Module 1 of the ClearDesk Platform** - AI-powered document compliance agent for Ghanaian businesses.

## What It Does

An accountant uploads any mix of business documents (scanned, uploaded, or photographed), and the agent:
- Reads every single document automatically
- Identifies what each document is (GRA VAT Return, SSNIT Form, Invoice, Bank Statement, etc.)
- Extracts all data into structured fields
- Flags every problem (calculation errors, missing fields, anomalies)
- Walks the accountant through everything via a professional in-app chat interface
- Drafts emails and generates reports

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  ┌──────────────────┐     ┌─────────────────────────────┐   │
│  │  Document Panel  │     │     Agent Chat Interface    │   │
│  │  - Upload        │◄───►│     - Real-time WebSocket   │   │
│  │  - Status Cards  │     │     - Context-aware AI      │   │
│  │  - Flags Display │     │     - Action Recommendations│   │
│  └──────────────────┘     └─────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / WebSocket
┌───────────────────────────▼─────────────────────────────────┐
│                  BACKEND (FastAPI / Python 3.13)             │
│                                                              │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Ingestion  │  │ Intelligence│  │    Output Layer     │  │
│  │ - Upload   │  │ - Classify  │  │  - Email Drafting   │  │
│  │ - Scan     │  │ - Extract   │  │  - Report Building  │  │
│  │ - OCR      │  │ - Validate  │  │  - Export (Excel)   │  │
│  └────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agent Service (Grok API)                │   │
│  │  - Context Management  - Chat Responses  - Prompts   │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │  Supabase Storage│  │
│  │  (Main DB)   │  │  (Cache/Queue)│  │  (File Storage)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Supported Document Types

### Tax & Revenue
- GRA VAT Return
- GRA Income Tax Return
- PAYE Monthly Filing
- Withholding Tax Certificate
- Tax Clearance Certificate
- Corporate Tax Self-Assessment

### Customs
- Import/Export Declarations
- Bill of Entry
- Packing List
- Commercial Invoice

### HR & Labour
- SSNIT Contribution Forms
- Payroll Sheets
- Employment Contracts

### Finance
- Supplier Invoices
- Purchase Orders
- Bank Statements
- Expense Reports

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL
- Redis
- Grok API Key

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROK_API_KEY, DATABASE_URL, etc.

# Run database migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Variables

```env
# AI
GROK_API_KEY=your_grok_api_key
GOOGLE_VISION_API_KEY=optional_fallback_ocr_key

# Database
DATABASE_URL=postgresql://user:pass@localhost/cleardesk
REDIS_URL=redis://localhost:6379

# Storage
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET=cleardesk

# Auth
JWT_SECRET=your_secret_key
JWT_EXPIRE_HOURS=24

# Limits
MAX_FILE_SIZE_MB=50
```

## Project Structure

```
cleardesk-compliance/
├── backend/
│   ├── api/routes/          # API endpoints
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── agent.py
│   │   └── compliance.py
│   ├── services/
│   │   ├── ingestion/       # File upload, scan, OCR
│   │   ├── intelligence/    # Classification, extraction, validation
│   │   ├── agent/           # Chat handling, context, prompts
│   │   └── output/          # Email drafting, reports, exports
│   ├── models/              # SQLAlchemy models
│   ├── utils/               # Shared utilities
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   └── ComplianceDashboard.jsx
    │   ├── components/
    │   │   ├── documents/   # Document panel, cards, upload
    │   │   ├── chat/        # Chat interface, messages
    │   │   └── output/      # Data views, flags, email drafts
    │   ├── hooks/           # Custom React hooks
    │   └── services/        # API client
    └── package.json
```

## The Seven Processing Stages

1. **Document Ingestion** - Upload, scan, or email attachment
2. **OCR Text Extraction** - Tesseract with Google Vision fallback
3. **Document Classification** - Grok API identifies document type
4. **Data Extraction** - Pull structured data based on document type
5. **Validation & Flagging** - Check calculations, required fields, anomalies
6. **Agent Chat Activation** - Professional conversation about results
7. **Output Generation** - Emails, reports, exports

## Key Features

✅ **Multi-format Support** - PDF, DOCX, XLSX, JPG, PNG, WEBP  
✅ **Mobile Scanning** - Phone camera with auto-straighten and enhance  
✅ **Smart OCR** - Free Tesseract first, paid Google Vision fallback  
✅ **Ghana-focused** - Trained on GRA, SSNIT, and local document formats  
✅ **Validation Engine** - Catches calculation errors and missing data  
✅ **Context-aware Chat** - Agent knows all documents in session  
✅ **Email Drafting** - Professional templates for common scenarios  
✅ **Excel Export** - Formatted spreadsheets ready for sharing  

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload file
- `POST /api/documents/scan` - Process phone scan
- `GET /api/documents/` - List documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Agent Chat
- `POST /api/agent/message` - Send message, get response
- `POST /api/agent/initial-message` - Generate first agent message
- `WS /api/agent/ws/{session_id}` - WebSocket for streaming

### Compliance
- `POST /api/compliance/process` - Trigger full processing pipeline
- `GET /api/compliance/report/{session_id}` - Generate compliance report
- `POST /api/compliance/export` - Export data (Excel, CSV, JSON)

## Cost Estimate (Monthly)

| Service | Free Tier | MVP Scale |
|---------|-----------|-----------|
| Supabase (DB + Storage) | 500MB free | $25 |
| Grok API | Pay per token | ~$30-50 |
| Google Vision | 1000 units free | ~$5 |
| Redis (Upstash) | 10K req free | $10 |
| **Total** | | **~$70-90/month** |

**Break-even:** Just 2 paying customers at $50/month covers costs.

## Next Steps

This is Module 1 (Compliance Agent). After validation:
- Module 2: Real Estate Agent (property photos → listings)
- Unified Dashboard: Single login housing both modules

## License

Proprietary - ClearDesk Platform

---

*Built for Ghana, Built for Africa*
