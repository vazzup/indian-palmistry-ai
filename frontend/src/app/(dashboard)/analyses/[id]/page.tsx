'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Hand, 
  ArrowLeft,
  Eye,
  Calendar,
  Clock,
  MessageCircle,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';
import { analysisApi, conversationsApi, handleApiError } from '@/lib/api';
import { LoadingPage } from '@/components/ui/Spinner';
import type { Analysis, Message, TalkResponse, InitialConversationResponse } from '@/types';
import { Input } from '@/components/ui/Input';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { LegalNotice } from '@/components/legal/LegalNotice';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const analysisId = params.id as string;
  
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  
  // Conversation state
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [question, setQuestion] = React.useState('');
  const [isAsking, setIsAsking] = React.useState(false);
  const [isTransitioning, setIsTransitioning] = React.useState(false);
  const [transitionMessage, setTransitionMessage] = React.useState('');
  const [conversationError, setConversationError] = React.useState<string | null>(null);
  const [showFullAnalysisModal, setShowFullAnalysisModal] = React.useState(false);
  
  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  
  React.useEffect(() => {
    console.log('Dashboard page useEffect - authLoading:', authLoading, 'isAuthenticated:', isAuthenticated, 'analysisId:', analysisId);
    
    // Wait for auth to be loaded
    if (authLoading) {
      console.log('Auth still loading, waiting...');
      return;
    }
    
    // Redirect unauthenticated users to summary page
    if (!isAuthenticated) {
      console.log('User not authenticated, redirecting to summary page');
      router.push(`/analysis/${analysisId}/summary`);
      return;
    }

    console.log('User is authenticated, proceeding to fetch analysis');

    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const analysisData = await analysisApi.getAnalysis(analysisId);
        setAnalysis(analysisData);
      } catch (err: any) {
        // Handle 401 errors gracefully - redirect to summary page
        if (err.response?.status === 401) {
          router.push(`/analysis/${analysisId}/summary`);
          return;
        }
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    
    if (analysisId) {
      fetchAnalysis();
    }
  }, [analysisId, isAuthenticated, authLoading, router]);

  // Load conversation messages when analysis is loaded and is in chat mode
  React.useEffect(() => {
    const loadMessages = async () => {
      if (!analysis || !isAuthenticated || analysis.conversation_mode !== 'chat' || !analysis.conversation_id) return;

      try {
        const messageData = await conversationsApi.getConversationMessages(
          analysisId,
          analysis.conversation_id.toString()
        );
        setMessages(messageData.messages || []);
      } catch (error) {
        console.error('Failed to load messages:', error);
        setConversationError('Failed to load conversation messages');
      }
    };

    loadMessages();
  }, [analysis, analysisId, isAuthenticated]);

  const handleAskQuestion = async () => {
    if (!question.trim() || !analysis || isAsking || isTransitioning) return;

    setIsAsking(true);
    setConversationError(null);
    const questionText = question.trim();
    setQuestion(''); // Clear input immediately

    let messageInterval: NodeJS.Timeout | null = null;
    
    try {
      if (analysis.conversation_mode === 'analysis') {
        // FEATURE: Interstitial loading screen for analysis-to-chat transition
        // Shows engaging messages while transitioning from reading view to chat mode
        setIsTransitioning(true);
        
        // Animate through different mystical messages to enhance UX
        const messages = [
          'Preparing your question...',
          'Reading your palms again...',
          'Connecting with ancient wisdom...',
          'Thinking about your question...',
          'Crafting your personalized response...'
        ];
        
        let messageIndex = 0;
        setTransitionMessage(messages[0]);
        
        // Cycle through messages every 1.2 seconds for visual engagement
        messageInterval = setInterval(() => {
          messageIndex = (messageIndex + 1) % messages.length;
          setTransitionMessage(messages[messageIndex]);
        }, 1200);
        
        // Start new conversation with initial reading
        const response: InitialConversationResponse = await conversationsApi.startConversation(
          analysisId,
          questionText
        );
        
        // Update analysis state to reflect new conversation mode
        setAnalysis(prev => prev ? {
          ...prev,
          conversation_mode: 'chat',
          conversation_id: response.conversation.id
        } : null);
        
        // Set all messages from the response
        setMessages([
          response.initial_message,
          response.user_message,
          response.assistant_message
        ]);
      } else if (analysis.conversation_id) {
        // Continue existing conversation
        const response: TalkResponse = await conversationsApi.sendMessage(
          analysisId,
          analysis.conversation_id.toString(),
          questionText
        );
        
        // Add both messages to the list
        setMessages(prev => [...prev, response.user_message, response.assistant_message]);
      }

    } catch (error) {
      console.error('Failed to ask question:', error);
      setConversationError('Failed to get AI response. Please try again.');
      setQuestion(questionText); // Restore question on error
    } finally {
      // Clean up transition interval
      if (messageInterval) {
        clearInterval(messageInterval);
      }
      setIsAsking(false);
      setIsTransitioning(false);
    }
  };

  const handleDeleteAnalysis = async () => {
    console.log('Delete button clicked, analysis:', analysis?.id, 'isDeleting:', isDeleting);
    
    if (!analysis || isDeleting) {
      console.log('Returning early - no analysis or already deleting');
      return;
    }

    console.log('Starting delete process for analysis:', analysisId);
    setIsDeleting(true);
    
    try {
      console.log('Calling deleteAnalysis API...');
      const result = await analysisApi.deleteAnalysis(analysisId);
      console.log('Delete successful:', result);
      
      // Redirect to analyses list after successful deletion
      console.log('Redirecting to /analyses');
      router.push('/analyses');
    } catch (error) {
      console.error('Failed to delete analysis:', error);
      setError('Failed to delete analysis. Please try again.');
    } finally {
      console.log('Cleaning up delete state');
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };
  
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown date';
    }
  };

  /**
   * Gets the user's initial for display in chat avatars
   * Prioritizes name over email, falls back to 'U' if neither available
   */
  const getUserInitial = () => {
    if (!user) return 'U';
    if (user.name) {
      return user.name.charAt(0).toUpperCase();
    }
    if (user.email) {
      return user.email.charAt(0).toUpperCase();
    }
    return 'U';
  };
  
  if (loading || authLoading) {
    return <LoadingPage message={authLoading ? "Checking authentication..." : "Loading your full palm reading..."} />;
  }
  
  if (error || !analysis) {
    return (
      <DashboardLayout
        title="Analysis Not Found"
        description="Unable to load this palm reading"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <Eye className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Analysis Not Found
            </h3>
            <p className="text-gray-600 mb-4">
              {error || 'This palm reading could not be found or you may not have access to it.'}
            </p>
            <Button onClick={() => router.push('/analyses')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to All Readings
            </Button>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title={analysis.conversation_mode === 'chat' ? `Chat about Reading #${analysis.id}` : `Reading #${analysis.id}`}
      description={`Created on ${formatDate(analysis.created_at)}`}
    >
      {/* Interstitial Loading Screen */}
      {isTransitioning && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md mx-4 text-center">
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin mx-auto"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Hand className="w-6 h-6 text-saffron-600" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Pondering your question...
            </h3>
            <p className="text-gray-600 mb-4 min-h-[1.5rem]">
              {transitionMessage}
            </p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}
      
      <div className="space-y-6 h-full">
        {/* 
         * Responsive header with back navigation and delete action
         * Layout adapts for mobile/desktop with text hiding on smaller screens
         */}
        <div className="flex items-center justify-between">
          {/* Back Button - Responsive */}
          <Button
            variant="outline"
            onClick={() => router.push('/analyses')}
            className="flex items-center"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:ml-2 sm:inline">Back to Readings</span>
            <span className="ml-1 sm:hidden">Back</span>
          </Button>
          
          {/* Delete Button - Responsive */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              console.log('Delete button clicked - showing confirmation modal');
              setShowDeleteConfirm(true);
            }}
            className="text-red-600 hover:text-red-700 hover:border-red-300 border-red-200"
            title="Delete Reading"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:ml-2 sm:inline">Delete Reading</span>
            <span className="ml-1 sm:hidden">Delete</span>
          </Button>
        </div>


        {/* Render different content based on conversation mode */}
        {analysis.conversation_mode === 'analysis' ? (
          // Analysis Mode - Show full traditional view with ask question section
          <>
            {/* Analysis Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Hand className="w-5 h-5 text-saffron-600" />
                  Palm Reading Summary
                </CardTitle>
                <CardDescription>
                  Based on traditional Indian palmistry (Hast Rekha Shastra)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-saffron-50 border border-saffron-200 rounded-lg p-4">
                  <p className="text-gray-800 leading-relaxed">
                    {analysis.summary || 'No summary available.'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Full Report */}
            {analysis.full_report && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="w-5 h-5 text-saffron-600" />
                    Detailed Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {analysis.full_report}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Key Features */}
            {analysis.key_features && analysis.key_features.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hand className="w-5 h-5 text-saffron-600" />
                    Key Features Observed
                  </CardTitle>
                  <CardDescription>
                    Notable characteristics found in your palm
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysis.key_features.map((feature, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-saffron-600 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-800 leading-relaxed">{feature}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Strengths */}
            {analysis.strengths && analysis.strengths.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hand className="w-5 h-5 text-emerald-600" />
                    Your Strengths
                  </CardTitle>
                  <CardDescription>
                    Positive traits and characteristics revealed by your palm
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysis.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-emerald-600 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-800 leading-relaxed">{strength}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Guidance */}
            {analysis.guidance && analysis.guidance.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Hand className="w-5 h-5 text-blue-600" />
                    Life Guidance
                  </CardTitle>
                  <CardDescription>
                    Insights and recommendations based on your palm reading
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysis.guidance.map((guide, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-800 leading-relaxed">{guide}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Analysis Metadata */}
            {/*<Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-gray-600">
                  Analysis Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-sm font-medium">Created</p>
                      <p className="text-xs text-gray-600">
                        {formatDate(analysis.created_at)}
                      </p>
                    </div>
                  </div>
                  
                  {analysis.processing_started_at && analysis.processing_completed_at && (
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium">Processing Time</p>
                        <p className="text-xs text-gray-600">
                          {Math.round((new Date(analysis.processing_completed_at).getTime() - 
                                       new Date(analysis.processing_started_at).getTime()) / 1000)} seconds
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>*/}

            {/* Ask Follow-up Question Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-saffron-600" />
                  Ask a follow up question
                </CardTitle>
                <CardDescription>
                  Get personalized insights about your palm reading from our AI expert
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex space-x-2">
                    <Input
                      type="text"
                      placeholder="Type your question here"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleAskQuestion();
                        }
                      }}
                      disabled={isAsking || isTransitioning}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleAskQuestion}
                      disabled={!question.trim() || isAsking || isTransitioning}
                      loading={isAsking || isTransitioning}
                      className="bg-saffron-600 hover:bg-saffron-700 text-white"
                    >
                      Ask Question
                    </Button>
                  </div>
                  
                  {conversationError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-600">{conversationError}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          // Chat Mode - Show conversation interface
          <>
            
            {/* 
             * Enhanced chat interface with modern messaging UI
             * Features: responsive design, proper viewport constraints, and chat bubbles
             * Uses flexbox for proper scrolling behavior in constrained height
             */}
            <Card className="flex flex-col bg-gradient-to-b from-saffron-50/30 to-white h-[calc(100vh-200px)] max-h-[800px]">
              <CardHeader className="border-b border-saffron-100 flex-shrink-0">
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-saffron-600" />
                  Conversation about your Palm Reading
                </CardTitle>
                <CardDescription>
                  Your questions and AI insights about this palm reading
                </CardDescription>
              </CardHeader>
              
              {/* Messages Area - Scrollable */}
              <div className="flex-1 overflow-y-auto">
                <div className="space-y-6 p-6 min-h-0">
                  {messages.length === 0 && !isAsking ? (
                    // Empty state
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-saffron-400 to-saffron-600 flex items-center justify-center mb-4 shadow-lg">
                        <Hand className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Your Palm Reading Conversation</h3>
                      <p className="text-gray-600 text-sm max-w-sm">
                        The conversation will appear here once it begins. Your questions and the AI's mystical insights will be displayed in a flowing dialogue.
                      </p>
                      <div className="mt-4 text-xs text-saffron-600 bg-saffron-50 px-3 py-1 rounded-full">
                        AI responses on the left • Your messages on the right
                      </div>
                    </div>
                  ) : (
                    messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role.toLowerCase() === 'user' ? 'justify-end' : 'justify-start'} group`}
                    >
                      <div className={`flex items-start space-x-3 max-w-[80%] ${
                        message.role.toLowerCase() === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                      }`}>
                        {/* Avatar */}
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          message.role.toLowerCase() === 'user' 
                            ? 'bg-saffron-600 text-white shadow-sm' 
                            : 'bg-gradient-to-br from-saffron-500 to-saffron-600 text-white shadow-md'
                        }`}>
                          {message.role.toLowerCase() === 'user' ? getUserInitial() : <Hand className="w-4 h-4" />}
                        </div>
                        
                        {/* Message content */}
                        <div
                          className={`rounded-2xl px-4 py-3 shadow-sm relative ${
                            message.role.toLowerCase() === 'user'
                              ? 'bg-saffron-600 text-white rounded-tr-sm'
                              : 'bg-white text-gray-900 border border-saffron-100 rounded-tl-sm'
                          }`}
                        >
                          {/* Message tail */}
                          <div className={`absolute top-2 w-3 h-3 ${
                            message.role.toLowerCase() === 'user' 
                              ? 'right-0 translate-x-1/2 rotate-45 bg-saffron-600' 
                              : 'left-0 -translate-x-1/2 rotate-45 bg-white border-l border-t border-saffron-100'
                          }`} />
                          
                          <div className="relative">
                            {message.message_type === 'INITIAL_READING' ? (
                              // Initial reading message with "Read more" link
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-xs font-medium text-saffron-700 bg-saffron-100 px-2 py-1 rounded-full">
                                    Initial Reading
                                  </span>
                                </div>
                                <p className="text-sm leading-relaxed mb-3">
                                  {message.content || analysis.summary || 'Your palm reading analysis is ready.'}
                                </p>
                                <button
                                  onClick={() => setShowFullAnalysisModal(true)}
                                  className="inline-flex items-center text-xs text-saffron-700 hover:text-saffron-800 font-medium transition-colors"
                                >
                                  View Full Analysis →
                                </button>
                              </div>
                            ) : (
                              // MARKDOWN RENDERING: Render markdown for AI messages, plain text for user messages
                              // This solves the issue where AI responses contained raw markdown (### headers, **bold**)
                              // that wasn't being formatted properly, making responses hard to read.
                              message.role.toLowerCase() === 'assistant' ? (
                                <div className="text-sm leading-relaxed">
                                  <ReactMarkdown
                                    remarkPlugins={[remarkGfm]} // GitHub Flavored Markdown support
                                    components={{
                                      // Custom styled headers with hierarchical saffron theming
                                      // H3 gets saffron accent as it's commonly used for section headers
                                      h1: ({children}) => <h1 className="text-base font-bold text-gray-900 mb-2 mt-0">{children}</h1>,
                                      h2: ({children}) => <h2 className="text-sm font-bold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h2>,
                                      h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
                                      h4: ({children}) => <h4 className="text-sm font-semibold text-gray-800 mb-1 mt-2 first:mt-0">{children}</h4>,
                                      // Bold text gets saffron accent for emphasis and cultural consistency
                                      strong: ({children}) => <strong className="font-semibold text-saffron-700">{children}</strong>,
                                      // Lists with proper indentation and spacing for palmistry feature lists
                                      ul: ({children}) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                                      ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                                      li: ({children}) => <li className="text-sm text-gray-800">{children}</li>,
                                      // Paragraphs with consistent spacing, works well with Hindi/English mixed content
                                      p: ({children}) => <p className="text-sm text-gray-800 mb-2 last:mb-0">{children}</p>
                                    }}
                                  >
                                    {message.content}
                                  </ReactMarkdown>
                                </div>
                              ) : (
                                // User messages remain as plain text with whitespace preservation
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                  {message.content}
                                </p>
                              )
                            )}
                            
                            {/* Message metadata */}
                            <div className={`mt-3 pt-2 border-t ${
                              message.role.toLowerCase() === 'user' 
                                ? 'border-saffron-500/30' 
                                : 'border-gray-100'
                            }`}>
                              <p className={`text-xs ${
                                message.role.toLowerCase() === 'user' ? 'text-saffron-200' : 'text-gray-500'
                              }`}>
                                {new Date(message.created_at).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    ))
                  )}
                  
                  {isAsking && (
                    <div className="flex justify-start group">
                      <div className="flex items-start space-x-3 max-w-[80%]">
                        {/* AI Avatar */}
                        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium bg-gradient-to-br from-saffron-500 to-saffron-600 text-white shadow-md">
                          <Hand className="w-4 h-4" />
                        </div>
                        
                        {/* Typing indicator */}
                        <div className="bg-white text-gray-900 border border-saffron-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm relative">
                          <div className="absolute top-2 left-0 -translate-x-1/2 rotate-45 bg-white border-l border-t border-saffron-100 w-3 h-3" />
                          <div className="flex items-center space-x-3">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 bg-saffron-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                            <span className="text-sm text-gray-600">The mystic is contemplating...</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Message Input Area - Fixed at Bottom */}
              <div className="border-t border-saffron-100 bg-white/80 backdrop-blur-sm flex-shrink-0">
                <div className="p-4">
                  <div className="flex space-x-3 items-end">
                    <div className="flex-1 relative">
                      <Input
                        type="text"
                        placeholder="Ask another question about your palm reading..."
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleAskQuestion();
                          }
                        }}
                        disabled={isAsking || isTransitioning}
                        className="border-saffron-200 focus:border-saffron-500 focus:ring-saffron-500 rounded-xl bg-white"
                      />
                    </div>
                    <Button
                      onClick={handleAskQuestion}
                      disabled={!question.trim() || isAsking || isTransitioning}
                      loading={isAsking || isTransitioning}
                      className="bg-saffron-600 hover:bg-saffron-700 text-white rounded-xl px-6 py-2 font-medium"
                    >
                      {isAsking || isTransitioning ? 'Sending...' : 'Send'}
                    </Button>
                  </div>
                  
                  {conversationError && (
                    <div className="p-3 mt-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-600 flex items-center gap-2">
                        <span className="text-red-500">⚠️</span>
                        {conversationError}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </>
        )}

        {/* Full Analysis Modal */}
        {showFullAnalysisModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
              <div className="flex items-center justify-between p-6 border-b">
                <h3 className="text-xl font-semibold text-gray-900">
                  Complete Palm Reading Analysis
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFullAnalysisModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[80vh] space-y-6">
                {/* Summary */}
                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">Summary</h4>
                  <div className="bg-saffron-50 border border-saffron-200 rounded-lg p-4">
                    <p className="text-gray-800 leading-relaxed">
                      {analysis.summary || 'No summary available.'}
                    </p>
                  </div>
                </div>

                {/* Full Report */}
                {analysis.full_report && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Detailed Analysis</h4>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="prose prose-sm max-w-none">
                        <div className="whitespace-pre-wrap text-gray-700">
                          {analysis.full_report}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Key Features */}
                {analysis.key_features && analysis.key_features.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Key Features Observed</h4>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="space-y-3">
                        {analysis.key_features.map((feature, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-saffron-600 rounded-full mt-2 flex-shrink-0"></div>
                            <p className="text-gray-800 leading-relaxed">{feature}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Strengths */}
                {analysis.strengths && analysis.strengths.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Your Strengths</h4>
                    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                      <div className="space-y-3">
                        {analysis.strengths.map((strength, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-emerald-600 rounded-full mt-2 flex-shrink-0"></div>
                            <p className="text-gray-800 leading-relaxed">{strength}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Guidance */}
                {analysis.guidance && analysis.guidance.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-3">Life Guidance</h4>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="space-y-3">
                        {analysis.guidance.map((guide, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                            <p className="text-gray-800 leading-relaxed">{guide}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="p-6 border-t bg-gray-50 flex justify-end">
                <Button
                  onClick={() => setShowFullAnalysisModal(false)}
                  className="bg-saffron-600 hover:bg-saffron-700 text-white"
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Delete Palm Reading
                  </h3>
                  <p className="text-sm text-gray-600">
                    Reading #{analysis.id}
                  </p>
                </div>
              </div>
              
              <p className="text-gray-700 mb-6">
                Are you sure you want to delete this palm reading? This action cannot be undone. 
                All associated conversations and data will be permanently removed.
              </p>
              
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    console.log('Confirmation delete button clicked');
                    handleDeleteAnalysis();
                  }}
                  disabled={isDeleting}
                  loading={isDeleting}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  {isDeleting ? 'Deleting...' : 'Delete Reading'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
