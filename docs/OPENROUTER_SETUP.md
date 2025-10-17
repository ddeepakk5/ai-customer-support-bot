# 🚀 OpenRouter Setup Guide

## Free AI Model Access via OpenRouter

Get **free access** to premium AI models including OpenAI GPT models through OpenRouter!

---

## 📋 What is OpenRouter?

**OpenRouter** is a unified API that provides access to multiple AI models, including:
- ✅ GPT-3.5 Turbo (via OpenAI)
- ✅ GPT-4 (limited free credits)
- ✅ Mistral 7B (open-source)
- ✅ Llama 2 70B (open-source)
- ✅ And many more...

**Best Part:** FREE credits for OSS (Open Source Software) models!

---

## 🎯 Step-by-Step Setup

### Step 1: Get Free OpenRouter API Key

1. Visit: **https://openrouter.ai**
2. Click "Sign Up" or "Sign In"
3. No credit card required for free tier
4. Go to: https://openrouter.ai/keys
5. Copy your API key

### Step 2: Update .env File

```bash
# Copy template
cp .env.example .env

# Edit .env and set:
LLM_TYPE=openai
OPENROUTER_API_KEY=your_copied_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-3.5-turbo
```

### Step 3: Run Your Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
cd backend
python -m uvicorn app.main:app --reload

# Start frontend (new terminal)
streamlit run frontend/ui/app.py

# Open http://localhost:8501
```

**That's it! You're ready to go! 🎉**

---

## 🆓 Free Models Available

### Tier 1: Completely Free
- `mistral/mistral-7b-instruct` - Fast, quality responses
- `meta-llama/llama-2-70b-chat` - Powerful open-source
- `gpt-3.5-turbo` - Limited free tier (check balance)

### Tier 2: Free with Earned Credits
- Sign up → Get free credits
- Use free models → Earn more credits
- Reinvest credits for premium models

---

## ⚙️ Configuration Options

### Available Models

```bash
# Ultra-fast (best for FAQ)
OPENROUTER_MODEL=mistral/mistral-7b-instruct

# Most powerful free option
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat

# OpenAI quality
OPENROUTER_MODEL=gpt-3.5-turbo

# Best quality (uses credits faster)
OPENROUTER_MODEL=gpt-4-turbo-preview
```

### Recommended Configuration

```env
LLM_TYPE=openai
OPENROUTER_API_KEY=sk_your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=mistral/mistral-7b-instruct
```

Why Mistral?
- ✅ Free tier available
- ✅ Fast responses (< 5 seconds)
- ✅ Good quality answers
- ✅ Perfect for FAQ

---

## 💰 Pricing & Free Tier

### Free Credits
- All new users get: **$5 free credits**
- Use for any model
- No auto-billing when expired

### Free Models (No Credits Used)
- Most open-source models have a free tier
- Limited requests per day
- Check your dashboard for usage

### Credit Usage Examples
```
Mistral 7B:     $0.0002 per 1K tokens (very cheap!)
Llama 2 70B:    $0.0008 per 1K tokens (still cheap)
GPT-3.5-Turbo:  $0.001 per 1K tokens (moderate)
GPT-4:          $0.03 per 1K tokens (premium)
```

---

## 🔍 Monitor Your Usage

1. Go to: https://openrouter.ai/account/limits
2. View:
   - Credits remaining
   - Requests used
   - Model usage breakdown

---

## ⚡ Performance Tips

### For Best Results

```bash
# Use Mistral for speed
OPENROUTER_MODEL=mistral/mistral-7b-instruct

# Use Llama for quality
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat

# Use GPT-3.5 if you have credits
OPENROUTER_MODEL=gpt-3.5-turbo
```

### Typical Response Times
- Mistral: 2-5 seconds
- Llama 2: 3-8 seconds
- GPT-3.5: 1-3 seconds

### Cost Estimates (FAQ Chatbot)
- 100 conversations/day
- ~500 tokens per conversation
- **Monthly cost with Mistral:** ~$0.05
- **Monthly cost with Llama:** ~$0.20
- **Monthly cost with GPT-3.5:** ~$0.50

---

## 🆘 Troubleshooting

### Issue: "Invalid API Key"
```
Solution:
1. Check key at https://openrouter.ai/keys
2. Make sure LLM_TYPE=openai
3. Restart backend after changing .env
```

### Issue: "Rate Limited"
```
Solution:
1. You've exceeded free tier limit
2. Wait until next day
3. Or switch to a different model
4. Or add payment method for unlimited
```

### Issue: "No credits remaining"
```
Solution:
1. Check balance at https://openrouter.ai/account
2. Free tier: come back tomorrow
3. Or add payment method: https://openrouter.ai/account/billing
```

### Issue: "Model not found"
```
Solution:
1. Verify model name is correct
2. Check available models: https://openrouter.ai/docs/models
3. Try: mistral/mistral-7b-instruct
```

---

## 📚 Resources

- **OpenRouter Docs:** https://openrouter.ai/docs
- **Available Models:** https://openrouter.ai/docs/models
- **Pricing:** https://openrouter.ai/pricing
- **API Reference:** https://openrouter.ai/docs/api/chat-completions

---

## ✅ Quick Verification

After setup, test with curl:

```bash
# Get your key from https://openrouter.ai/keys
# Then test the API:

curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "model": "mistral/mistral-7b-instruct",
    "messages": [
      {
        "role": "user",
        "content": "What is 2+2?"
      }
    ]
  }'
```

You should get a response with the answer!

---

## 🎓 Next Steps

1. ✅ Get API key at https://openrouter.ai
2. ✅ Update `.env` with your key
3. ✅ Run the chatbot
4. ✅ Upload your FAQ PDF
5. ✅ Start chatting for FREE!

---

## 💡 Pro Tips

1. **Start with Mistral** - Free, fast, and good quality
2. **Monitor usage** - Check dashboard regularly
3. **Switch models** - Easy to change in .env
4. **No commitment** - Cancel anytime, no credit card needed
5. **Share with team** - Multiple projects on one account

---

**Enjoy your free, unlimited AI Customer Support Bot! 🚀**

*Powered by OpenRouter + OSS AI Models*
