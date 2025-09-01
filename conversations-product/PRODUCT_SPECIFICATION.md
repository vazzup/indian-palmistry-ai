# Analysis Follow-up Questions - Product Specification

## Executive Summary

This specification defines the implementation of Analysis Follow-up Questions, a strategic feature that unifies palm reading analyses with contextual conversations. This feature transforms our linear palm reading experience into an interactive, educational journey where users can ask up to 5 follow-up questions about their specific palm reading, with AI responses that maintain full context of their original palm images and conversation history.

## Current State Analysis

### Existing Architecture
- **Analysis Flow**: Upload → Processing → Complete reading → End
- **Conversation System**: Exists independently, not connected to analyses
- **Technology Stack**: 
  - Backend: FastAPI + PostgreSQL + Redis + OpenAI API
  - Frontend: Next.js 15 + TypeScript + Zustand
  - Authentication: Session-based with Redis
  - Job Processing: Celery for background analysis tasks

### Current Limitations
1. Users cannot ask clarifying questions about their specific reading
2. Conversation system exists but lacks analysis context
3. Palm images are not referenced in follow-up discussions
4. No natural progression from analysis to deeper exploration
5. Missing engagement opportunity post-analysis completion

## Feature Vision: Analysis Follow-up Questions

### Core Value Proposition
Transform static palm readings into interactive, educational experiences where users can explore their results through personalized Q&A sessions that maintain full context of their original palm images.

### Success Metrics
- **Engagement**: 40% of completed analyses generate at least 1 follow-up question
- **Retention**: Users with follow-up questions return 3x more frequently
- **Satisfaction**: 90% of users find follow-up responses helpful and contextually accurate
- **Technical**: <2 second response time for follow-up questions
- **Cost Efficiency**: Follow-up questions cost 60% less than full analyses

## User Experience Flow

### Primary User Journey
```
1. User uploads palm images → Starts analysis
2. Analysis completes → User views results
3. At bottom of results: "Ask Follow-up Questions" CTA appears
4. User clicks → Opens follow-up question interface
5. User types question → Submits (up to 5 questions total)
6. AI responds with context from original images + previous Q&A
7. User can ask additional questions (within limit)
8. All Q&A saved as conversation history linked to analysis
```

### User Interface Design

#### Analysis Results Page Enhancement
```
[Existing Analysis Results Display]

┌─────────────────────────────────────────────────┐
│ 📝 Have questions about your palm reading?     │
│                                                 │
│ [Ask Follow-up Questions] (Primary Button)     │
│                                                 │
│ Get personalized answers about your specific   │
│ palm features and reading insights.             │
└─────────────────────────────────────────────────┘
```

#### Follow-up Questions Interface
```
┌─────────────────────────────────────────────────┐
│ Questions about your palm reading (3/5 used)   │
│                                                 │
│ 💬 Previous Questions:                          │
│ Q: What does my heart line mean for love?      │
│ A: Based on your heart line shape...           │
│                                                 │
│ Q: Why is my life line curved?                 │
│ A: The curvature in your life line...          │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Ask your next question... (2 remaining)    │ │
│ │                                             │ │
│ │ [Submit Question]                           │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 🔒 Questions are specific to your palm images  │
└─────────────────────────────────────────────────┘
```

### Question Examples & Use Cases
**Common Follow-up Questions:**
- "What does my heart line shape mean for my love life?"
- "Why does my life line have that curve in the middle?"
- "Can you explain the meaning of those small lines on my mount of Venus?"
- "What do the crosses on my palm indicate about my career?"
- "How does my thumb shape relate to my personality traits?"

## Technical Architecture

### Database Schema Changes

#### Enhanced Conversation Model
```python
class Conversation(Base):
    # Existing fields...
    
    # NEW FIELDS for Analysis Follow-up
    openai_file_ids = Column(JSON, nullable=True)  # Store OpenAI file IDs
    questions_count = Column(Integer, default=0, nullable=False)  # Track question count
    max_questions = Column(Integer, default=5, nullable=False)  # Question limit
    is_analysis_followup = Column(Boolean, default=False, nullable=False)  # Flag for follow-up type
    
    # Enhanced metadata
    analysis_context = Column(JSON, nullable=True)  # Store relevant analysis snippets for context
```

#### Analysis Model Enhancement
```python
class Analysis(Base):
    # Existing fields...
    
    # NEW FIELDS for OpenAI Files API
    openai_file_ids = Column(JSON, nullable=True)  # Store uploaded file IDs for reuse
    has_followup_conversation = Column(Boolean, default=False, nullable=False)  # Quick check
```

### API Architecture

#### New Endpoint Structure
```
POST /api/v1/analyses/{analysis_id}/followup/start
- Creates follow-up conversation
- Uploads palm images to OpenAI Files API
- Returns conversation ID and limits

POST /api/v1/analyses/{analysis_id}/followup/{conversation_id}/ask
- Accepts user question
- Validates question limit
- Generates AI response with image context
- Updates question count

GET /api/v1/analyses/{analysis_id}/followup/{conversation_id}/questions
- Returns all questions and answers
- Paginated response
- Include remaining question count
```

### OpenAI Files API Integration

#### Image Upload Strategy
```python
async def upload_analysis_images_to_openai(analysis_id: int) -> Dict[str, str]:
    """
    Upload palm images to OpenAI Files API for persistent reference.
    Returns mapping of image_type -> file_id
    """
    analysis = await get_analysis_by_id(analysis_id)
    file_ids = {}
    
    # Upload left palm if exists
    if analysis.left_image_path:
        file_id = await openai_client.files.create(
            file=open(analysis.left_image_path, 'rb'),
            purpose='vision'
        )
        file_ids['left_palm'] = file_id.id
    
    # Upload right palm if exists  
    if analysis.right_image_path:
        file_id = await openai_client.files.create(
            file=open(analysis.right_image_path, 'rb'),
            purpose='vision'
        )
        file_ids['right_palm'] = file_id.id
        
    return file_ids
```

#### Context-Aware Question Processing
```python
async def process_followup_question(
    conversation_id: int,
    question: str,
    openai_file_ids: Dict[str, str],
    previous_qa: List[Dict]
) -> str:
    """
    Process follow-up question with full context:
    - Original palm images via Files API
    - Previous Q&A history
    - Original analysis summary
    """
    
    # Build context from previous Q&A
    conversation_context = build_qa_context(previous_qa)
    
    # Create message with image references
    messages = [
        {
            "role": "system",
            "content": FOLLOWUP_SYSTEM_PROMPT
        },
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": f"Original analysis context: {analysis.summary}"},
                {"type": "text", "text": f"Previous questions: {conversation_context}"},
                {"type": "text", "text": f"New question: {question}"},
                {"type": "image", "image_url": {"file_id": openai_file_ids['left_palm']}},
                {"type": "image", "image_url": {"file_id": openai_file_ids['right_palm']}}
            ]
        }
    ]
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

### Security & Validation

#### Prompt Injection Prevention
```python
SECURITY_FILTERS = {
    "forbidden_topics": [
        "medical advice", "health diagnosis", "future prediction",
        "system instructions", "ignore previous", "roleplay as"
    ],
    "required_keywords": [
        "palm", "hand", "line", "mount", "reading", "palmistry"
    ]
}

def validate_followup_question(question: str, analysis_summary: str) -> bool:
    """
    Validate that question is legitimately about palm reading.
    """
    question_lower = question.lower()
    
    # Check for forbidden topics
    for forbidden in SECURITY_FILTERS["forbidden_topics"]:
        if forbidden in question_lower:
            return False
    
    # Ensure palmistry relevance
    palmistry_keywords = ["palm", "hand", "line", "finger", "thumb", "mount"]
    if not any(keyword in question_lower for keyword in palmistry_keywords):
        return False
        
    # Check length limits
    if len(question) > 500 or len(question) < 10:
        return False
        
    return True
```

#### Question Limit Enforcement
```python
async def check_question_limit(conversation_id: int) -> bool:
    """
    Enforce 5-question limit per analysis.
    """
    conversation = await get_conversation_by_id(conversation_id)
    return conversation.questions_count < conversation.max_questions
```

## Implementation Phases

### Phase 1: Backend Foundation (Week 1-2)
**Backend Team Deliverables:**
- [ ] Database migrations for enhanced conversation model
- [ ] OpenAI Files API service integration
- [ ] Follow-up question validation system
- [ ] Basic follow-up endpoints (start, ask, get)
- [ ] Security filters and validation
- [ ] Comprehensive test coverage

**Acceptance Criteria:**
- All API endpoints return proper responses
- OpenAI Files API integration working
- Question limits enforced correctly
- Security validation prevents injection attacks
- 95% test coverage on new code

### Phase 2: Frontend Integration (Week 2-3)
**Frontend Team Deliverables:**
- [ ] "Ask Follow-up Questions" CTA on analysis results
- [ ] Follow-up questions interface component
- [ ] Question/answer display with context
- [ ] Question counter and limit indicators
- [ ] Integration with existing conversation UI
- [ ] Mobile-responsive design

**Acceptance Criteria:**
- Seamless navigation from analysis to follow-up
- Clear question limit communication
- Real-time question counter updates
- Mobile interface works smoothly
- Consistent with existing design system

### Phase 3: Advanced Features (Week 3-4)
**Combined Team Deliverables:**
- [ ] Conversation history page integration
- [ ] Question categorization and suggestions
- [ ] Enhanced error handling and retry logic
- [ ] Performance optimization for image context
- [ ] Analytics tracking for feature usage
- [ ] A/B testing framework for CTA placement

**Acceptance Criteria:**
- Follow-up conversations appear in history
- Suggested questions improve engagement
- Error states handled gracefully
- Response times under 2 seconds
- Analytics data collection working

### Phase 4: Production Optimization (Week 4-5)
**DevOps & Optimization:**
- [ ] Load testing for concurrent follow-up questions
- [ ] OpenAI API rate limiting and error handling
- [ ] File cleanup processes for uploaded images
- [ ] Monitoring and alerting setup
- [ ] Documentation for support team
- [ ] Feature flag implementation

**Acceptance Criteria:**
- System handles 100 concurrent follow-up questions
- Graceful degradation when OpenAI API limits hit
- Automated cleanup of old file uploads
- Comprehensive monitoring in place
- Support documentation complete

## Risk Assessment & Mitigation

### Technical Risks

**Risk 1: OpenAI Files API Failures**
- **Impact**: High - Feature completely broken
- **Probability**: Medium
- **Mitigation**: 
  - Implement retry logic with exponential backoff
  - Fallback to text-only responses if image upload fails
  - Cache file IDs to avoid re-uploads
  - Monitor API status and proactively handle outages

**Risk 2: Prompt Injection Attacks**
- **Impact**: High - Security breach, inappropriate responses
- **Probability**: Medium
- **Mitigation**:
  - Multi-layer validation system
  - Whitelist approach for palmistry terms
  - Content filtering on both input and output
  - Regular security audits and testing

**Risk 3: Cost Escalation from Image Processing**
- **Impact**: Medium - Budget overrun
- **Probability**: High
- **Mitigation**:
  - Implement daily/monthly spending caps
  - Optimize image sizes before upload
  - Cache responses to avoid duplicate processing
  - Monitor costs with automated alerts

### Product Risks

**Risk 4: Low User Adoption**
- **Impact**: Medium - Feature doesn't drive engagement
- **Probability**: Medium
- **Mitigation**:
  - A/B test different CTA placements and messaging
  - Provide suggested questions to guide users
  - Track engagement metrics and iterate quickly
  - User testing before full rollout

**Risk 5: User Confusion About Question Limits**
- **Impact**: Medium - User frustration, support burden
- **Probability**: Low
- **Mitigation**:
  - Clear, prominent question counter display
  - Progressive disclosure of remaining questions
  - Helpful messaging about question limits
  - FAQ section for common questions

## Success Metrics & KPIs

### Engagement Metrics
- **Follow-up Adoption Rate**: 40% target (users who ask ≥1 question per completed analysis)
- **Question Completion Rate**: 60% target (users who use 4-5 of their 5 questions)
- **Average Questions per User**: 3.2 target
- **Time to First Question**: <2 minutes target after analysis completion

### Quality Metrics  
- **Response Relevance Score**: 4.5/5.0 target (user ratings)
- **Context Accuracy**: 90% target (questions properly reference palm images)
- **Security Incident Rate**: 0 target (successful prompt injections)

### Technical Metrics
- **Response Time**: <2 seconds target for follow-up answers
- **API Success Rate**: 99.5% target (successful OpenAI API calls)
- **Error Rate**: <1% target for follow-up question submissions
- **File Upload Success**: 99% target for palm image uploads to OpenAI

### Business Metrics
- **User Retention**: 3x improvement for users with follow-up questions
- **Session Duration**: 40% increase for analyses with follow-up questions
- **Cost per Follow-up**: 60% less than full analysis cost
- **Support Ticket Reduction**: 20% fewer palm reading clarification requests

## Development Team Instructions

### Backend Team Focus Areas
1. **OpenAI Integration**: Prioritize robust Files API integration with proper error handling
2. **Security**: Implement comprehensive prompt injection prevention
3. **Performance**: Optimize for concurrent users and API rate limits
4. **Data Integrity**: Ensure question counts and limits are accurately tracked

### Frontend Team Focus Areas  
1. **User Experience**: Create intuitive flow from analysis to follow-up questions
2. **Visual Design**: Make question interface engaging and easy to use
3. **State Management**: Handle conversation state updates smoothly
4. **Mobile Experience**: Ensure follow-up interface works well on all devices

### Quality Assurance Priorities
1. **Security Testing**: Extensive prompt injection testing
2. **Load Testing**: Verify system handles concurrent follow-up questions
3. **User Acceptance Testing**: Validate complete user journey
4. **Edge Case Testing**: Handle API failures, network issues, limit exceeded scenarios

## Launch Strategy

### Pre-Launch (Week 1-4)
- Complete development phases 1-4
- Internal testing and security review
- Performance testing and optimization
- Support team training

### Soft Launch (Week 5)
- Release to 10% of users via feature flag
- Monitor metrics and gather feedback
- Address any critical issues quickly
- Prepare for full rollout

### Full Launch (Week 6)
- Roll out to all users
- Monitor adoption and engagement metrics
- Collect user feedback and iterate
- Plan next enhancement phase

This comprehensive product specification provides clear direction for implementing the Analysis Follow-up Questions feature while maintaining security, performance, and user experience standards. The phased approach ensures systematic development and testing, while the detailed metrics framework enables data-driven optimization post-launch.