# AI Customer Support Chatbot

A production-ready customer support bot with PDF-based FAQ management. Answers questions only from your FAQ database, creates support tickets for new questions, and guides users appropriately.

## 🎯 What This Does

- **PDF FAQ Upload**: Upload FAQ PDFs → Automatic extraction & storage
- **FAQ-First Responses**: Only answers from your FAQ database
- **Smart Relevance Detection**: AI checks if questions are product-related
- **Automatic Tickets**: Creates support tickets for product questions not in FAQ
- **User Guidance**: Guides users to ask product/service questions only

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key (free at openrouter.ai)
```

### 2. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend (New Terminal)

```bash
cd frontend/ui
streamlit run app.py
```

Opens at `http://localhost:8501`

### 4. Upload FAQ PDF

1. In sidebar → "📚 FAQ Management"
2. Upload FAQ PDF with Q&A format
3. Click "📤 Upload & Process FAQ"

## 📋 System Flow

```
User Question
    ↓
Search FAQ Database
├─ Match Found (≥50%) → Answer from FAQ ✅
└─ No Match → Check if product-related
    ├─ YES → Create Support Ticket 🎫
    └─ NO → Send Guidance Message 📋
```

## 📄 FAQ Format

Create a PDF with:

```
Q: How do I reset my password?
A: Go to login page and click 'Forgot Password'. Enter your email and follow the reset link.

Q: What payment methods do you accept?
A: We accept credit cards, UPI, net banking, and PayPal.
```

Supports Q:/A:, Question:/Answer:, section headers, and numbered formats.

## 🔌 API Endpoints

```bash
# Chat
POST /api/v1/chat
{
  "session_id": "session-abc123",
  "customer_id": "customer-xyz",
  "message": "How do I reset my password?"
}

# Upload FAQ
POST /api/v1/faqs/upload

# Get all FAQs
GET /api/v1/faqs

# Delete FAQ
DELETE /api/v1/faqs/{faq_id}

# API Docs
GET /docs
```

## 📊 Response Types

| Type | When | Action |
|------|------|--------|
| **FAQ** ✅ | Matches FAQ (≥50% confidence) | Direct answer |
| **Ticket** 🎫 | Related question not in FAQ | Creates ticket |
| **Guidance** 📋 | Unrelated question | Suggests topics |

## 🛠️ Project Structure

```
ai-customer-support-bot/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI setup
│       ├── routes/chat.py       # Chat & upload endpoints
│       ├── models/database.py   # Database models
│       ├── schemas/             # Request/response schemas
│       └── utils/
│           ├── llm_integration.py
│           └── pdf_processor.py
├── frontend/
│   └── ui/app.py               # Streamlit interface
├── requirements.txt            # Dependencies
├── .env.example               # Configuration template
└── README.md                  # This file
```

## 💾 Database

**FAQs**: `faq_documents` table
- question, answer, category, keywords, source, is_active

**Tickets**: `escalations` table
- escalation_id (ticket-xxx), reason, status, priority

## ⚙️ Configuration

Edit `backend/app/routes/chat.py` to adjust thresholds:

```python
# FAQ matching threshold (change 0.5)
if faq_found and faq_confidence >= 0.5:

# AI relevance threshold (change 0.6)
if is_related and relevance_confidence >= 0.6:
```

## 🔑 Environment Variables

```
OPENROUTER_API_KEY=your_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DATABASE_URL=sqlite:///./support_bot.db
DEBUG=False
```

## 📚 Dependencies

- FastAPI - API framework
- Streamlit - UI framework
- SQLAlchemy - Database ORM
- PyPDF2/pdfplumber - PDF processing
- OpenRouter - LLM API (free)

## 🧪 Testing

1. **Upload FAQ PDF** → Check FAQ Management sidebar
2. **Ask FAQ question** → Should get instant answer ✅
3. **Ask related question** → Should create ticket 🎫
4. **Ask unrelated question** → Should get guidance 📋

## 🐛 Troubleshooting

**PDF not uploading?**
- Ensure PDF format (not image)
- Check Q&A format: "Q: ... A: ..."
- Verify file size < 10MB

**Questions not matching FAQs?**
- Check `/api/v1/faqs` endpoint for uploaded FAQs
- Verify question keywords match FAQ text
- Review confidence threshold setting

**Tickets not creating?**
- Check backend logs
- Verify AI relevance detection working
- Ensure question is product-related

## 📞 Support

- Backend logs: See terminal where backend is running
- Frontend logs: See Streamlit terminal
- API Documentation: `http://localhost:8000/docs`

## 🔐 Security

- API key stored in .env (not in repo)
- PDF files deleted after processing
- Input validation on all uploads
- SQL injection prevention (SQLAlchemy ORM)

## 📝 License

Open source
