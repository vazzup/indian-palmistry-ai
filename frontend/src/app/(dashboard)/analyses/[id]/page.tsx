'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Hand, 
  ArrowLeft,
  Eye,
  Calendar,
  Clock,
  DollarSign,
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
import type { Analysis, Conversation, Message, TalkResponse, InitialConversationResponse } from '@/types';
import { Input } from '@/components/ui/Input';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
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
              <div className="w-16 h-16 border-4 border-orange-200 border-t-orange-600 rounded-full animate-spin mx-auto"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl">🪬</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Transitioning to Chat Mode
            </h3>
            <p className="text-gray-600 mb-4 min-h-[1.5rem]">
              {transitionMessage}
            </p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}
      
      <div className="space-y-6">
        {/* Back Button */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => router.push('/analyses')}
            className="flex items-center"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Readings
          </Button>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              Status: 
              <span className={`ml-1 font-medium ${
                analysis.status === 'COMPLETED' ? 'text-green-600' :
                analysis.status === 'PROCESSING' ? 'text-yellow-600' : 
                'text-red-600'
              }`}>
                {analysis.status}
              </span>
            </span>
            
            {/* Delete Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                console.log('Delete button clicked - showing confirmation modal');
                setShowDeleteConfirm(true);
              }}
              className="text-red-600 hover:text-red-700 hover:border-red-300 border-red-200"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Reading
            </Button>
          </div>
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
            <Card>
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
            </Card>

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
            {/* Chat Interface */}
            <Card className="flex-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-saffron-600" />
                  Conversation about your Palm Reading
                </CardTitle>
                <CardDescription>
                  Your questions and AI insights about this palm reading
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-[60vh] overflow-y-auto">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'USER' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-lg p-4 ${
                          message.role === 'USER'
                            ? 'bg-saffron-600 text-white'
                            : 'bg-gray-100 text-gray-900 border'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="flex-1">
                            {message.message_type === 'INITIAL_READING' ? (
                              // Initial reading message with "Read more" link
                              <div>
                                <p className="text-sm leading-relaxed">
                                  {analysis.summary || 'Your palm reading analysis is ready.'}
                                </p>
                                <button
                                  onClick={() => setShowFullAnalysisModal(true)}
                                  className="mt-2 text-xs text-saffron-600 hover:text-saffron-700 underline"
                                >
                                  Read more →
                                </button>
                              </div>
                            ) : (
                              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                {message.content}
                              </p>
                            )}
                            <div className="flex items-center justify-between mt-2">
                              <p className={`text-xs ${
                                message.role === 'USER' ? 'text-saffron-200' : 'text-gray-500'
                              }`}>
                                {new Date(message.created_at).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </p>
                              {message.cost && (
                                <p className={`text-xs ${
                                  message.role === 'USER' ? 'text-saffron-200' : 'text-gray-500'
                                }`}>
                                  ${message.cost.toFixed(3)}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isAsking && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 border rounded-lg p-4">
                        <div className="flex items-center space-x-3">
                          <div className="animate-pulse">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                          </div>
                          <span className="text-sm text-gray-600">AI is thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Message input */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex space-x-2">
                    <Input
                      type="text"
                      placeholder="Ask another question..."
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
                      Send
                    </Button>
                  </div>
                  
                  {conversationError && (
                    <div className="p-3 mt-2 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-600">{conversationError}</p>
                    </div>
                  )}
                </div>
              </CardContent>
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
