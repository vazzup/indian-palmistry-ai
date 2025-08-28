'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  MessageCircle, 
  Search, 
  Calendar,
  Hand,
  Eye,
  Trash2,
  Plus,
  Loader2,
  AlertCircle,
  RefreshCw,
  Shield,
  User,
  Bot
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { 
  useConversationsList, 
  formatAnalysisDate, 
  getStatusColorClass,
  type ConversationListItem 
} from '@/hooks/useDashboard';
import { DataInconsistencyErrorBoundary } from '@/components/errors/DataInconsistencyErrorBoundary';

export default function ConversationsPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterAnalysis, setFilterAnalysis] = React.useState<string>('all');
  const [sortBy, setSortBy] = React.useState<'newest' | 'oldest' | 'most_active'>('newest');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [localSearchQuery, setLocalSearchQuery] = React.useState('');
  
  // Debounce search query
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(localSearchQuery);
      setCurrentPage(1); // Reset to first page when searching
    }, 300);
    
    return () => clearTimeout(timer);
  }, [localSearchQuery]);

  // Fetch conversations from API with current filters
  const apiParams = React.useMemo(() => ({
    page: currentPage,
    limit: 10,
    analysis_id: filterAnalysis === 'all' ? undefined : filterAnalysis,
    sort: sortBy === 'newest' ? '-updated_at' : sortBy === 'oldest' ? 'updated_at' : '-message_count',
  }), [currentPage, filterAnalysis, sortBy]);

  const { 
    data: conversationsData, 
    loading, 
    error, 
    refetch,
    forceRefresh,
    isRefreshing,
    lastRefresh
  } = useConversationsList(apiParams);

  // Filter conversations by search query (client-side for now)
  const filteredConversations = React.useMemo(() => {
    if (!conversationsData?.conversations) return [];
    
    if (!searchQuery.trim()) return conversationsData.conversations;
    
    const query = searchQuery.toLowerCase();
    return conversationsData.conversations.filter(conversation =>
      conversation.title.toLowerCase().includes(query) ||
      conversation.last_message?.content.toLowerCase().includes(query) ||
      (conversation.analysis?.summary && conversation.analysis.summary.toLowerCase().includes(query))
    );
  }, [conversationsData?.conversations, searchQuery]);

  // Note: Conversations could be grouped by analysis if needed in the future

  // Handle filter changes
  const handleFilterChange = (newFilter: string) => {
    setFilterAnalysis(newFilter);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleSortChange = (newSort: 'newest' | 'oldest' | 'most_active') => {
    setSortBy(newSort);
    setCurrentPage(1); // Reset to first page when sorting
  };

  const handleDeleteConversation = (conversationId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    // TODO: Implement delete confirmation and API call
    console.log('Delete conversation:', conversationId);
  };

  const handleViewConversation = (conversationId: string, analysisId: string) => {
    router.push(`/analyses/${analysisId}?conversation=${conversationId}`);
  };

  const handleViewAnalysis = (analysisId: string) => {
    router.push(`/analyses/${analysisId}`);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const getLastMessagePreview = (conversation: ConversationListItem) => {
    if (!conversation.last_message) return 'No messages yet';
    
    const content = conversation.last_message.content;
    const preview = content.length > 100 ? content.substring(0, 100) + '...' : content;
    const role = conversation.last_message.role === 'USER' ? 'You' : 'AI';
    
    return `${role}: ${preview}`;
  };

  const getRoleIcon = (role: 'USER' | 'ASSISTANT') => {
    return role === 'USER' ? (
      <User className="w-3 h-3 text-blue-600" />
    ) : (
      <Bot className="w-3 h-3 text-saffron-600" />
    );
  };

  // Loading state
  if (loading) {
    return (
      <DashboardLayout
        title="Conversations"
        description="View and continue your palm reading discussions"
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-saffron-600" />
          <span className="ml-3 text-gray-600">Loading your conversations...</span>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout
        title="Conversations"
        description="View and continue your palm reading discussions"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to Load Conversations
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={() => refetch()}>Try Again</Button>
              <Button onClick={forceRefresh} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Force Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title="Conversations"
      description="View and continue your palm reading discussions"
    >
      <DataInconsistencyErrorBoundary>
      <div className="space-y-6">
        {/* Data Status Bar */}
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Conversations {isRefreshing ? 'refreshing...' : 'loaded'}
              </span>
              {lastRefresh && (
                <span className="text-xs text-gray-500">
                  Updated {formatAnalysisDate(lastRefresh.toISOString(), true)}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={() => refetch()}
                disabled={loading || isRefreshing}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${(loading || isRefreshing) ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                onClick={forceRefresh}
                disabled={loading || isRefreshing}
                variant="outline"
                size="sm"
                className="text-orange-600 border-orange-300 hover:bg-orange-50"
              >
                <Shield className="w-4 h-4 mr-1" />
                Clear Cache
              </Button>
            </div>
          </div>
        </div>
        
        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search conversations..."
                value={localSearchQuery}
                onChange={(e) => setLocalSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <select
                value={filterAnalysis}
                onChange={(e) => handleFilterChange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="all">All Analyses</option>
                {/* TODO: Populate with user's analyses */}
              </select>

              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value as 'newest' | 'oldest' | 'most_active')}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="newest">Most Recent</option>
                <option value="oldest">Oldest First</option>
                <option value="most_active">Most Active</option>
              </select>
            </div>
          </div>

          {/* New Reading Button */}
          <Button
            onClick={() => router.push('/')}
            className="bg-saffron-600 hover:bg-saffron-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Reading
          </Button>
        </div>

        {/* Results Count */}
        <div className="text-sm text-muted-foreground">
          Showing {filteredConversations.length} of {conversationsData?.total || 0} conversation{(conversationsData?.total || 0) !== 1 ? 's' : ''}
          {searchQuery && ` (filtered)`}
        </div>

        {/* Conversations List */}
        {filteredConversations.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-saffron-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchQuery || filterAnalysis !== 'all' ? 'No matching conversations' : 'No conversations yet'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchQuery || filterAnalysis !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Start a conversation by asking questions about your palm reading analysis'
                }
              </p>
              {!searchQuery && filterAnalysis === 'all' && (
                <Button onClick={() => router.push('/analyses')}>
                  View Your Analyses
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredConversations.map((conversation) => (
              <Card key={conversation.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Icon */}
                      <div className="w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <MessageCircle className="w-6 h-6 text-saffron-600" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900">
                              {conversation.title}
                            </h3>
                            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-saffron-100 text-saffron-700">
                              <MessageCircle className="w-3 h-3 mr-1" />
                              {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">
                            {formatAnalysisDate(conversation.updated_at, true)}
                          </div>
                        </div>

                        {/* Last Message Preview */}
                        {conversation.last_message && (
                          <div className="flex items-start space-x-2 mb-3 p-3 bg-gray-50 rounded-md">
                            {getRoleIcon(conversation.last_message.role)}
                            <p className="text-gray-600 text-sm line-clamp-2 flex-1">
                              {getLastMessagePreview(conversation)}
                            </p>
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(conversation.created_at).toLocaleDateString()}
                          </span>
                          
                          {conversation.analysis && (
                            <button
                              onClick={() => handleViewAnalysis(conversation.analysis_id)}
                              className="flex items-center hover:text-saffron-600 transition-colors"
                            >
                              <Hand className="w-3 h-3 mr-1" />
                              Analysis #{conversation.analysis_id}
                            </button>
                          )}

                          {conversation.analysis?.status && (
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${getStatusColorClass(conversation.analysis.status)}`}
                            >
                              {conversation.analysis.status}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewConversation(conversation.id, conversation.analysis_id)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Continue
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        className="text-red-600 hover:text-red-700 hover:border-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {conversationsData && conversationsData.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-2 py-4">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {conversationsData.total_pages}
            </span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === conversationsData.total_pages}
            >
              Next
            </Button>
          </div>
        )}

        {/* Tips Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <span className="text-lg mr-2">💬</span>
              Conversation Tips
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">🤔 Ask Specific Questions</h4>
                <p className="text-xs text-muted-foreground">
                  Get more detailed insights by asking about specific aspects of your reading
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">📚 Reference Your Analysis</h4>
                <p className="text-xs text-muted-foreground">
                  The AI has context about your palm reading and can provide personalized responses
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">🔄 Continue Conversations</h4>
                <p className="text-xs text-muted-foreground">
                  Come back anytime to continue discussing your readings with full context
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">🎯 Organize by Topic</h4>
                <p className="text-xs text-muted-foreground">
                  Create separate conversations for different topics like career, love, or health
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </DataInconsistencyErrorBoundary>
    </DashboardLayout>
  );
}