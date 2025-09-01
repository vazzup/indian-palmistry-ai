# Frontend Technical Specification - Analysis Follow-up Questions

## Overview

This document provides detailed technical specifications for frontend implementation of the Analysis Follow-up Questions feature. The frontend team will implement the follow-up questions interface, integration with existing analysis pages, state management, and mobile-responsive design.

## Component Architecture

### 1. Core Components Structure

```
src/components/analysis/
├── FollowupQuestions/
│   ├── FollowupCTA.tsx              # Call-to-action on analysis results
│   ├── FollowupInterface.tsx        # Main follow-up questions interface
│   ├── QuestionInput.tsx            # Question input with validation
│   ├── QuestionHistory.tsx          # Display previous Q&A pairs
│   ├── QuestionLimitIndicator.tsx   # Show remaining questions
│   └── FollowupLoading.tsx          # Loading states for AI responses
├── AnalysisResults.tsx              # Enhanced with follow-up CTA
└── AnalysisPage.tsx                 # Main analysis page updates
```

### 2. State Management

```typescript
// Add to existing Zustand store or create new follow-up store
interface FollowupStore {
  // State
  followupStatus: FollowupStatus | null
  currentConversation: FollowupConversation | null
  questions: QuestionAnswer[]
  isLoading: boolean
  isSubmitting: boolean
  error: string | null
  
  // Actions
  checkFollowupStatus: (analysisId: number) => Promise<void>
  startFollowupConversation: (analysisId: number) => Promise<void>
  askQuestion: (conversationId: number, question: string) => Promise<void>
  loadQuestions: (conversationId: number) => Promise<void>
  resetFollowup: () => void
  clearError: () => void
}

// Types
interface FollowupStatus {
  analysisCompleted: boolean
  followupAvailable: boolean
  followupConversationExists: boolean
  questionsAsked: number
  questionsRemaining: number
  conversationId?: number
}

interface FollowupConversation {
  id: number
  analysisId: number
  title: string
  questionsCount: number
  maxQuestions: number
  createdAt: string
}

interface QuestionAnswer {
  id: string
  question: string
  answer: string
  timestamp: string
  tokensUsed: number
}
```

## Component Implementation Details

### 1. FollowupCTA Component

```typescript
// src/components/analysis/FollowupQuestions/FollowupCTA.tsx
'use client'

import React from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { MessageCircle, ArrowRight } from 'lucide-react'
import { useFollowupStore } from '@/lib/stores/followupStore'

interface FollowupCTAProps {
  analysisId: number
  onStartFollowup: () => void
}

export function FollowupCTA({ analysisId, onStartFollowup }: FollowupCTAProps) {
  const { followupStatus, isLoading, checkFollowupStatus } = useFollowupStore()

  React.useEffect(() => {
    checkFollowupStatus(analysisId)
  }, [analysisId, checkFollowupStatus])

  if (!followupStatus?.followupAvailable || isLoading) {
    return null
  }

  return (
    <Card className="mt-8 p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-indigo-100 rounded-full">
          <MessageCircle className="w-6 h-6 text-indigo-600" />
        </div>
        
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Have questions about your palm reading?
          </h3>
          <p className="text-gray-600 text-sm">
            Ask up to 5 personalized questions about your specific palm features and get detailed answers.
          </p>
        </div>
        
        <Button 
          onClick={onStartFollowup}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors"
        >
          Ask Questions
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
      
      {followupStatus.followupConversationExists && (
        <div className="mt-4 pt-4 border-t border-indigo-200">
          <div className="flex items-center justify-between text-sm text-indigo-700">
            <span>Questions asked: {followupStatus.questionsAsked}/5</span>
            <span>{followupStatus.questionsRemaining} remaining</span>
          </div>
          <div className="w-full bg-indigo-200 rounded-full h-2 mt-2">
            <div 
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(followupStatus.questionsAsked / 5) * 100}%` }}
            />
          </div>
        </div>
      )}
    </Card>
  )
}
```

### 2. FollowupInterface Component

```typescript
// src/components/analysis/FollowupQuestions/FollowupInterface.tsx
'use client'

import React from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeft, MessageCircle } from 'lucide-react'
import { QuestionInput } from './QuestionInput'
import { QuestionHistory } from './QuestionHistory'
import { QuestionLimitIndicator } from './QuestionLimitIndicator'
import { FollowupLoading } from './FollowupLoading'
import { useFollowupStore } from '@/lib/stores/followupStore'

interface FollowupInterfaceProps {
  analysisId: number
  onBack: () => void
}

export function FollowupInterface({ analysisId, onBack }: FollowupInterfaceProps) {
  const {
    currentConversation,
    questions,
    isLoading,
    isSubmitting,
    error,
    startFollowupConversation,
    askQuestion,
    loadQuestions,
    clearError
  } = useFollowupStore()

  React.useEffect(() => {
    const initializeFollowup = async () => {
      if (!currentConversation) {
        await startFollowupConversation(analysisId)
      }
    }
    
    initializeFollowup()
  }, [analysisId, currentConversation, startFollowupConversation])

  React.useEffect(() => {
    if (currentConversation?.id) {
      loadQuestions(currentConversation.id)
    }
  }, [currentConversation?.id, loadQuestions])

  const handleQuestionSubmit = async (question: string) => {
    if (currentConversation?.id) {
      await askQuestion(currentConversation.id, question)
    }
  }

  const canAskMoreQuestions = currentConversation 
    ? currentConversation.questionsCount < currentConversation.maxQuestions
    : false

  if (isLoading && !currentConversation) {
    return (
      <Card className="p-8">
        <FollowupLoading message="Setting up your follow-up conversation..." />
      </Card>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="outline" 
          onClick={onBack}
          className="p-2"
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <MessageCircle className="w-6 h-6 text-indigo-600" />
            Questions about your palm reading
          </h1>
          <p className="text-gray-600 mt-1">
            Ask specific questions about your palm features and get personalized answers
          </p>
        </div>
        
        {currentConversation && (
          <QuestionLimitIndicator 
            used={currentConversation.questionsCount}
            total={currentConversation.maxQuestions}
          />
        )}
      </div>

      {/* Error Display */}
      {error && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="flex items-center justify-between">
            <p className="text-red-800 text-sm">{error}</p>
            <Button variant="ghost" size="sm" onClick={clearError}>
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      {/* Question History */}
      {questions.length > 0 && (
        <QuestionHistory questions={questions} />
      )}

      {/* Question Input */}
      {canAskMoreQuestions ? (
        <QuestionInput 
          onSubmit={handleQuestionSubmit}
          isSubmitting={isSubmitting}
          remainingQuestions={currentConversation.maxQuestions - currentConversation.questionsCount}
        />
      ) : (
        <Card className="p-6 text-center bg-gray-50 border-gray-200">
          <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            All questions used
          </h3>
          <p className="text-gray-600">
            You've asked all 5 questions for this palm reading. You can review your questions and answers above.
          </p>
        </Card>
      )}
    </div>
  )
}
```

### 3. QuestionInput Component

```typescript
// src/components/analysis/FollowupQuestions/QuestionInput.tsx
'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Send, AlertCircle } from 'lucide-react'
import { FollowupLoading } from './FollowupLoading'

interface QuestionInputProps {
  onSubmit: (question: string) => Promise<void>
  isSubmitting: boolean
  remainingQuestions: number
}

export function QuestionInput({ onSubmit, isSubmitting, remainingQuestions }: QuestionInputProps) {
  const [question, setQuestion] = useState('')
  const [validationError, setValidationError] = useState('')

  const validateQuestion = (text: string): string | null => {
    if (text.length < 10) {
      return 'Question must be at least 10 characters long'
    }
    if (text.length > 500) {
      return 'Question must be less than 500 characters'
    }
    
    // Check for palmistry relevance
    const palmistryTerms = ['palm', 'hand', 'finger', 'thumb', 'line', 'mount', 'reading']
    const hasRelevantTerm = palmistryTerms.some(term => 
      text.toLowerCase().includes(term)
    )
    
    if (!hasRelevantTerm) {
      return 'Question must be about palm reading or palmistry'
    }
    
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const validation = validateQuestion(question.trim())
    if (validation) {
      setValidationError(validation)
      return
    }
    
    setValidationError('')
    await onSubmit(question.trim())
    setQuestion('')
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value)
    if (validationError) {
      setValidationError('')
    }
  }

  if (isSubmitting) {
    return (
      <Card className="p-6">
        <FollowupLoading message="Getting your personalized answer..." />
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
            Ask your question ({remainingQuestions} remaining)
          </label>
          
          <textarea
            id="question"
            value={question}
            onChange={handleInputChange}
            placeholder="What would you like to know about your palm reading? For example: 'What does the curve in my life line mean?' or 'Can you explain the lines on my mount of Venus?'"
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            rows={4}
            maxLength={500}
            disabled={isSubmitting}
          />
          
          <div className="flex items-center justify-between mt-2">
            <div className="text-sm text-gray-500">
              {question.length}/500 characters
              {question.length >= 10 && (
                <span className="text-green-600 ml-2">✓ Minimum length reached</span>
              )}
            </div>
          </div>
        </div>

        {validationError && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-red-800 text-sm">{validationError}</span>
          </div>
        )}

        <Button
          type="submit"
          disabled={question.length < 10 || isSubmitting}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
          Ask Question
        </Button>
      </form>
      
      <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
        <p className="text-indigo-800 text-sm">
          💡 <strong>Tip:</strong> Ask specific questions about features you can see in your palm images for the most accurate answers.
        </p>
      </div>
    </Card>
  )
}
```

### 4. QuestionHistory Component

```typescript
// src/components/analysis/FollowupQuestions/QuestionHistory.tsx
'use client'

import React from 'react'
import { Card } from '@/components/ui/Card'
import { MessageCircle, Clock, Zap } from 'lucide-react'
import type { QuestionAnswer } from '@/lib/stores/followupStore'

interface QuestionHistoryProps {
  questions: QuestionAnswer[]
}

export function QuestionHistory({ questions }: QuestionHistoryProps) {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-6">
        <MessageCircle className="w-5 h-5 text-indigo-600" />
        <h2 className="text-lg font-semibold text-gray-900">
          Your Questions & Answers
        </h2>
      </div>
      
      <div className="space-y-6">
        {questions.map((qa, index) => (
          <div key={qa.id} className="border-l-4 border-indigo-200 pl-6 relative">
            {/* Question Number Badge */}
            <div className="absolute -left-3 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              {index + 1}
            </div>
            
            {/* Question */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-indigo-600">Your Question</span>
                <Clock className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-500">
                  {new Date(qa.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-gray-900 bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                {qa.question}
              </p>
            </div>
            
            {/* Answer */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-green-600">AI Response</span>
                <Zap className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-500">
                  {qa.tokensUsed} tokens used
                </span>
              </div>
              <div className="text-gray-800 bg-green-50 p-4 rounded-lg border border-green-100 leading-relaxed whitespace-pre-wrap">
                {qa.answer}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
```

### 5. State Management Implementation

```typescript
// src/lib/stores/followupStore.ts
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { api } from '@/lib/api'

interface FollowupStatus {
  analysisCompleted: boolean
  followupAvailable: boolean
  followupConversationExists: boolean
  questionsAsked: number
  questionsRemaining: number
  conversationId?: number
}

interface FollowupConversation {
  id: number
  analysisId: number
  title: string
  questionsCount: number
  maxQuestions: number
  createdAt: string
}

interface QuestionAnswer {
  id: string
  question: string
  answer: string
  timestamp: string
  tokensUsed: number
}

interface FollowupStore {
  // State
  followupStatus: FollowupStatus | null
  currentConversation: FollowupConversation | null
  questions: QuestionAnswer[]
  isLoading: boolean
  isSubmitting: boolean
  error: string | null
  
  // Actions
  checkFollowupStatus: (analysisId: number) => Promise<void>
  startFollowupConversation: (analysisId: number) => Promise<void>
  askQuestion: (conversationId: number, question: string) => Promise<void>
  loadQuestions: (conversationId: number) => Promise<void>
  resetFollowup: () => void
  clearError: () => void
}

export const useFollowupStore = create<FollowupStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      followupStatus: null,
      currentConversation: null,
      questions: [],
      isLoading: false,
      isSubmitting: false,
      error: null,
      
      // Actions
      checkFollowupStatus: async (analysisId: number) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await api.get(`/analyses/${analysisId}/followup/status`)
          
          set({ 
            followupStatus: response.data,
            isLoading: false
          })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to check follow-up status',
            isLoading: false
          })
        }
      },
      
      startFollowupConversation: async (analysisId: number) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await api.post(`/analyses/${analysisId}/followup/start`)
          
          set({ 
            currentConversation: response.data,
            isLoading: false
          })
          
          // Update status
          get().checkFollowupStatus(analysisId)
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to start follow-up conversation',
            isLoading: false
          })
        }
      },
      
      askQuestion: async (conversationId: number, question: string) => {
        try {
          set({ isSubmitting: true, error: null })
          
          const response = await api.post(
            `/analyses/${get().currentConversation?.analysisId}/followup/${conversationId}/ask`,
            { question }
          )
          
          const { user_message, assistant_message, questions_remaining } = response.data
          
          // Add new Q&A to history
          const newQA: QuestionAnswer = {
            id: `${user_message.id}-${assistant_message.id}`,
            question: user_message.content,
            answer: assistant_message.content,
            timestamp: user_message.created_at,
            tokensUsed: assistant_message.tokens_used || 0
          }
          
          set(state => ({
            questions: [...state.questions, newQA],
            currentConversation: state.currentConversation ? {
              ...state.currentConversation,
              questionsCount: state.currentConversation.questionsCount + 1
            } : null,
            isSubmitting: false
          }))
          
          // Update status
          if (get().currentConversation?.analysisId) {
            get().checkFollowupStatus(get().currentConversation!.analysisId)
          }
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to process question',
            isSubmitting: false
          })
        }
      },
      
      loadQuestions: async (conversationId: number) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await api.get(
            `/analyses/${get().currentConversation?.analysisId}/conversations/${conversationId}/messages`
          )
          
          const messages = response.data.messages
          const questions: QuestionAnswer[] = []
          
          // Pair user and assistant messages
          for (let i = 0; i < messages.length; i += 2) {
            if (i + 1 < messages.length) {
              const userMessage = messages[i]
              const assistantMessage = messages[i + 1]
              
              questions.push({
                id: `${userMessage.id}-${assistantMessage.id}`,
                question: userMessage.content,
                answer: assistantMessage.content,
                timestamp: userMessage.created_at,
                tokensUsed: assistantMessage.tokens_used || 0
              })
            }
          }
          
          set({ 
            questions,
            isLoading: false
          })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to load questions',
            isLoading: false
          })
        }
      },
      
      resetFollowup: () => {
        set({
          followupStatus: null,
          currentConversation: null,
          questions: [],
          isLoading: false,
          isSubmitting: false,
          error: null
        })
      },
      
      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'followup-store'
    }
  )
)
```

## Integration with Existing Pages

### 1. Analysis Results Page Enhancement

```typescript
// Enhance existing src/app/(public)/analysis/[id]/page.tsx
'use client'

import React, { useState } from 'react'
import { FollowupCTA } from '@/components/analysis/FollowupQuestions/FollowupCTA'
import { FollowupInterface } from '@/components/analysis/FollowupQuestions/FollowupInterface'
// ... other imports

export default function AnalysisPage({ params }: { params: { id: string } }) {
  const [showFollowup, setShowFollowup] = useState(false)
  const analysisId = parseInt(params.id)
  
  // ... existing code for loading analysis data
  
  if (showFollowup) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <FollowupInterface 
          analysisId={analysisId}
          onBack={() => setShowFollowup(false)}
        />
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      {/* Existing analysis results display */}
      
      {/* Add Follow-up CTA at the bottom */}
      <FollowupCTA 
        analysisId={analysisId}
        onStartFollowup={() => setShowFollowup(true)}
      />
    </div>
  )
}
```

### 2. Mobile Responsiveness

```css
/* Add to globals.css or component-specific CSS */

/* Follow-up interface mobile styles */
@media (max-width: 768px) {
  .followup-interface {
    padding: 1rem;
  }
  
  .question-input textarea {
    min-height: 120px;
    font-size: 16px; /* Prevent zoom on iOS */
  }
  
  .question-history {
    border-left-width: 2px;
    padding-left: 1rem;
  }
  
  .question-number-badge {
    width: 1.5rem;
    height: 1.5rem;
    left: -0.75rem;
    font-size: 0.75rem;
  }
  
  .followup-cta {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .followup-cta .cta-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .followup-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .question-limit-indicator {
    width: 100%;
  }
}
```

## Testing Requirements

### Unit Tests

```typescript
// __tests__/components/FollowupQuestions/FollowupCTA.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FollowupCTA } from '@/components/analysis/FollowupQuestions/FollowupCTA'
import { useFollowupStore } from '@/lib/stores/followupStore'

// Mock the store
jest.mock('@/lib/stores/followupStore')

describe('FollowupCTA', () => {
  const mockOnStartFollowup = jest.fn()
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('renders CTA when followup is available', () => {
    (useFollowupStore as jest.Mock).mockReturnValue({
      followupStatus: {
        followupAvailable: true,
        followupConversationExists: false,
        questionsAsked: 0,
        questionsRemaining: 5
      },
      isLoading: false,
      checkFollowupStatus: jest.fn()
    })
    
    render(<FollowupCTA analysisId={1} onStartFollowup={mockOnStartFollowup} />)
    
    expect(screen.getByText('Have questions about your palm reading?')).toBeInTheDocument()
    expect(screen.getByText('Ask Questions')).toBeInTheDocument()
  })
  
  it('calls onStartFollowup when button clicked', () => {
    (useFollowupStore as jest.Mock).mockReturnValue({
      followupStatus: {
        followupAvailable: true,
        followupConversationExists: false
      },
      isLoading: false,
      checkFollowupStatus: jest.fn()
    })
    
    render(<FollowupCTA analysisId={1} onStartFollowup={mockOnStartFollowup} />)
    
    fireEvent.click(screen.getByText('Ask Questions'))
    
    expect(mockOnStartFollowup).toHaveBeenCalled()
  })
  
  it('shows progress bar when conversation exists', () => {
    (useFollowupStore as jest.Mock).mockReturnValue({
      followupStatus: {
        followupAvailable: true,
        followupConversationExists: true,
        questionsAsked: 2,
        questionsRemaining: 3
      },
      isLoading: false,
      checkFollowupStatus: jest.fn()
    })
    
    render(<FollowupCTA analysisId={1} onStartFollowup={mockOnStartFollowup} />)
    
    expect(screen.getByText('Questions asked: 2/5')).toBeInTheDocument()
    expect(screen.getByText('3 remaining')).toBeInTheDocument()
  })
})
```

### Integration Tests

```typescript
// __tests__/integration/followup-flow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FollowupInterface } from '@/components/analysis/FollowupQuestions/FollowupInterface'
import { api } from '@/lib/api'

// Mock API
jest.mock('@/lib/api')

describe('Follow-up Questions Flow', () => {
  it('completes full question flow', async () => {
    const user = userEvent.setup()
    
    // Mock API responses
    (api.post as jest.Mock)
      .mockResolvedValueOnce({
        data: {
          id: 1,
          analysisId: 1,
          questionsCount: 0,
          maxQuestions: 5
        }
      })
      .mockResolvedValueOnce({
        data: {
          user_message: {
            id: 1,
            content: 'What does my heart line mean?',
            created_at: '2024-01-01T10:00:00Z'
          },
          assistant_message: {
            id: 2,
            content: 'Your heart line indicates...',
            created_at: '2024-01-01T10:00:01Z',
            tokens_used: 150
          },
          questions_remaining: 4
        }
      })
    
    render(<FollowupInterface analysisId={1} onBack={jest.fn()} />)
    
    // Wait for initialization
    await waitFor(() => {
      expect(screen.getByText(/Ask your question/)).toBeInTheDocument()
    })
    
    // Type a question
    const textarea = screen.getByPlaceholderText(/What would you like to know/)
    await user.type(textarea, 'What does my heart line mean?')
    
    // Submit question
    await user.click(screen.getByText('Ask Question'))
    
    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('What does my heart line mean?')).toBeInTheDocument()
      expect(screen.getByText('Your heart line indicates...')).toBeInTheDocument()
    })
  })
})
```

## Performance Optimization

### 1. Component Optimization

```typescript
// Use React.memo for heavy components
export const QuestionHistory = React.memo(({ questions }: QuestionHistoryProps) => {
  return (
    // Component implementation
  )
})

// Use useMemo for expensive calculations
const questionStats = React.useMemo(() => {
  return {
    totalTokens: questions.reduce((sum, q) => sum + q.tokensUsed, 0),
    avgResponseTime: questions.length > 0 ? 
      questions.reduce((sum, q) => sum + q.responseTime, 0) / questions.length : 0
  }
}, [questions])
```

### 2. State Management Optimization

```typescript
// Implement selector pattern for specific state slices
const useFollowupStatus = () => useFollowupStore(state => state.followupStatus)
const useQuestions = () => useFollowupStore(state => state.questions)
const useFollowupActions = () => useFollowupStore(state => ({
  checkFollowupStatus: state.checkFollowupStatus,
  askQuestion: state.askQuestion,
  startFollowupConversation: state.startFollowupConversation
}))
```

## Deployment Checklist

### Pre-deployment
- [ ] All components implemented and tested
- [ ] Mobile responsiveness verified
- [ ] State management working correctly
- [ ] Integration with existing pages complete
- [ ] Error handling implemented
- [ ] Loading states designed and working
- [ ] Accessibility features added (ARIA labels, keyboard navigation)

### Testing
- [ ] Unit tests pass (90%+ coverage)
- [ ] Integration tests pass
- [ ] Mobile device testing complete
- [ ] Cross-browser testing complete
- [ ] Performance testing (loading times, responsiveness)
- [ ] User acceptance testing

### Monitoring
- [ ] Analytics tracking for feature usage
- [ ] Error boundary implementation
- [ ] Performance monitoring setup
- [ ] User feedback collection mechanism

This comprehensive frontend technical specification provides the development team with detailed implementation guidance for creating an intuitive and performant follow-up questions interface that integrates seamlessly with the existing application.