# 🤖 AI Customer Support Chatbot

A production-ready AI-powered customer support chatbot with intelligent FAQ management, automatic ticket escalation, and AI response generation using GPT-OSS 20B model.

## 📌 Project Description

This is an enterprise-grade customer support solution that combines:
- **FAQ Database**: Store and search product FAQs from PDF documents
- **Intelligent Matching**: AI-powered relevance detection for customer questions
- **Hybrid Response System**: 
  - Direct FAQ answers when found
  - AI-generated responses for related product questions
  - Automatic escalation for off-topic queries
- **Ticket Management**: Automatic support ticket creation for escalations
- **Chat Interface**: Real-time Streamlit frontend with session management

Perfect for e-commerce, SaaS, and service-based businesses seeking to automate tier-1 support.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git
- OpenRouter API key (free at https://openrouter.ai)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/ddeepakk5/ai-customer-support-bot.git
cd ai-customer-support-bot
```

### 2️⃣ Create Virtual Environment

**On Windows (CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ You should see `(venv)` at the start of your terminal line

### 3️⃣ Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

**Copy the example file:**
```bash
cp .env.example .env
```

**Edit `.env` file and add your credentials:**
```
# LLM Configuration - Get free API key from https://openrouter.ai
LLM_TYPE=openai
OPENROUTER_API_KEY=your api-key here 
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b:free

# Database Configuration
DATABASE_URL=sqlite:///./support_bot.db

# Application Configuration
ENVIRONMENT=development
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
SESSION_TIMEOUT=30
MAX_MESSAGES_PER_SESSION=100
```

⚠️ **Never commit `.env` file - it contains sensitive API keys**

---

## ⚡ Running the Application

### Start Backend API (Terminal 1)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ API is ready at `http://localhost:8000`
📖 API Documentation: `http://localhost:8000/docs`

### Start Frontend UI (Terminal 2)

Keep the backend terminal open, open a new terminal:

```bash
# Activate venv first
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

cd frontend/ui
streamlit run app.py
```

Expected output:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

✅ Open `http://localhost:8501` in your browser

---

## 📋 Project Structure

```
ai-customer-support-bot/
│
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI application entry point
│       ├── config.py               # Configuration settings
│       ├── routes/
│       │   └── chat.py             # Chat endpoints, FAQ upload, escalation
│       ├── models/
│       │   ├── database.py         # SQLAlchemy database models
│       │   ├── __init__.py         # Database initialization
│       │   └── ...
│       ├── schemas/                # Request/response schemas
│       ├── utils/
│       │   ├── llm_integration.py  # OpenRouter LLM integration
│       │   └── pdf_processor.py    # PDF extraction & parsing
│       └── __pycache__/
│
├── frontend/
│   └── ui/
│       └── app.py                  # Streamlit chat interface
│
├── data/
│   ├── faq.md                      # Sample FAQ markdown
│   ├── FAQs.pdf                    # Sample FAQ PDF
│   └── sample-faqs.txt             # Sample FAQ text
│
├── tests/
│   └── test_api.py                 # API unit tests
│
├── docs/
│   ├── OPENROUTER_SETUP.md        # OpenRouter configuration guide
│   └── PROMPTS.md                 # LLM prompts reference
│
├── requirements.txt                # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

---

## 🔄 How It Works

### Chat Flow Diagram

```
┌─────────────────────┐
│  Customer Question  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Step 1: Search FAQ Database     │
└──────────┬──────────────────────┘
           │
      ┌────┴────┐
      │          │
      ▼          ▼
  FOUND      NOT FOUND
  ✅          │
  Return      │
  FAQ Answer  ▼
              │
      ┌───────────────────────┐
      │ Step 2: AI Relevance  │
      │ Check (GPT-OSS)       │
      └──────────┬────────────┘
                 │
            ┌────┴─────┐
            │           │
            ▼           ▼
        RELATED     OFF-TOPIC
        │           ▼
        │       Escalate ⚠️
        │       (Out of Scope)
        │
        ▼
    ┌─────────────────────┐
    │ Step 3: Generate AI │
    │ Response (GPT-OSS)  │
    │ + Escalation Info   │
    └─────────────────────┘
```

### Processing Steps

1. **FAQ Search**: Keyword matching against FAQ database (confidence ≥ 50%)
2. **Relevance Detection**: AI checks if question is product/service related
3. **Response Generation**: 
   - If FAQ match → Answer from database
   - If related but no FAQ → GPT-OSS generates response
   - If off-topic → Escalate to support team
4. **Ticket Creation**: Automatic support ticket for escalations

---

## 📤 Upload & Manage FAQs

### Using the UI

1. Open `http://localhost:8501`
2. In sidebar → **📚 FAQ Management**
3. Upload your FAQ PDF
4. Click **📤 Upload & Process FAQ**
5. View FAQ count in the metric

### FAQ PDF Format

Your PDF should have questions and answers in one of these formats:

**Format 1: Q: / A:**
```
Q: How do I reset my password?
A: Go to login page, click "Forgot Password", enter your email, and follow the reset link.

Q: What payment methods do you accept?
A: We accept credit cards, PayPal, UPI, and bank transfers.
```

**Format 2: Question: / Answer:**
```
Question: How do I change my email?
Answer: Go to Settings > Account > Change Email to update your email address.
```

**Format 3: Sections with Q/A:**
```
## Account Management

Q: How do I delete my account?
A: Go to Settings > Delete Account. This action is permanent.
```

### Clear FAQs

To remove old FAQs and upload new ones:
1. Sidebar → **🗑️ Clear All FAQs**
2. Upload new FAQ PDF
3. FAQs are automatically replaced

---

## 🔌 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Chat Endpoint
```bash
POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "session-abc123",
  "customer_id": "customer-xyz",
  "message": "How do I reset my password?",
  "conversation_history": [
    {"sender": "user", "content": "Previous message"},
    {"sender": "bot", "content": "Previous response"}
  ]
}

Response:
{
  "session_id": "session-abc123",
  "user_message": "How do I reset my password?",
  "bot_response": "Go to login page and click Forgot Password...",
  "confidence_score": 0.85,
  "response_type": "faq",
  "requires_escalation": false,
  "timestamp": "2025-10-17T10:30:00"
}
```

### FAQ Management
```bash
# Get all FAQs
GET /api/v1/faqs

# Upload FAQ PDF
POST /api/v1/faqs/upload
Content-Type: multipart/form-data
Body: file=<your-faq.pdf>

# Clear all FAQs
DELETE /api/v1/faqs/clear/all

# Delete single FAQ
DELETE /api/v1/faqs/{faq_id}
```

### Session Management
```bash
# Create new session
POST /api/v1/sessions
{
  "customer_id": "customer-xyz"
}

# Get session messages
GET /api/v1/sessions/{session_id}/messages
```

📖 **Full API Documentation**: http://localhost:8000/docs

---

## 🔧 Configuration & Customization

### Adjust Matching Thresholds

Edit `backend/app/routes/chat.py`:

```python
# FAQ confidence threshold (line ~226)
if faq_found and faq_confidence >= 0.5:  # Change 0.5 to adjust

# AI relevance threshold (line ~237)
if is_related and relevance_confidence >= 0.6:  # Change 0.6 to adjust
```

### Change AI Model

Edit `.env`:
```bash
# Use different OpenRouter model
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat:free
# Or: mistralai/mistral-7b-instruct:free
# Or: microsoft/phi-2
```

### Database Configuration

Edit `.env` for different database:
```bash
# SQLite (default)
DATABASE_URL=sqlite:///./support_bot.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/support_bot

# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost/support_bot
```

---

## 📊 Response Types

| Type | Trigger | Behavior |
|------|---------|----------|
| **FAQ** | Exact/partial FAQ match (≥50% confidence) | Returns FAQ answer directly |
| **AI Generated** | Product-related question not in FAQ | GPT-OSS generates response |
| **Out of Scope** | Question unrelated to products/services | Escalates to support team |
| **Escalated** | System error or AI generation fails | Creates support ticket |

---

## 🧪 Testing the Bot

### Test Case 1: FAQ Answer ✅
```
Q: How do I reset my password?
Expected: Direct answer from FAQ
```

### Test Case 2: AI-Generated Answer (Related) 🤖
```
Q: Can I use multiple accounts?
Expected: AI-generated response (if not in FAQ)
```

### Test Case 3: Escalation ⚠️
```
Q: Tell me a joke
Expected: Escalation message (off-topic)
```

---

## ⚙️ Environment Variables Reference

```bash
# LLM Configuration
LLM_TYPE=openai                          # LLM provider
OPENROUTER_API_KEY=sk-or-v1-xxxxx       # Your API key (FREE)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-20b:free

# Database
DATABASE_URL=sqlite:///./support_bot.db

# Application
ENVIRONMENT=development                  # development or production
DEBUG=True                               # Enable debug mode
API_HOST=0.0.0.0                        # API server host
API_PORT=8000                           # API server port
LOG_LEVEL=INFO                          # Logging level
SESSION_TIMEOUT=30                      # Session timeout (minutes)
MAX_MESSAGES_PER_SESSION=100            # Max messages per session
```

---

## 📦 Dependencies

```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
streamlit==1.28.1         # Frontend framework
sqlalchemy==2.0.23        # ORM
pydantic==2.5.0           # Data validation
python-dotenv==1.0.0      # Environment variables
pydantic-settings==2.1.0  # Settings management
pdfplumber==0.10.3        # PDF extraction
PyPDF2==3.0.1             # PDF processing
requests==2.31.0          # HTTP client
```

---

## 🔐 Security Best Practices

✅ **What we've done:**
- API key stored in `.env` (not in code)
- `.env` file added to `.gitignore`
- PDF files deleted after processing
- SQL injection prevention (SQLAlchemy ORM)
- Input validation on all endpoints
- CORS protection

⚠️ **Before production:**
- Use PostgreSQL instead of SQLite
- Enable HTTPS/SSL
- Add authentication (JWT tokens)
- Implement rate limiting
- Set `DEBUG=False` in `.env`
- Use strong database password
- Implement API key rotation

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000               # macOS/Linux

# Use different port
python -m uvicorn app.main:app --port 8001
```

### PDF upload fails
- ✅ Ensure file is actual PDF (not image/screenshot)
- ✅ Check file size < 10MB
- ✅ Verify Q&A format: "Q: ... A: ..."
- ✅ Check backend logs for errors

### Questions not matching FAQs
```bash
# Check uploaded FAQs
curl http://localhost:8000/api/v1/faqs

# Verify FAQ count in UI sidebar
# Adjust matching threshold if needed (see Configuration section)
```

### API key not working
```bash
# Get free OpenRouter API key: https://openrouter.ai
# Sign up → Get API key → Add to .env
# Restart backend
```

### Virtual environment issues
```bash
# Deactivate and recreate
deactivate
rm -r venv/  # or rmdir /s venv (Windows)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **OpenRouter Setup**: See `docs/OPENROUTER_SETUP.md`
- **LLM Prompts**: See `docs/PROMPTS.md`
- **FastAPI Docs**: http://localhost:8000/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **OpenRouter Models**: https://openrouter.ai/models

---

## 🚀 Deployment

### Deploy Backend (Heroku, Railway, Render)
```bash
# Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port $PORT" > Procfile

# Push to platform
git push heroku main
```

### Deploy Frontend (Streamlit Cloud)
```bash
# Connect GitHub repo
# https://streamlit.io/cloud
```

---

## 📞 Support & Contributing

- 🐛 Found a bug? Open an issue
- 💡 Have a feature idea? Create a discussion
- 🤝 Want to contribute? Submit a pull request

---

## 📝 License

Open Source - Feel free to use and modify

---

**Happy chatting! 🤖💬**
