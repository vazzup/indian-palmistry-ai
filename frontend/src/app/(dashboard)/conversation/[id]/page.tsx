'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Send,
  Loader2,
  MessageCircle,
  AlertCircle,
  Hand,
  Trash2
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/lib/auth';
import { conversationsApi, handleApiError } from '@/lib/api';
import { LoadingPage } from '@/components/ui/Spinner';
import type { Conversation, Message, TalkResponse } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ConversationPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const conversationId = params.id as string;

  const [conversation, setConversation] = React.useState<Conversation | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [newMessage, setNewMessage] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [isSending, setIsSending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const messagesContainerRef = React.useRef<HTMLDivElement>(null);
  const [shouldScrollToQuestion, setShouldScrollToQuestion] = React.useState(false);
  const [lastQuestionId, setLastQuestionId] = React.useState<number | null>(null);

  // Auto-scroll to show the question near the top after getting AI response
  React.useEffect(() => {
    if (shouldScrollToQuestion && lastQuestionId && messagesContainerRef.current) {
      const questionElement = messagesContainerRef.current.querySelector(`[data-message-id="${lastQuestionId}"]`) as HTMLElement;
      if (questionElement) {
        // Scroll so the question appears near the top with some margin
        const container = messagesContainerRef.current;
        const elementTop = questionElement.offsetTop - container.offsetTop;
        container.scrollTo({
          top: Math.max(0, elementTop - 60), // 60px margin from top
          behavior: 'smooth'
        });
      }
      setShouldScrollToQuestion(false);
      setLastQuestionId(null);
    }
  }, [messages, shouldScrollToQuestion, lastQuestionId]);

  const fetchConversation = React.useCallback(async () => {
    if (!isAuthenticated || authLoading) return;

    try {
      setLoading(true);
      setError(null);

      // Get conversation (using dummy analysis ID since backend ignores it now)
      const conversationResponse = await conversationsApi.getAnalysisConversation('1');
      setConversation(conversationResponse);

      // Get conversation messages
      const messagesResponse = await conversationsApi.getMessages(conversationId);
      setMessages(messagesResponse.messages || []);

    } catch (err) {
      const errorMsg = handleApiError(err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [conversationId, isAuthenticated, authLoading]);

  React.useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  // Handle sending a message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newMessage.trim() || isSending || !conversation) return;

    const messageText = newMessage.trim();
    setNewMessage('');
    setIsSending(true);

    try {
      // Add optimistic user message
      const optimisticUserMessage: Message = {
        id: Date.now(), // Temporary ID
        conversation_id: parseInt(conversationId),
        role: 'USER',
        content: messageText,
        message_type: 'USER_QUESTION',
        created_at: new Date().toISOString(),
        tokens_used: 0,
        cost: 0,
        analysis_data: undefined
      };

      setMessages(prev => [...prev, optimisticUserMessage]);

      // Trigger scroll immediately after user message is added
      setTimeout(() => {
        setLastQuestionId(optimisticUserMessage.id);
        setShouldScrollToQuestion(true);
      }, 100); // Small delay to ensure DOM is updated

      // Send message to API
      const response: TalkResponse = await conversationsApi.sendMessageToConversation(
        conversationId,
        messageText
      );

      // Add the AI response (user message is already in the list)
      setMessages(prev => [...prev, response.assistant_message]);

    } catch (err) {
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
      setNewMessage(messageText); // Restore message
      setError(handleApiError(err));
    } finally {
      setIsSending(false);
    }
  };

  const handleBackToConversations = () => {
    router.push('/conversations');
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

  // Loading state
  if (authLoading || loading) {
    return <LoadingPage message="Loading conversation..." />;
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout
        title="Conversation"
        description="Chat about your palm reading"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to Load Conversation
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={fetchConversation}>Try Again</Button>
              <Button variant="outline" onClick={handleBackToConversations}>
                Back to Conversations
              </Button>
            </div>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  if (!conversation) {
    return (
      <DashboardLayout
        title="Conversation"
        description="Chat about your palm reading"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Conversation Not Found
            </h3>
            <p className="text-gray-600 mb-4">
              This conversation may have been deleted or you don't have permission to view it.
            </p>
            <Button onClick={handleBackToConversations}>
              Back to Conversations
            </Button>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title={conversation.title}
      description="Chat about your palm reading"
    >
      <div className="space-y-6 h-full">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={handleBackToConversations}
            className="flex items-center"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="ml-2">Back</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="text-red-600 hover:text-red-700 hover:border-red-300 border-red-200"
          >
            <Trash2 className="w-4 h-4" />
            <span className="ml-2">Delete</span>
          </Button>
        </div>


        {/* Enhanced chat interface - Using the exact design from analyses page */}
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
          <div className="flex-1 overflow-y-auto" ref={messagesContainerRef}>
            <div className="space-y-6 p-6 min-h-0">
              {messages.length === 0 && !isSending ? (
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
                  data-message-id={message.id}
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
                        {/* MARKDOWN RENDERING: Render markdown for AI messages, plain text for user messages */}
                        {message.role.toLowerCase() === 'assistant' ? (
                          <div className="text-sm leading-relaxed">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]} // GitHub Flavored Markdown support
                              components={{
                                // Custom styled headers with hierarchical saffron theming
                                h1: ({children}) => <h1 className="text-base font-bold text-gray-900 mb-2 mt-0">{children}</h1>,
                                h2: ({children}) => <h2 className="text-sm font-bold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h2>,
                                h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
                                h4: ({children}) => <h4 className="text-sm font-semibold text-gray-800 mb-1 mt-2 first:mt-0">{children}</h4>,
                                // Bold text gets saffron accent for emphasis
                                strong: ({children}) => <strong className="font-semibold text-saffron-700">{children}</strong>,
                                // Lists with proper indentation and spacing
                                ul: ({children}) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                                ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                                li: ({children}) => <li className="text-sm text-gray-800">{children}</li>,
                                // Paragraphs with consistent spacing
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

              {isSending && (
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
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
                    disabled={isSending}
                    className="border-saffron-200 focus:border-saffron-500 focus:ring-saffron-500 rounded-xl bg-white"
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim() || isSending}
                  className="bg-saffron-600 hover:bg-saffron-700 text-white rounded-xl px-6 py-2 font-medium"
                >
                  {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Send'}
                </Button>
              </div>

              {error && (
                <div className="p-3 mt-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600 flex items-center gap-2">
                    <span className="text-red-500">⚠️</span>
                    {error}
                  </p>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}