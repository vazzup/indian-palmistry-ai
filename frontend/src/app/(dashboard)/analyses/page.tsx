'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  Hand, 
  Search, 
  Filter, 
  Calendar,
  MessageCircle,
  Eye,
  Trash2,
  Plus,
  ArrowRight,
  Clock,
  CheckCircle,
  XCircle 
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Analysis {
  id: number;
  createdAt: string;
  status: 'completed' | 'processing' | 'failed';
  summary: string;
  conversationCount: number;
  leftImagePath?: string;
  rightImagePath?: string;
  cost?: number;
}

export default function AnalysesPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState<string>('all');
  const [sortBy, setSortBy] = React.useState<'newest' | 'oldest'>('newest');
  
  // TODO: Replace with actual API calls
  const [analyses] = React.useState<Analysis[]>([
    {
      id: 5,
      createdAt: '2024-01-15T10:30:00Z',
      status: 'completed',
      summary: 'Your life line shows strong vitality and a long, healthy life ahead. The depth and clarity indicate excellent physical constitution and natural resilience.',
      conversationCount: 3,
      leftImagePath: '/path/to/left.jpg',
      cost: 0.12,
    },
    {
      id: 4,
      createdAt: '2024-01-12T14:20:00Z',
      status: 'completed',
      summary: 'The heart line reveals a passionate nature with deep emotional connections. You value meaningful relationships and have strong intuitive abilities.',
      conversationCount: 2,
      rightImagePath: '/path/to/right.jpg',
      cost: 0.08,
    },
    {
      id: 3,
      createdAt: '2024-01-08T09:15:00Z',
      status: 'completed',
      summary: 'Your head line indicates analytical thinking and creative problem-solving abilities. You approach challenges with both logic and innovation.',
      conversationCount: 1,
      leftImagePath: '/path/to/left.jpg',
      rightImagePath: '/path/to/right.jpg',
      cost: 0.15,
    },
    {
      id: 2,
      createdAt: '2024-01-05T16:45:00Z',
      status: 'processing',
      summary: '',
      conversationCount: 0,
      leftImagePath: '/path/to/left.jpg',
    },
    {
      id: 1,
      createdAt: '2024-01-02T11:20:00Z',
      status: 'failed',
      summary: '',
      conversationCount: 0,
      leftImagePath: '/path/to/left.jpg',
    },
  ]);

  const [filteredAnalyses, setFilteredAnalyses] = React.useState<Analysis[]>(analyses);

  React.useEffect(() => {
    let filtered = analyses;

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(analysis =>
        analysis.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        analysis.id.toString().includes(searchQuery)
      );
    }

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(analysis => analysis.status === filterStatus);
    }

    // Sort
    filtered = filtered.sort((a, b) => {
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
    });

    setFilteredAnalyses(filtered);
  }, [analyses, searchQuery, filterStatus, sortBy]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDeleteAnalysis = (analysisId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    // TODO: Implement delete confirmation and API call
    console.log('Delete analysis:', analysisId);
  };

  const handleViewAnalysis = (analysisId: number) => {
    router.push(`/analyses/${analysisId}`);
  };

  return (
    <DashboardLayout
      title="My Readings"
      description="View and manage all your palm analyses"
    >
      <div className="space-y-6">
        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search readings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="failed">Failed</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest')}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
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
          Showing {filteredAnalyses.length} of {analyses.length} reading{analyses.length !== 1 ? 's' : ''}
        </div>

        {/* Analyses List */}
        {filteredAnalyses.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Hand className="w-8 h-8 text-saffron-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchQuery || filterStatus !== 'all' ? 'No matching readings' : 'No readings yet'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchQuery || filterStatus !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Upload your first palm image to get started with AI-powered insights'
                }
              </p>
              {!searchQuery && filterStatus === 'all' && (
                <Button onClick={() => router.push('/')}>
                  Get Your First Reading
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredAnalyses.map((analysis) => (
              <Card key={analysis.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Icon */}
                      <div className="w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Hand className="w-6 h-6 text-saffron-600" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900">
                              Reading #{analysis.id}
                            </h3>
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(analysis.status)}`}
                            >
                              {getStatusIcon(analysis.status)}
                              <span className="ml-1 capitalize">{analysis.status}</span>
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">
                            {formatDate(analysis.createdAt)}
                          </div>
                        </div>

                        {/* Summary */}
                        {analysis.summary && (
                          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                            {analysis.summary}
                          </p>
                        )}

                        {/* Metadata */}
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(analysis.createdAt).toLocaleDateString()}
                          </span>
                          
                          {analysis.conversationCount > 0 && (
                            <span className="flex items-center">
                              <MessageCircle className="w-3 h-3 mr-1" />
                              {analysis.conversationCount} conversation{analysis.conversationCount !== 1 ? 's' : ''}
                            </span>
                          )}
                          
                          {analysis.cost && (
                            <span>
                              Cost: ${analysis.cost.toFixed(2)}
                            </span>
                          )}
                          
                          <span>
                            {analysis.leftImagePath && analysis.rightImagePath 
                              ? 'Both palms' 
                              : analysis.leftImagePath 
                                ? 'Left palm' 
                                : 'Right palm'
                            }
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      {analysis.status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewAnalysis(analysis.id)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleDeleteAnalysis(analysis.id, e)}
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

        {/* Pagination (TODO: Implement when needed) */}
        {filteredAnalyses.length > 10 && (
          <div className="flex items-center justify-center space-x-2 py-4">
            <Button variant="outline" size="sm" disabled>
              Previous
            </Button>
            <span className="text-sm text-gray-600">Page 1 of 1</span>
            <Button variant="outline" size="sm" disabled>
              Next
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}