'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  Hand, 
  MessageCircle, 
  Clock, 
  TrendingUp,
  Plus,
  ArrowRight,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { NewReadingModal } from '@/components/dashboard/NewReadingModal';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { useAuth } from '@/lib/auth';
import { getRandomMessage } from '@/lib/cultural-theme';
import {
  useDashboard,
  formatAnalysisDate,
  calculateSuccessRate
} from '@/hooks/useDashboard';
import { DataInconsistencyErrorBoundary } from '@/components/errors/DataInconsistencyErrorBoundary';

export default function DashboardPage() {
  const router = useRouter();
  const { user, associateAnalysisIfNeeded } = useAuth();
  const [welcomeMessage] = React.useState(() => getRandomMessage('welcome'));
  const [showNewReadingModal, setShowNewReadingModal] = React.useState(false);
  
  // Fetch dashboard data from API
  const {
    data: dashboardData,
    loading,
    error,
    refetch
  } = useDashboard();

  // Associate any pending guest analysis when component mounts (for OAuth users)
  // Also check if user profile is complete (for existing users)
  React.useEffect(() => {
    const handleOnboarding = async () => {
      if (!user) return;

      // Check if profile is incomplete (existing user who needs to complete profile)
      if (!user.age || !user.gender) {
        console.log('User profile incomplete, redirecting to complete-profile');
        router.push('/complete-profile');
        return;
      }

      // If profile is complete, proceed with analysis association
      try {
        const associatedAnalysisId = await associateAnalysisIfNeeded();
        if (associatedAnalysisId) {
          console.log(`OAuth user: Successfully associated analysis ${associatedAnalysisId}`);
          // Redirect to the analysis page to show the reading
          router.push(`/analyses/${associatedAnalysisId}`);
        }
      } catch (error) {
        console.error('Failed to associate analysis for OAuth user:', error);
      }
    };

    handleOnboarding();
  }, [user, associateAnalysisIfNeeded, router]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  // Calculate derived stats from dashboard data
  const stats = React.useMemo(() => {
    if (!dashboardData?.overview) {
      return {
        totalAnalyses: 0,
        totalConversations: 0,
        thisMonth: 0,
        avgResponseTime: '--',
        successRate: 0,
      };
    }

    const { overview, analytics } = dashboardData;
    const currentMonth = new Date().getMonth();
    const thisMonthData = analytics?.analyses_by_month?.find(
      (item: any) => new Date(item.month).getMonth() === currentMonth
    );

    return {
      totalAnalyses: overview.total_analyses,
      totalConversations: overview.total_conversations,
      thisMonth: thisMonthData?.count || 0,
      avgResponseTime: analytics?.avg_response_time || '--',
      successRate: overview.success_rate,
    };
  }, [dashboardData]);


  const recentAnalyses = React.useMemo(() => {
    if (!dashboardData?.recent_activity) return [];
    
    // Filter and transform recent activity to analysis format
    return dashboardData.recent_activity
      .filter((activity: any) => activity.type === 'analysis' && activity.id)
      .slice(0, 3)
      .map((activity: any) => ({
        id: activity.id,
        createdAt: activity.timestamp,
        status: activity.status || 'completed',
        summary: activity.description || 'Analysis completed successfully',
        conversationCount: 0, // Will be populated from backend if available
      }));
  }, [dashboardData]);

  // Loading state
  if (loading) {
    return (
      <DashboardLayout
        title={`${getGreeting()}, ${user?.name?.split(' ')[0] || 'there'}!`}
        description={welcomeMessage}
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-saffron-600" />
          <span className="ml-3 text-gray-600">Loading your dashboard...</span>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout
        title={`${getGreeting()}, ${user?.name?.split(' ')[0] || 'there'}!`}
        description={welcomeMessage}
      >
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Unable to Load Dashboard
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <Button onClick={() => refetch()}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title={`${getGreeting()}, ${user?.name?.split(' ')[0] || 'there'}!`}
      description={welcomeMessage}
    >
      <DataInconsistencyErrorBoundary>
      <div className="space-y-6">
        
        {/* Quick Actions */}
        <div className="bg-gradient-to-r from-saffron-50 to-turmeric-50 rounded-lg p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-4 sm:space-y-0">
            <div>
              <h2 className="text-lg font-semibold text-saffron-900">
                Ready for a new reading?
              </h2>
              <p className="text-sm text-saffron-700">
                Upload your palm images and discover new insights about your life
              </p>
            </div>
            <Button
              onClick={() => setShowNewReadingModal(true)}
              className="bg-saffron-600 hover:bg-saffron-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Reading
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/*<StatsCard
            title="Total Readings"
            value={stats.totalAnalyses}
            description="All time palm analyses"
            icon={Hand}
            trend={stats.totalAnalyses > 0 ? { value: Math.min(stats.successRate, 100), isPositive: true } : undefined}
          />
          <StatsCard
            title="Conversations"
            value={stats.totalConversations}
            description="AI chat sessions"
            icon={MessageCircle}
            trend={stats.totalConversations > stats.totalAnalyses ? 
              { value: Math.round(((stats.totalConversations - stats.totalAnalyses) / Math.max(stats.totalAnalyses, 1)) * 100), isPositive: true } : 
              undefined
            }
          />
          <StatsCard
            title="This Month"
            value={stats.thisMonth}
            description="New readings this month"
            icon={TrendingUp}
          />
          <StatsCard
            title="Success Rate"
            value={`${Math.round(stats.successRate)}%`}
            description="Analysis completion rate"
            icon={Clock}
            trend={stats.successRate >= 80 ? { value: Math.round(stats.successRate), isPositive: true } : undefined}
          />*/}
        </div>

        {/* Recent Analyses */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Readings</CardTitle>
              <CardDescription>
                Your latest palm analyses and insights
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/analyses')}
            >
              View All
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardHeader>
          <CardContent>
            {recentAnalyses.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Hand className="w-8 h-8 text-saffron-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No readings yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Upload your first palm image to get started with AI-powered insights
                </p>
                <Button onClick={() => setShowNewReadingModal(true)}>
                  Get Your First Reading
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentAnalyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg hover:border-saffron-200 hover:bg-saffron-50/30 transition-colors cursor-pointer"
                    onClick={() => router.push(`/analyses/${analysis.id}`)}
                  >
                    <div className="w-10 h-10 bg-saffron-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Hand className="w-5 h-5 text-saffron-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          Reading #{analysis.id}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatAnalysisDate(analysis.createdAt)}
                        </p>
                      </div>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {analysis.summary}
                      </p>
                      <div className="flex items-center mt-2 space-x-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-700">
                          Completed
                        </span>
                        {analysis.conversationCount > 0 && (
                          <span className="text-xs text-gray-500 flex items-center">
                            <MessageCircle className="w-3 h-3 mr-1" />
                            {analysis.conversationCount} conversation{analysis.conversationCount !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>


        {/* Quick Tips */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Palm Reading Tips
            </CardTitle>
            <CardDescription>
              Make the most of your readings with these insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Best Photo Practices</h4>
                <p className="text-xs text-muted-foreground">
                  Use natural lighting and keep your palm flat for the most accurate readings
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Ask Follow-up Questions</h4>
                <p className="text-xs text-muted-foreground">
                  Chat with AI about specific aspects of your reading for deeper insights
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Track Progress</h4>
                <p className="text-xs text-muted-foreground">
                  Compare readings over time to see how your life path evolves
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Cultural Context</h4>
                <p className="text-xs text-muted-foreground">
                  Our AI uses traditional Indian palmistry principles for authentic readings
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </DataInconsistencyErrorBoundary>

      {/* New Reading Modal */}
      <NewReadingModal
        isOpen={showNewReadingModal}
        onClose={() => setShowNewReadingModal(false)}
      />

      {/* Floating Action Button for Mobile */}
      <FloatingActionButton
        onClick={() => setShowNewReadingModal(true)}
        icon={<Plus className="w-6 h-6" />}
        label="New Reading"
        className="md:hidden" // Only show on mobile
      />
    </DashboardLayout>
  );
}
