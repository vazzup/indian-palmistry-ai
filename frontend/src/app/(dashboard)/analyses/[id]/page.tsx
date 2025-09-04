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
import type { Analysis, Conversation, Message, TalkResponse } from '@/types';
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
  const [conversation, setConversation] = React.useState<Conversation | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [showConversation, setShowConversation] = React.useState(false);
  const [question, setQuestion] = React.useState('');
  const [isAsking, setIsAsking] = React.useState(false);
  const [conversationError, setConversationError] = React.useState<string | null>(null);
  
  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  
  React.useEffect(() => {
    const fetchAnalysis = async () => {
      // Don't fetch if not authenticated
      if (!isAuthenticated) {
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const analysisData = await analysisApi.getAnalysis(analysisId);
        setAnalysis(analysisData);
      } catch (err: any) {
        // Handle 401 errors gracefully - redirect to homepage
        if (err.response?.status === 401) {
          setError('Please log in to view this analysis');
          router.push('/');
          return;
        }
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    
    // Wait for authentication to be checked before fetching
    if (analysisId && !authLoading) {
      fetchAnalysis();
    }
  }, [analysisId, isAuthenticated, authLoading, router]);

  // Load existing conversation when analysis is loaded
  React.useEffect(() => {
    const loadConversation = async () => {
      if (!analysis || !isAuthenticated) return;

      try {
        const conversationData = await conversationsApi.getAnalysisConversation(analysisId);
        if (conversationData) {
          setConversation(conversationData);
          // Load messages
          const messageData = await conversationsApi.getConversationMessages(
            analysisId,
            conversationData.id.toString()
          );
          setMessages(messageData.messages || []);
        }
      } catch (error) {
        console.error('Failed to load conversation:', error);
        // Don't show error for missing conversation - it's expected for new analyses
      }
    };

    loadConversation();
  }, [analysis, analysisId, isAuthenticated]);

  const handleAskQuestion = async () => {
    if (!question.trim() || !analysis || isAsking) return;

    setIsAsking(true);
    setConversationError(null);
    const questionText = question.trim();
    setQuestion(''); // Clear input immediately

    try {
      let currentConversation = conversation;

      // Create conversation if it doesn't exist
      if (!currentConversation) {
        currentConversation = await conversationsApi.createConversation({
          analysis_id: parseInt(analysisId),
          title: `Questions about Reading #${analysis.id}`
        });
        setConversation(currentConversation);
        setShowConversation(true);
      }

      // Send message and get AI response
      if (!currentConversation) {
        throw new Error("No conversation available");
      }
      
      const response: TalkResponse = await conversationsApi.sendMessage(
        analysisId,
        currentConversation.id.toString(),
        questionText
      );

      // Add both messages to the list
      setMessages(prev => [...prev, response.user_message, response.assistant_message]);
      setShowConversation(true);

    } catch (error) {
      console.error('Failed to ask question:', error);
      setConversationError('Failed to get AI response. Please try again.');
      setQuestion(questionText); // Restore question on error
    } finally {
      setIsAsking(false);
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
      title={`Reading #${analysis.id}`}
      description={`Created on ${formatDate(analysis.created_at)}`}
    >
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
              
              {/*analysis.cost && (
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium">Cost</p>
                    <p className="text-xs text-gray-600">
                      ${analysis.cost.toFixed(4)}
                    </p>
                  </div>
                </div>
              )*/}
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
                  disabled={isAsking}
                  className="flex-1"
                />
                <Button
                  onClick={handleAskQuestion}
                  disabled={!question.trim() || isAsking}
                  loading={isAsking}
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

        {/* Conversation History */}
        {showConversation && messages.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-saffron-600" />
                Conversation
              </CardTitle>
              <CardDescription>
                Your questions and AI responses about this palm reading
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
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
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">
                            {message.content}
                          </p>
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
              
              {/* Additional question input within conversation */}
              {showConversation && (
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
                      disabled={isAsking}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleAskQuestion}
                      disabled={!question.trim() || isAsking}
                      loading={isAsking}
                      size="sm"
                      className="bg-saffron-600 hover:bg-saffron-700 text-white"
                    >
                      Send
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
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
