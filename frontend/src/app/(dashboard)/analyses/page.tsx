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
  XCircle,
  Loader2,
  AlertCircle,
  RefreshCw,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAnalysesList, formatAnalysisDate, getStatusColorClass } from '@/hooks/useDashboard';
import { DataInconsistencyErrorBoundary } from '@/components/errors/DataInconsistencyErrorBoundary';
import { analysisApi } from '@/lib/api';

export default function AnalysesPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState<string>('all');
  const [sortBy, setSortBy] = React.useState<'newest' | 'oldest'>('newest');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [localSearchQuery, setLocalSearchQuery] = React.useState('');
  
  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [analysisToDelete, setAnalysisToDelete] = React.useState<string | null>(null);
  
  // Debounce search query
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(localSearchQuery);
      setCurrentPage(1); // Reset to first page when searching
    }, 300);
    
    return () => clearTimeout(timer);
  }, [localSearchQuery]);

  // Fetch analyses from API with current filters
  const apiParams = React.useMemo(() => ({
    page: currentPage,
    limit: 10,
    status: filterStatus === 'all' ? undefined : filterStatus,
    sort: sortBy === 'newest' ? '-created_at' : 'created_at',
  }), [currentPage, filterStatus, sortBy]);

  const { 
    data: analysesData, 
    loading, 
    error, 
    refetch,
    forceRefresh,
    isRefreshing,
    lastRefresh
  } = useAnalysesList(apiParams);

  // Filter analyses by search query and only show successful ones (client-side for now)
  const filteredAnalyses = React.useMemo(() => {
    if (!analysesData?.analyses) return [];
    
    // First filter to only show completed analyses (hide failed ones)
    const completedAnalyses = analysesData.analyses.filter(analysis => 
      analysis.status === 'completed'
    );
    
    if (!searchQuery.trim()) return completedAnalyses;
    
    const query = searchQuery.toLowerCase();
    return completedAnalyses.filter(analysis =>
      analysis.id.toLowerCase().includes(query) ||
      (analysis.summary && analysis.summary.toLowerCase().includes(query))
    );
  }, [analysesData?.analyses, searchQuery]);

  // Handle filter changes
  const handleFilterChange = (newFilter: string) => {
    setFilterStatus(newFilter);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleSortChange = (newSort: 'newest' | 'oldest') => {
    setSortBy(newSort);
    setCurrentPage(1); // Reset to first page when sorting
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

  const handleDeleteAnalysis = (analysisId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    console.log('Delete button clicked for analysis:', analysisId);
    setAnalysisToDelete(analysisId);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteAnalysis = async () => {
    if (!analysisToDelete || isDeleting) return;

    console.log('Confirming delete for analysis:', analysisToDelete);
    setIsDeleting(true);

    try {
      await analysisApi.deleteAnalysis(analysisToDelete);
      console.log('Delete successful, refreshing list');
      
      // Refresh the analyses list
      refetch();
      
      // Close modal
      setShowDeleteConfirm(false);
      setAnalysisToDelete(null);
    } catch (error) {
      console.error('Failed to delete analysis:', error);
      // Keep modal open, show error (you could add error state if needed)
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewAnalysis = (analysisId: string) => {
    router.push(`/analyses/${analysisId}`);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Loading state
  if (loading) {
    return (
      <DashboardLayout
        title="My Readings"
        description="View and manage all your palm analyses"
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-saffron-600" />
          <span className="ml-3 text-gray-600">Loading your analyses...</span>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout
        title="My Readings"
        description="View and manage all your palm analyses"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to Load Analyses
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
      title="My Readings"
      description="View and manage all your palm analyses"
    >
      <DataInconsistencyErrorBoundary>
      <div className="space-y-6">
        {/* Data Status Bar */}
        {/*<div className="bg-white border border-gray-200 rounded-lg p-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Analyses {isRefreshing ? 'refreshing...' : 'loaded'}
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
        </div> */}
        
        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        {/*<div className="flex flex-col sm:flex-row gap-4 flex-1">*/}
            {/* Search */}
            {/*<div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search readings..."
                value={localSearchQuery}
                onChange={(e) => setLocalSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>*/}

            {/* Filters */}
            {/*<div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) => handleFilterChange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="failed">Failed</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value as 'newest' | 'oldest')}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-saffron-500"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
              </select>
            </div>*/}
            {/*</div>*/}

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
          Showing {filteredAnalyses.length} successful reading{filteredAnalyses.length !== 1 ? 's' : ''}
          {searchQuery && ` (filtered)`}
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
                        {/* Header - Clean without duplicate date */}
                        <div className="mb-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            Reading #{analysis.id}
                          </h3>
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
                            {new Date(analysis.created_at).toLocaleDateString()}
                          </span>
                          
                          {analysis.conversation_count > 0 && (
                            <span className="flex items-center">
                              <MessageCircle className="w-3 h-3 mr-1" />
                              {analysis.conversation_count} conversation{analysis.conversation_count !== 1 ? 's' : ''}
                            </span>
                          )}
                          
                          {/*{analysis.cost && (
                            <span>
                              Cost: ${analysis.cost.toFixed(2)}
                            </span>
                          )}*/}
                          
                        </div>
                      </div>
                    </div>

                    {/* Actions - Mobile Responsive */}
                    <div className="flex items-center space-x-2 ml-4">
                      {analysis.status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewAnalysis(analysis.id)}
                        >
                          <Eye className="w-4 h-4" />
                          <span className="hidden sm:ml-1 sm:inline">View</span>
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleDeleteAnalysis(analysis.id, e)}
                        className="text-red-600 hover:text-red-700 hover:border-red-300"
                        title="Delete Reading"
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
        {analysesData && analysesData.total_pages > 1 && (
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
              Page {currentPage} of {analysesData.total_pages}
            </span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === analysesData.total_pages}
            >
              Next
            </Button>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && analysisToDelete && (
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
                    Reading #{analysisToDelete}
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
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setAnalysisToDelete(null);
                  }}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmDeleteAnalysis}
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
      </DataInconsistencyErrorBoundary>
    </DashboardLayout>
  );
}
