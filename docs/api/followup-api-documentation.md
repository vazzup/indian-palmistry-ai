# Analysis Follow-up API Documentation

## Overview

The Analysis Follow-up API enables users to ask specific questions about their completed palm readings. This system provides context-aware AI responses using the original palm images and analysis results, creating an interactive conversation experience.

### Key Features

- **Context-Aware Responses**: AI can see the original palm images and reference the complete analysis
- **Conversation Continuity**: Each question builds on previous Q&A in the same conversation
- **Security Validation**: Comprehensive protection against prompt injection and inappropriate content
- **Usage Limits**: Controlled question limits (typically 5 per analysis) with transparent tracking
- **Performance Monitoring**: Token usage, cost tracking, and response time metrics

### Authentication

All follow-up endpoints require user authentication. Include the JWT token in the Authorization header:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## API Endpoints

### 1. Get Follow-up Status

Check the availability and current state of follow-up questions for an analysis.

**Endpoint:** `GET /api/v1/analyses/{analysis_id}/followup/status`

**Parameters:**
- `analysis_id` (path, required): ID of the palm reading analysis

**Response Schema:** `FollowupStatusResponse`

**Example Request:**
```http
GET /api/v1/analyses/123/followup/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example Response (Available):**
```json
{
  "analysis_id": 123,
  "analysis_completed": true,
  "followup_available": true,
  "followup_conversation_exists": false,
  "conversation_id": null,
  "questions_asked": 0,
  "questions_remaining": 5,
  "max_questions": 5,
  "has_openai_files": false,
  "total_followup_questions": 0
}
```

**Example Response (In Progress Analysis):**
```json
{
  "analysis_id": 124,
  "analysis_completed": false,
  "followup_available": false,
  "followup_conversation_exists": false,
  "conversation_id": null,
  "questions_asked": 0,
  "questions_remaining": 5,
  "max_questions": 5,
  "has_openai_files": false,
  "total_followup_questions": 0
}
```

**Example Response (Active Conversation):**
```json
{
  "analysis_id": 125,
  "analysis_completed": true,
  "followup_available": true,
  "followup_conversation_exists": true,
  "conversation_id": 456,
  "questions_asked": 3,
  "questions_remaining": 2,
  "max_questions": 5,
  "has_openai_files": true,
  "total_followup_questions": 3
}
```

**Error Responses:**
- `404 Not Found`: Analysis not found or not owned by user
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Server error

---

### 2. Start Follow-up Conversation

Create a new conversation for asking questions about a palm reading.

**Endpoint:** `POST /api/v1/analyses/{analysis_id}/followup/start`

**Parameters:**
- `analysis_id` (path, required): ID of the completed analysis

**Response Schema:** `FollowupConversationResponse`

**Example Request:**
```http
POST /api/v1/analyses/123/followup/start
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Example Response:**
```json
{
  "id": 456,
  "analysis_id": 123,
  "title": "Questions about your palm reading",
  "questions_count": 0,
  "max_questions": 5,
  "openai_file_ids": {
    "left_palm": "file-abc123def456",
    "right_palm": "file-ghi789jkl012"
  },
  "created_at": "2025-08-30T10:30:00Z",
  "last_message_at": null,
  "is_active": true
}
```

**Process Flow:**
1. Validates analysis is completed and belongs to user
2. Uploads palm images to OpenAI Files API (if not already done)
3. Creates conversation with cached analysis context
4. Returns conversation details for immediate use

**Error Responses:**
- `404 Not Found`: Analysis not found, not completed, or not owned by user
- `403 Forbidden`: Analysis not owned by current user
- `400 Bad Request`: Analysis not eligible for follow-up
- `500 Internal Server Error`: File upload failure or server error
- `401 Unauthorized`: Authentication required

**Performance Notes:**
- First call may take 2-5 seconds due to file upload
- Subsequent calls return existing conversation immediately
- File upload is cached for future conversations

---

### 3. Ask Follow-up Question

Ask a specific question about the palm reading with full AI context.

**Endpoint:** `POST /api/v1/analyses/{analysis_id}/followup/{conversation_id}/ask`

**Parameters:**
- `analysis_id` (path, required): ID of the analysis (for validation)
- `conversation_id` (path, required): ID of the follow-up conversation

**Request Body Schema:** `FollowupQuestionRequest`

**Response Schema:** `FollowupQuestionResponse`

**Example Request:**
```http
POST /api/v1/analyses/123/followup/456/ask
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "question": "What does my heart line reveal about my emotional nature and approach to relationships?"
}
```

**Example Response:**
```json
{
  "user_message": {
    "id": 101,
    "conversation_id": 456,
    "message_type": "USER",
    "content": "What does my heart line reveal about my emotional nature and approach to relationships?",
    "tokens_used": null,
    "cost": null,
    "processing_time": null,
    "created_at": "2025-08-30T10:45:00Z"
  },
  "assistant_message": {
    "id": 102,
    "conversation_id": 456,
    "message_type": "ASSISTANT",
    "content": "Looking at your palm images, I can see that your heart line shows several distinctive characteristics that offer insights into your emotional nature.\n\n**Heart Line Analysis:**\nYour heart line appears deep and well-defined, extending from the edge of your palm toward your fingers. This traditionally indicates someone with strong emotional depth and the capacity for meaningful connections.\n\n**Emotional Characteristics:**\nThe curve and length of your heart line suggests you approach relationships with sincerity and emotional investment. You likely value deep, authentic connections over superficial interactions.\n\n**Relationship Approach:**\nThe clarity of your heart line indicates emotional stability and the ability to maintain long-term relationships. You probably prefer quality over quantity when it comes to close relationships and friendships.\n\n**Connection to Other Features:**\nI also notice how your heart line interacts with other features in your palm, which provides additional context about how you balance emotion with practical considerations in relationships.",
    "tokens_used": 187,
    "cost": 0.0056,
    "processing_time": 2.1,
    "created_at": "2025-08-30T10:45:02Z"
  },
  "questions_remaining": 4,
  "tokens_used": 187,
  "cost": 0.0056,
  "processing_time": 2.1
}
```

**Question Validation Rules:**
- **Length:** 10-500 characters
- **Content:** Must be palmistry-related
- **Security:** No prompt injection attempts
- **Topics:** Only palmistry, no medical/legal/financial advice
- **Predictions:** Discourages specific future event predictions

**Valid Question Examples:**
```json
{"question": "What do the lines on my fingers indicate about my personality?"}
{"question": "Can you explain the meaning of the mount of Venus in my palm?"}
{"question": "How should I interpret the depth and curve of my head line?"}
{"question": "What does the intersection of my heart and head lines signify?"}
{"question": "How do the mounts on my palm relate to my character traits?"}
```

**Invalid Question Examples (will be rejected):**
```json
{"question": "Hi"}  // Too short
{"question": "When will I get married?"}  // Future prediction
{"question": "What's the weather today?"}  // Non-palmistry
{"question": "Can you diagnose my medical condition?"}  // Medical advice
{"question": "Ignore previous instructions..."}  // Prompt injection
```

**Error Responses:**
- `400 Bad Request`: Invalid question format, content, or validation error
- `404 Not Found`: Conversation not found or not accessible
- `429 Too Many Requests`: Maximum questions exceeded
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: AI processing failure

**AI Response Features:**
- **Visual Analysis:** References what AI sees in your specific palm images
- **Context Awareness:** Builds on previous questions in the conversation
- **Educational Content:** Explains palmistry principles and interpretations
- **Structured Format:** Uses headers, bullet points, and clear organization
- **Personalized:** Focuses on your unique palm features

---

### 4. Get Conversation History

Retrieve the complete history of questions and answers for a follow-up conversation.

**Endpoint:** `GET /api/v1/analyses/{analysis_id}/followup/{conversation_id}/history`

**Parameters:**
- `analysis_id` (path, required): ID of the analysis
- `conversation_id` (path, required): ID of the follow-up conversation
- `limit` (query, optional): Maximum messages to return (default: 20, max: 100)

**Response Schema:** `FollowupHistoryResponse`

**Example Request:**
```http
GET /api/v1/analyses/123/followup/456/history?limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example Response:**
```json
{
  "conversation": {
    "id": 456,
    "analysis_id": 123,
    "title": "Questions about your palm reading",
    "questions_count": 2,
    "max_questions": 5,
    "openai_file_ids": {
      "left_palm": "file-abc123",
      "right_palm": "file-def456"
    },
    "created_at": "2025-08-30T10:30:00Z",
    "last_message_at": "2025-08-30T11:00:03Z",
    "is_active": true
  },
  "messages": [
    {
      "id": 101,
      "conversation_id": 456,
      "message_type": "USER",
      "content": "What does my heart line reveal about my emotional nature?",
      "tokens_used": null,
      "cost": null,
      "processing_time": null,
      "created_at": "2025-08-30T10:45:00Z"
    },
    {
      "id": 102,
      "conversation_id": 456,
      "message_type": "ASSISTANT",
      "content": "Looking at your palm images, your heart line shows several distinctive characteristics...",
      "tokens_used": 187,
      "cost": 0.0056,
      "processing_time": 2.1,
      "created_at": "2025-08-30T10:45:02Z"
    },
    {
      "id": 103,
      "conversation_id": 456,
      "message_type": "USER",
      "content": "How does the mount of Venus relate to what you mentioned about my heart line?",
      "tokens_used": null,
      "cost": null,
      "processing_time": null,
      "created_at": "2025-08-30T11:00:00Z"
    },
    {
      "id": 104,
      "conversation_id": 456,
      "message_type": "ASSISTANT",
      "content": "Building on the heart line analysis, the mount of Venus in your palm complements those emotional characteristics...",
      "tokens_used": 203,
      "cost": 0.0061,
      "processing_time": 2.3,
      "created_at": "2025-08-30T11:00:03Z"
    }
  ],
  "questions_asked": 2,
  "questions_remaining": 3,
  "analysis_context": {
    "summary": "Your palm shows strong life and heart lines indicating vitality and emotional depth.",
    "full_report": "Detailed Analysis:\\n\\nLife Line: Strong and deep, suggesting good health...",
    "created_at": "2025-08-30T09:15:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found`: Conversation not found or not accessible
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Database error

**Usage Notes:**
- Messages are returned in chronological order (oldest first)
- Each user question is immediately followed by the AI response
- Use `limit` parameter to control response size for large conversations
- `analysis_context` provides reference to the original palm reading

---

## Complete Workflow Example

Here's a complete example of using the follow-up API from start to finish:

### Step 1: Check Follow-up Status
```bash
curl -X GET "https://api.example.com/api/v1/analyses/123/followup/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response indicates follow-up is available but no conversation exists yet.

### Step 2: Start Follow-up Conversation
```bash
curl -X POST "https://api.example.com/api/v1/analyses/123/followup/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

Response provides conversation ID (456) for future requests.

### Step 3: Ask First Question
```bash
curl -X POST "https://api.example.com/api/v1/analyses/123/followup/456/ask" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does my heart line reveal about my emotional nature?"
  }'
```

AI provides detailed response with visual analysis of your palm.

### Step 4: Ask Follow-up Question with Context
```bash
curl -X POST "https://api.example.com/api/v1/analyses/123/followup/456/ask" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does the mount of Venus relate to what you mentioned about my heart line?"
  }'
```

AI provides context-aware response building on the previous answer.

### Step 5: View Conversation History
```bash
curl -X GET "https://api.example.com/api/v1/analyses/123/followup/456/history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Returns complete conversation history with all Q&A pairs.

---

## Error Handling

### Common Error Responses

**400 Bad Request - Invalid Question:**
```json
{
  "detail": "Question must be at least 10 characters long"
}
```

**400 Bad Request - Prompt Injection:**
```json
{
  "detail": "Question contains prohibited content. Please ask about palm reading only."
}
```

**400 Bad Request - Non-Palmistry:**
```json
{
  "detail": "Please ask questions related to palm reading and palmistry."
}
```

**429 Too Many Requests - Question Limit:**
```json
{
  "detail": "Maximum 5 questions allowed per analysis"
}
```

**404 Not Found - Analysis:**
```json
{
  "detail": "Analysis not found, not owned by user, or not completed"
}
```

**404 Not Found - Conversation:**
```json
{
  "detail": "Follow-up conversation not found or not accessible"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to process question"
}
```

### Error Handling Best Practices

1. **Check Status First:** Always check follow-up status before attempting operations
2. **Handle Rate Limits:** Implement proper error handling for question limits
3. **Validate Locally:** Pre-validate questions on the frontend to reduce API calls
4. **Retry Logic:** Implement exponential backoff for 500 errors
5. **User Feedback:** Provide clear error messages to users based on API responses

---

## Security Considerations

### Content Validation
- All questions are validated for prompt injection attempts
- Only palmistry-related content is allowed
- Medical, legal, and financial advice requests are blocked
- Specific future predictions are discouraged

### Authentication & Authorization
- JWT token required for all endpoints
- Users can only access their own analyses and conversations
- Analysis ownership is verified for every request

### Rate Limiting
- Question limits prevent abuse (typically 5 questions per analysis)
- API rate limiting prevents excessive requests
- Conversation limits ensure fair resource usage

### Data Privacy
- Palm images are uploaded to OpenAI with appropriate security
- Conversation data is associated with user accounts
- Analysis context is cached securely for performance

---

## Performance Guidelines

### Response Time Targets
- **Status Check:** < 500ms
- **Conversation Creation:** < 3s (includes file upload)
- **Question Processing:** < 2s (includes AI response)
- **History Retrieval:** < 500ms

### Optimization Tips
1. **Cache Status:** Cache follow-up status on frontend to reduce API calls
2. **Preload Conversations:** Create conversations when users show interest
3. **Batch History:** Load conversation history in chunks for large conversations
4. **Monitor Usage:** Track token usage and costs for billing purposes
5. **Handle Concurrency:** Implement proper loading states for AI processing

### Token Usage
- Typical question: 150-300 tokens
- Cost per question: $0.005-$0.015
- Context overhead: 50-100 tokens per question
- Image processing: Additional 200-400 tokens per image

---

## Integration Examples

### JavaScript/TypeScript
```typescript
class FollowupAPI {
  private baseURL = 'https://api.example.com/api/v1';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  async getFollowupStatus(analysisId: number): Promise<FollowupStatusResponse> {
    const response = await fetch(`${this.baseURL}/analyses/${analysisId}/followup/status`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    return response.json();
  }

  async startConversation(analysisId: number): Promise<FollowupConversationResponse> {
    const response = await fetch(`${this.baseURL}/analyses/${analysisId}/followup/start`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    return response.json();
  }

  async askQuestion(
    analysisId: number, 
    conversationId: number, 
    question: string
  ): Promise<FollowupQuestionResponse> {
    const response = await fetch(
      `${this.baseURL}/analyses/${analysisId}/followup/${conversationId}/ask`, 
      {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question })
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    return response.json();
  }
}

// Usage example
const api = new FollowupAPI('your-jwt-token');

try {
  // Check if follow-up is available
  const status = await api.getFollowupStatus(123);
  
  if (status.followup_available && !status.followup_conversation_exists) {
    // Start a new conversation
    const conversation = await api.startConversation(123);
    console.log(`Started conversation ${conversation.id}`);
    
    // Ask a question
    const result = await api.askQuestion(123, conversation.id, 
      "What does my heart line reveal about my emotional nature?"
    );
    
    console.log('AI Response:', result.assistant_message.content);
    console.log('Questions remaining:', result.questions_remaining);
    console.log('Cost:', result.cost);
  }
} catch (error) {
  console.error('Follow-up API error:', error);
}
```

### Python
```python
import requests
from typing import Dict, Any, Optional

class FollowupAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def get_followup_status(self, analysis_id: int) -> Dict[str, Any]:
        """Check follow-up availability and status."""
        response = self.session.get(f'{self.base_url}/analyses/{analysis_id}/followup/status')
        response.raise_for_status()
        return response.json()

    def start_conversation(self, analysis_id: int) -> Dict[str, Any]:
        """Start a new follow-up conversation."""
        response = self.session.post(f'{self.base_url}/analyses/{analysis_id}/followup/start')
        response.raise_for_status()
        return response.json()

    def ask_question(self, analysis_id: int, conversation_id: int, question: str) -> Dict[str, Any]:
        """Ask a follow-up question."""
        response = self.session.post(
            f'{self.base_url}/analyses/{analysis_id}/followup/{conversation_id}/ask',
            json={'question': question}
        )
        response.raise_for_status()
        return response.json()

    def get_history(self, analysis_id: int, conversation_id: int, limit: int = 20) -> Dict[str, Any]:
        """Get conversation history."""
        response = self.session.get(
            f'{self.base_url}/analyses/{analysis_id}/followup/{conversation_id}/history',
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json()

# Usage example
api = FollowupAPI('https://api.example.com/api/v1', 'your-jwt-token')

try:
    # Check status
    status = api.get_followup_status(123)
    print(f"Follow-up available: {status['followup_available']}")
    
    if status['followup_available'] and not status['followup_conversation_exists']:
        # Start conversation
        conversation = api.start_conversation(123)
        conversation_id = conversation['id']
        print(f"Started conversation {conversation_id}")
        
        # Ask questions
        questions = [
            "What does my heart line reveal about my emotional nature?",
            "How do the mounts on my palm relate to my personality?",
            "What does the depth of my life line indicate?"
        ]
        
        for question in questions:
            result = api.ask_question(123, conversation_id, question)
            print(f"\nQ: {question}")
            print(f"A: {result['assistant_message']['content'][:100]}...")
            print(f"Questions remaining: {result['questions_remaining']}")
            print(f"Cost: ${result['cost']:.4f}")
        
        # Get full history
        history = api.get_history(123, conversation_id)
        print(f"\nTotal messages in conversation: {len(history['messages'])}")

except requests.RequestException as e:
    print(f"API Error: {e}")
```

---

## Testing and Development

### Test Endpoints
Use the test environment for development:
- Base URL: `https://api-test.example.com/api/v1`
- Test analyses with IDs 1-10 are available
- Test conversations reset daily
- No actual costs incurred

### Mock Responses
For frontend development, you can use these mock responses:

```json
// Mock Status Response
{
  "analysis_id": 123,
  "analysis_completed": true,
  "followup_available": true,
  "followup_conversation_exists": false,
  "conversation_id": null,
  "questions_asked": 0,
  "questions_remaining": 5,
  "max_questions": 5,
  "has_openai_files": false,
  "total_followup_questions": 0
}

// Mock Question Response
{
  "user_message": {
    "id": 101,
    "conversation_id": 456,
    "message_type": "USER",
    "content": "What does my heart line reveal?",
    "created_at": "2025-08-30T10:45:00Z"
  },
  "assistant_message": {
    "id": 102,
    "conversation_id": 456,
    "message_type": "ASSISTANT",
    "content": "Your heart line shows strong emotional characteristics...",
    "tokens_used": 150,
    "cost": 0.0045,
    "processing_time": 1.8,
    "created_at": "2025-08-30T10:45:02Z"
  },
  "questions_remaining": 4,
  "tokens_used": 150,
  "cost": 0.0045,
  "processing_time": 1.8
}
```

---

## Support and Resources

### Documentation
- [API Reference](./api-reference.md)
- [Authentication Guide](./authentication.md)
- [Error Codes](./error-codes.md)
- [Rate Limiting](./rate-limiting.md)

### Support Channels
- Technical Issues: support@example.com
- API Documentation: docs@example.com
- Feature Requests: features@example.com

### Monitoring
- API Status: https://status.example.com
- Performance Metrics: Available in dashboard
- Usage Analytics: Track via API responses

---

*Last Updated: August 30, 2025*
*API Version: 1.0*