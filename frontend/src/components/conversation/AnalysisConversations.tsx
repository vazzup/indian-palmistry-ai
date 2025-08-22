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

interface Conversation {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

interface Message {
  id: number;
  conversationId: number;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  tokensUsed?: number;
  cost?: number;
}

interface AnalysisConversationsProps {
  analysisId: number;
}

export const AnalysisConversations: React.FC<AnalysisConversationsProps> = ({ 
  analysisId 
}) => {
  const [conversations, setConversations] = React.useState<Conversation[]>([
    {
      id: 1,
      title: 'Questions about my life line',
      createdAt: '2024-01-15T11:00:00Z',
      updatedAt: '2024-01-15T11:30:00Z',
      messageCount: 6,
    },
    {
      id: 2,
      title: 'Career insights',
      createdAt: '2024-01-15T14:00:00Z',
      updatedAt: '2024-01-15T14:15:00Z',
      messageCount: 4,
    },
    {
      id: 3,
      title: 'Love and relationships',
      createdAt: '2024-01-16T09:00:00Z',
      updatedAt: '2024-01-16T09:20:00Z',
      messageCount: 8,
    },
  ]);

  const [activeConversationId, setActiveConversationId] = React.useState<number | null>(
    conversations.length > 0 ? conversations[0].id : null
  );
  
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: 1,
      conversationId: 1,
      role: 'user',
      content: 'Can you tell me more about what my life line indicates?',
      createdAt: '2024-01-15T11:00:00Z',
    },
    {
      id: 2,
      conversationId: 1,
      role: 'assistant',
      content: 'Based on your palm reading, your life line shows several interesting characteristics. The depth and clarity of your life line indicate strong vitality and a robust constitution. The line appears to curve gently around the mount of Venus, suggesting a warm, affectionate nature and strong family bonds.',
      createdAt: '2024-01-15T11:01:00Z',
      tokensUsed: 85,
      cost: 0.002,
    },
    {
      id: 3,
      conversationId: 1,
      role: 'user',
      content: 'What does the length of my life line tell you about my longevity?',
      createdAt: '2024-01-15T11:05:00Z',
    },
    {
      id: 4,
      conversationId: 1,
      role: 'assistant',
      content: 'The length of your life line extends well toward your wrist, which in traditional palmistry is associated with longevity and sustained energy throughout life. However, it\'s important to note that the life line represents the quality of life and vitality rather than exact lifespan. Your line suggests you have the potential for a long, healthy life with good energy levels, especially if you maintain healthy lifestyle choices.',
      createdAt: '2024-01-15T11:06:00Z',
      tokensUsed: 92,
      cost: 0.003,
    },
  ]);

  const [newMessage, setNewMessage] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [isCreatingConversation, setIsCreatingConversation] = React.useState(false);
  const [newConversationTitle, setNewConversationTitle] = React.useState('');

  const conversationTemplates = [
    'Questions about my life line',
    'Career and financial insights',
    'Love and relationship guidance',
    'Health and wellness indicators',
    'Personal strengths and talents',
    'Future opportunities',
  ];

  const activeConversation = conversations.find(c => c.id === activeConversationId);
  const conversationMessages = messages.filter(m => m.conversationId === activeConversationId);

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !activeConversationId || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      conversationId: activeConversationId,
      role: 'user',
      content: newMessage.trim(),
      createdAt: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);

    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      const aiMessage: Message = {
        id: Date.now() + 1,
        conversationId: activeConversationId,
        role: 'assistant',
        content: `Thank you for your question about "${userMessage.content}". Based on your palm analysis, I can provide you with detailed insights. This is a simulated response for the demo. In the actual implementation, this would connect to the backend conversation API and provide contextual responses based on your specific palm reading.`,
        createdAt: new Date().toISOString(),
        tokensUsed: 75,
        cost: 0.002,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConversation = async (title: string) => {
    if (!title.trim()) return;

    setIsCreatingConversation(true);

    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newConversation: Conversation = {
        id: Date.now(),
        title: title.trim(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messageCount: 0,
      };

      setConversations(prev => [newConversation, ...prev]);
      setActiveConversationId(newConversation.id);
      setNewConversationTitle('');
    } catch (error) {
      console.error('Failed to create conversation:', error);
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

  if (conversations.length === 0 && !isCreatingConversation) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-saffron-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Start Your First Conversation
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
                />
                <Button
                  onClick={() => handleCreateConversation(newConversationTitle)}
                  disabled={!newConversationTitle.trim()}
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
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Conversations Sidebar */}
      <div className="lg:col-span-1">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Conversations</CardTitle>
              <Button
                size="sm"
                onClick={() => setIsCreatingConversation(true)}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isCreatingConversation && (
              <div className="p-4 border-b border-gray-200">
                <div className="space-y-2">
                  <Input
                    type="text"
                    placeholder="Conversation title..."
                    value={newConversationTitle}
                    onChange={(e) => setNewConversationTitle(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleCreateConversation(newConversationTitle);
                      }
                    }}
                    autoFocus
                  />
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      onClick={() => handleCreateConversation(newConversationTitle)}
                      disabled={!newConversationTitle.trim() || isCreatingConversation}
                      loading={isCreatingConversation}
                    >
                      Create
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setIsCreatingConversation(false);
                        setNewConversationTitle('');
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </div>
            )}
            
            <div className="max-h-96 overflow-y-auto">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => setActiveConversationId(conversation.id)}
                  className={`w-full text-left p-4 border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                    activeConversationId === conversation.id ? 'bg-saffron-50 border-saffron-200' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {conversation.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {conversation.messageCount} message{conversation.messageCount !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="ml-2 flex-shrink-0">
                      <p className="text-xs text-gray-400">
                        {formatTime(conversation.updatedAt)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chat Interface */}
      <div className="lg:col-span-3">
        {activeConversation ? (
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="text-lg">{activeConversation.title}</CardTitle>
              <CardDescription>
                Chat about your palm reading analysis
              </CardDescription>
            </CardHeader>
            
            {/* Messages */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {conversationMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-saffron-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'assistant' && (
                        <Bot className="w-4 h-4 mt-1 flex-shrink-0" />
                      )}
                      {message.role === 'user' && (
                        <User className="w-4 h-4 mt-1 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm">{message.content}</p>
                        <div className="flex items-center justify-between mt-2">
                          <p className={`text-xs ${
                            message.role === 'user' ? 'text-saffron-200' : 'text-gray-500'
                          }`}>
                            {formatTime(message.createdAt)}
                          </p>
                          {message.cost && (
                            <p className={`text-xs ${
                              message.role === 'user' ? 'text-saffron-200' : 'text-gray-500'
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
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a conversation
              </h3>
              <p className="text-gray-600">
                Choose a conversation from the sidebar to start chatting
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};