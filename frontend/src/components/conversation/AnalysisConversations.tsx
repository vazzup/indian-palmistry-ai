'use client';

import React from 'react';
import { 
  MessageCircle, 
  Plus, 
  Search,
  Send,
  Loader2,
  Clock,
  User,
  Bot 
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { conversationsApi } from '@/lib/api';
import { LegalNotice } from '@/components/legal/LegalNotice';
import type { Conversation, Message, TalkResponse } from '@/types';

interface AnalysisConversationsProps {
  analysisId: number;
}

export const AnalysisConversations: React.FC<AnalysisConversationsProps> = ({ 
  analysisId 
}) => {
  const [conversation, setConversation] = React.useState<Conversation | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [newMessage, setNewMessage] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [isCreatingConversation, setIsCreatingConversation] = React.useState(false);
  const [newConversationTitle, setNewConversationTitle] = React.useState('');
  const [isLoadingMessages, setIsLoadingMessages] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load conversation and messages on mount
  React.useEffect(() => {
    loadConversation();
  }, [analysisId]);

  const loadConversation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const conversationData = await conversationsApi.getAnalysisConversation(analysisId.toString());
      
      if (conversationData) {
        setConversation(conversationData);
        await loadMessages(conversationData.id);
      } else {
        setConversation(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      setError('Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (conversationId: number) => {
    try {
      setIsLoadingMessages(true);
      const messageData = await conversationsApi.getConversationMessages(
        analysisId.toString(), 
        conversationId.toString()
      );
      setMessages(messageData.messages || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
      // Don't show error for messages, just log it
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const conversationTemplates = [
    'Questions about my life line',
    'Career and financial insights',
    'Love and relationship guidance',
    'Health and wellness indicators',
    'Personal strengths and talents',
    'Future opportunities',
  ];

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !conversation || isLoading) return;

    setIsLoading(true);
    const messageContent = newMessage.trim();
    setNewMessage('');

    try {
      const response: TalkResponse = await conversationsApi.sendMessage(
        analysisId.toString(),
        conversation.id.toString(),
        messageContent
      );

      // Add both user message and assistant response to the messages list
      setMessages(prev => [...prev, response.user_message, response.assistant_message]);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message. Please try again.');
      // Restore the message text so user can retry
      setNewMessage(messageContent);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConversation = async (title: string) => {
    if (!title.trim()) return;

    setIsCreatingConversation(true);
    setError(null);

    try {
      const newConversation = await conversationsApi.createConversation({
        analysis_id: analysisId,
        title: title.trim()
      });

      setConversation(newConversation);
      setMessages([]); // New conversation starts with no messages
      setNewConversationTitle('');
    } catch (error) {
      console.error('Failed to create conversation:', error);
      setError('Failed to create conversation. Please try again.');
    } finally {
      setIsCreatingConversation(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-saffron-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading conversation...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-red-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Conversation</h3>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button onClick={loadConversation} variant="outline">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!conversation && !isCreatingConversation) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-saffron-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Start Your Conversation
          </h3>
          <p className="text-gray-600 mb-6">
            Ask questions about your palm reading and get detailed insights from our AI
          </p>
          
          <div className="max-w-md mx-auto space-y-3">
            <h4 className="text-sm font-medium text-gray-900">Popular conversation topics:</h4>
            <div className="grid grid-cols-1 gap-2">
              {conversationTemplates.map((template, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleCreateConversation(template)}
                  disabled={isCreatingConversation}
                  className="text-left justify-start"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {template}
                </Button>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex space-x-2">
                <Input
                  type="text"
                  placeholder="Or create custom conversation..."
                  value={newConversationTitle}
                  onChange={(e) => setNewConversationTitle(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateConversation(newConversationTitle);
                    }
                  }}
                  disabled={isCreatingConversation}
                />
                <Button
                  onClick={() => handleCreateConversation(newConversationTitle)}
                  disabled={!newConversationTitle.trim() || isCreatingConversation}
                  loading={isCreatingConversation}
                >
                  Create
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="text-lg">{conversation?.title || 'Palm Reading Conversation'}</CardTitle>
        <CardDescription>
          Chat about your palm reading analysis
        </CardDescription>
      </CardHeader>
            
      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoadingMessages ? (
          <div className="flex justify-center">
            <div className="flex items-center space-x-2 text-gray-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Loading messages...</span>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'USER' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'USER'
                    ? 'bg-saffron-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.role === 'ASSISTANT' && (
                    <Bot className="w-4 h-4 mt-1 flex-shrink-0" />
                  )}
                  {message.role === 'USER' && (
                    <User className="w-4 h-4 mt-1 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm">{message.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className={`text-xs ${
                        message.role === 'USER' ? 'text-saffron-200' : 'text-gray-500'
                      }`}>
                        {formatTime(message.created_at)}
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
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4" />
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
            
      {/* Message Input */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        <div className="mb-3">
          <LegalNotice variant="card" />
        </div>
        <div className="flex space-x-2">
          <Input
            type="text"
            placeholder="Ask about your palm reading..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!newMessage.trim() || isLoading}
            loading={isLoading}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};