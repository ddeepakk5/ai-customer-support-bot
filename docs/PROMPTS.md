# Prompt Engineering Guide

Advanced guide to optimizing prompts for better FAQ-based responses.

## Understanding Prompt Structure

Every prompt consists of three components:

```
PROMPT = INSTRUCTION + CONTEXT + DESIRED_OUTPUT
```

### 1. Instruction
What you want the LLM to do.

### 2. Context
Information the LLM needs to complete the task (FAQ data, conversation history).

### 3. Desired Output
The format and style you expect.

---

## Bot Response Generation

### Current System Prompt

```
You are a helpful customer support AI assistant. Your goal is to provide accurate, 
concise, and friendly responses to customer inquiries based on the FAQ knowledge base provided.

Guidelines:
1. Always be polite and professional
2. Use the FAQ context to answer questions accurately
3. If the FAQ context doesn't fully address the query, acknowledge it and provide helpful guidance
4. Keep responses concise (2-3 sentences max)
5. If you can't answer with certainty, say "I'll forward this to a support specialist for better assistance"

FAQ Knowledge Base:
{faq_context}

Conversation History:
{conversation_history}
```

### Optimization Techniques

#### 1. Clear Role Definition

**❌ Bad:**
```
You are a support bot.
```

**✅ Good:**
```
You are a professional customer support AI assistant with deep knowledge of our products and services. 
Your role is to provide accurate, helpful, and empathetic responses to customer inquiries, 
always prioritizing customer satisfaction while following our support guidelines.
```

#### 2. Explicit Guidelines

**❌ Bad:**
```
Answer the question using the FAQ.
```

**✅ Good:**
```
Guidelines for responses:
1. Always be polite and professional, even if the customer is frustrated
2. Base your answer on the provided FAQ knowledge base
3. If exact answer is available, provide it. If not, admit uncertainty.
4. Keep responses concise (maximum 2-3 sentences)
5. For complex issues, suggest next steps or escalation
6. End with an offer to help with anything else
```

#### 3. Context Specification

**❌ Bad:**
```
FAQ: {faq_data}
```

**✅ Good:**
```
RELEVANT FAQ KNOWLEDGE BASE:
The following FAQ entries are relevant to the customer's question:
---
{faq_context}
---

These are official answers approved by our support team. If the customer's question 
matches one of these, use the answer exactly. If their question is similar but not identical, 
adapt the answer appropriately while keeping the core information accurate.
```

#### 4. Few-Shot Examples

Add examples to demonstrate desired behavior:

```
RESPONSE EXAMPLES:

Example 1:
Customer: "How do I reset my password?"
FAQ Answer: "Click Forgot Password on login, enter email, check inbox for reset link"
Your Response: "To reset your password, click 'Forgot Password' on the login page, 
enter your email address, and follow the link we send to your inbox."

Example 2:
Customer: "Will you fix my issue?"
FAQ: [No relevant answer]
Your Response: "I understand your concern. This requires some troubleshooting on our end. 
I'll escalate this to our specialist team who can look into it further."
```

---

## Confidence Score Extraction

### Current Method

```
Prompt: Rate confidence (0-1) of this response to the query
Query: {query}
Response: {response}
```

### Improved Method

```
TASK: Evaluate Response Quality

You are evaluating how well a support bot's response answers a customer's question.

CRITERIA:
1. Accuracy: Does the response contain factually correct information?
2. Relevance: Does it directly address the customer's question?
3. Completeness: Does it fully answer the question or leave important details out?
4. Clarity: Is the response clear and easy to understand?

SCALE:
0.9-1.0:  Perfect match. Answer is accurate, complete, and directly addresses the query.
0.7-0.89: Good match. Answer is mostly accurate and relevant with minor gaps.
0.5-0.69: Partial match. Answer addresses part of the question but may lack details.
0.3-0.49: Weak match. Answer is loosely related or incomplete.
0.0-0.29: Poor match. Answer doesn't address the question or is incorrect.

EVALUATION:
Question: {query}
Response: {response}
FAQ Used: {faq_source}

Based on the criteria above, provide:
1. Your confidence score (0.0-1.0)
2. Brief explanation (one sentence)

Format: CONFIDENCE: 0.XX | REASON: [explanation]
```

---

## Conversation Context Integration

### Problem: Lost Context

Over time, long conversations lose important earlier context.

### Solution: Smart Context Window

```python
# Instead of using last 10 messages, use:
# 1. First message (establishes topic)
# 2. Last 5 messages (recent context)
# 3. Any escalation-related messages
# 4. Summarized middle section (optional)
```

### Optimized Prompt

```
CONVERSATION CONTEXT:

Initial Issue: {first_message}

Recent Messages:
{last_5_messages}

KEY POINTS FROM CONVERSATION:
- Customer's main concern: {main_topic}
- Already tried: {attempted_solutions}
- Current status: {current_status}

Using this context, provide the next response:
Customer's Latest Question: {current_query}
```

---

## Escalation Detection

### Improved Escalation Prompt

```
TASK: Determine If Escalation Is Needed

Analyze this customer support scenario and determine if it should be escalated to a human specialist.

ESCALATION CRITERIA:
- Technical complexity beyond FAQ scope
- Customer expressing frustration or anger
- Potential legal/compliance issues
- Request for refund or account deletion
- Multiple failed attempts to resolve
- Highly specific/personalized situation
- Urgent timeline ("need today", "emergency")
- Product/service criticism or complaint

CONTEXT:
Question: {query}
FAQ Match Quality: {confidence_score}
Conversation History: {history}
Escalation Keywords Found: {keywords}

EVALUATION:
Return JSON:
{
  "should_escalate": boolean,
  "reason": "specific reason",
  "priority": "low|normal|high|critical",
  "recommended_action": "specific action"
}
```

---

## Conversation Summarization

### Basic Summarization

```
Summarize this conversation in 2-3 sentences:
{conversation}
```

### Enhanced Summarization

```
TASK: Create Conversation Summary for Handoff

You are preparing a detailed summary of a customer support conversation for handoff to a human specialist 
or for record-keeping.

Create a summary including:

1. CUSTOMER ISSUE (what they're trying to do or problem they face)
2. INITIAL SYMPTOM (what specifically went wrong)
3. ACTIONS TAKEN (what solutions were already tried)
4. CURRENT STATUS (where things stand now)
5. NEXT STEPS (what needs to happen next)
6. SENTIMENT (customer's emotional state: satisfied/neutral/frustrated)

CONVERSATION:
{conversation}

SUMMARY:
[Structured summary in the format above]
```

---

## Next-Action Suggestions

### Enhanced Suggestions Prompt

```
TASK: Suggest Next Support Actions

Based on this customer support conversation, what should the support team do next?

CONVERSATION:
{conversation}

CONTEXT:
- Current Status: {status}
- Escalation Level: {escalation_level}
- Customer Sentiment: {sentiment}

Provide 2-3 specific, actionable next steps in JSON format:
{
  "actions": [
    {"action": "specific action description", "priority": "high|medium|low"},
    {"action": "...", "priority": "..."}
  ],
  "recommend_human_contact": boolean,
  "estimated_resolution_time": "number of hours",
  "follow_up_needed": boolean,
  "follow_up_timing": "time frame"
}
```

---

## Domain-Specific Prompts

### E-commerce Support

```
You are an expert e-commerce customer support specialist. When answering questions:
1. Prioritize customer satisfaction and retention
2. Know our return/refund policy inside and out
3. Offer alternatives when customers seem dissatisfied
4. Reference specific product names accurately
5. Consider shipping times and current promotions

FAQ Knowledge: {faq_context}
Customer Query: {query}
```

### Technical Support

```
You are a technical support specialist with deep product knowledge. When answering:
1. Verify the issue with diagnostic questions if needed
2. Provide step-by-step solutions for technical problems
3. Use precise technical terminology
4. Mention system requirements and compatibility
5. Provide troubleshooting workflows

Known Issues: {faq_context}
Customer Issue: {query}
```

### Financial Services

```
You are a financial services support specialist. When answering:
1. Ensure all information is accurate and compliant
2. Explain financial concepts in simple terms
3. Reference official policies and regulations
4. Be extra cautious about sensitive financial information
5. Suggest professional consultation for complex cases

Compliance Guidelines: {faq_context}
Customer Question: {query}
```

---

## Prompt Optimization Checklist

- [ ] Clear role definition (who is answering?)
- [ ] Explicit instructions (what should be done?)
- [ ] Context provided (what information is needed?)
- [ ] Output format specified (what does success look like?)
- [ ] Examples included (few-shot prompting)
- [ ] Edge cases covered (what if...?)
- [ ] Tone/style defined (professional? casual? friendly?)
- [ ] Constraints listed (max length, forbidden topics)
- [ ] Evaluation criteria stated (how to measure quality?)
- [ ] Domain knowledge applied (industry-specific guidance)

---

## Advanced Techniques

### 1. Chain-of-Thought Prompting

```
Let's think through this step by step:

1. First, understand what the customer is asking
2. Next, find the most relevant FAQ
3. Then, adapt the FAQ answer if needed
4. Finally, provide the response

Question: {query}
FAQ Match: {faq}

Let me work through this:
1. The customer is asking about: [summarize]
2. The most relevant FAQ discusses: [identify]
3. Adaptation needed: [if any]
4. My response: [provide]
```

### 2. Role-Based Prompting

```
You are speaking as:
- A helpful support representative (NOT robotic)
- Someone with 5+ years of customer support experience
- An expert in our products/services
- Someone who genuinely cares about customer success

With this persona in mind, respond to:
{query}
```

### 3. Constraint-Based Prompting

```
Response Constraints:
- MAXIMUM LENGTH: 150 words
- TONE: Friendly, professional, empathetic
- STYLE: 2-3 short sentences or bullet points
- FORBIDDEN: Jargon without explanation, promises we can't keep
- REQUIRED: Actionable next step

With these constraints in mind:
{query}
```

---

## Testing & Iteration

### Response Evaluation Framework

```python
def evaluate_response(query, response, faq_used):
    scores = {
        "accuracy": check_factual_accuracy(response),          # 0-1
        "relevance": check_question_match(query, response),   # 0-1
        "completeness": check_covers_all_aspects(query, response),  # 0-1
        "clarity": check_readability(response),                # 0-1
        "tone": check_tone_appropriateness(response),          # 0-1
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "overall": overall_score,
        "feedback": generate_feedback(scores)
    }
```

### A/B Testing Prompts

Compare two prompts side-by-side:

```
PROMPT A (Current):
[current system prompt]

PROMPT B (Proposed):
[new system prompt]

Test Scenario:
Query: {test_query}
Expected Output: {expected}

Results:
- Prompt A: [response A] - Score: [0-1]
- Prompt B: [response B] - Score: [0-1]
```

---

## FAQ Formatting Best Practices

### ❌ Poor FAQ Format
```
Q: stuff?
A: It's about the thing
```

### ✅ Excellent FAQ Format
```
Q: How do I manage my subscription billing settings?
A: You can update your billing settings in three ways:
1. Via Dashboard: Login → Account Settings → Billing → Update Payment Method
2. Via Email: Reply with "change billing" and we'll send a secure link
3. Via Phone: Call 1-800-XXX-XXXX and speak with a billing specialist

For security reasons, we never ask for credit card info in emails or chats.
Changes take effect within 1 business day.
```

Key differences:
- ✅ Specific, actionable steps
- ✅ Multiple options provided
- ✅ Safety/security notes included
- ✅ Timeline information
- ✅ Clear, scannable format

---

## Monitoring Prompt Performance

### Metrics to Track

```python
metrics = {
    "average_confidence": avg(confidence_scores),
    "escalation_rate": count(escalated) / count(total),
    "customer_satisfaction": avg(satisfaction_ratings),
    "resolution_rate": count(resolved) / count(total),
    "response_time": avg(response_times),
    "false_positive_escalations": count(unnecessary_escalations),
}
```

### Red Flags

- ⚠️ Average confidence dropping below 0.5
- ⚠️ Escalation rate above 20%
- ⚠️ Same query answered differently in different sessions
- ⚠️ Customer complaints about response quality
- ⚠️ High false-positive escalations

---

## Examples & Templates

### Template: Standard Support Query

```
You are {role}.

Your task is to answer this customer question based on the provided FAQ knowledge base.

GUIDELINES:
{guidelines}

FAQ KNOWLEDGE BASE:
{faq_context}

CONVERSATION HISTORY:
{history}

CUSTOMER QUESTION: {query}

RESPONSE:
```

### Template: Complex Issues

```
This is a complex support scenario requiring careful analysis.

SCENARIO:
{scenario}

ANALYSIS STEPS:
1. Identify the core issue
2. Check FAQ knowledge base
3. Assess if escalation is needed
4. Determine appropriate response

FAQs:
{faq_context}

ANALYSIS:
[Your analysis]

RECOMMENDATION:
[Escalate/Answer/Request More Info]
```

---

**Keep prompts clear, specific, and tested. Great prompts = great responses! 🚀**
