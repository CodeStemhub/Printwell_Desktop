# ClearDesk - Compliance Agent MVP

Document Intelligence Platform for African Business - Module 1 (Compliance Agent)

## Overview

This is the first module of ClearDesk, a two-module SaaS platform. This MVP focuses solely on the **Compliance Agent** which:

- Accepts business documents (PDF, DOCX, images)
- Automatically classifies document types (GRA VAT Returns, SSNIT Forms, Invoices, etc.)
- Extracts structured data using AI
- Flags errors and validation issues
- Provides an intelligent chat interface for querying documents

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL
- Redis (optional for caching)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs will be available at: http://localhost:8000/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## Features

### Document Processing
- **Upload**: Drag & drop or click to upload documents
- **OCR**: Automatic text extraction from images and scanned documents
- **Classification**: AI-powered document type detection
- **Data Extraction**: Structured data extraction based on document type
- **Validation**: Automatic flagging of errors and missing information

### Supported Document Types
- GRA VAT Returns
- SSNIT Forms
- Invoices
- Bank Statements
- Payroll Sheets
- Customs Declarations
- Purchase Orders
- Employment Contracts
- Receipts

### Chat Interface
- Real-time conversation with AI agent
- Context-aware responses based on uploaded documents
- Proactive issue identification
- Natural language queries about document data

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Documents
- `POST /api/documents/upload` - Upload document
- `POST /api/documents/scan` - Upload mobile scan
- `GET /api/documents/` - List documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Agent/Chat
- `GET /api/agent/session` - Get/create chat session
- `POST /api/agent/message` - Send message to agent
- `GET /api/agent/history` - Get chat history
- `WS /ws/chat/{session_id}` - WebSocket for real-time chat

### Compliance
- `POST /api/compliance/classify` - Re-classify document
- `GET /api/compliance/summary` - Get compliance summary

## Technology Stack

### Backend
- FastAPI (Python 3.13)
- SQLAlchemy + PostgreSQL
- Grok API for AI processing
- Tesseract OCR
- JWT Authentication

### Frontend
- React 18 + Vite
- TailwindCSS
- Framer Motion
- React Router
- Axios

## Project Structure

```
cleardesk/
├── backend/
│   ├── api/routes/       # API route handlers
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   ├── config.py         # Configuration
│   └── main.py           # App entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   └── services/     # API client
│   └── package.json
└── README.md
```

## Next Steps

After validating this Compliance Agent MVP, we will build:
1. **Module 2 - Real Estate Agent**: Property listing generation and management
2. **Unified Dashboard**: Single dashboard housing both modules

## License

Built for Ghana 🇬🇭 • Made for Africa
