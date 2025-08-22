'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { 
  Hand, 
  MessageCircle, 
  Clock, 
  TrendingUp,
  Plus,
  ArrowRight 
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';
import { getRandomMessage } from '@/lib/cultural-theme';

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [welcomeMessage] = React.useState(() => getRandomMessage('welcome'));
  
  // TODO: Replace with actual API calls
  const [stats] = React.useState({
    totalAnalyses: 3,
    totalConversations: 7,
    thisMonth: 2,
    avgResponseTime: '1.2s',
  });
  
  const [recentAnalyses] = React.useState([
    {
      id: 1,
      createdAt: '2024-01-15T10:30:00Z',
      status: 'completed',
      summary: 'Your life line shows strong vitality and a long, healthy life ahead...',
      conversationCount: 3,
    },
    {
      id: 2,
      createdAt: '2024-01-12T14:20:00Z',
      status: 'completed',
      summary: 'The heart line reveals a passionate nature with deep emotional connections...',
      conversationCount: 2,
    },
    {
      id: 3,
      createdAt: '2024-01-08T09:15:00Z',
      status: 'completed',
      summary: 'Your head line indicates analytical thinking and creative problem-solving...',
      conversationCount: 1,
    },
  ]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <DashboardLayout
      title={`${getGreeting()}, ${user?.name?.split(' ')[0] || 'there'}!`}
      description={welcomeMessage}
    >
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
              onClick={() => router.push('/')}
              className="bg-saffron-600 hover:bg-saffron-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Reading
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Readings"
            value={stats.totalAnalyses}
            description="All time palm analyses"
            icon={Hand}
            trend={{ value: 15, isPositive: true }}
          />
          <StatsCard
            title="Conversations"
            value={stats.totalConversations}
            description="AI chat sessions"
            icon={MessageCircle}
            trend={{ value: 8, isPositive: true }}
          />
          <StatsCard
            title="This Month"
            value={stats.thisMonth}
            description="New readings this month"
            icon={TrendingUp}
          />
          <StatsCard
            title="Avg Response"
            value={stats.avgResponseTime}
            description="AI response time"
            icon={Clock}
          />
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
                <Button onClick={() => router.push('/')}>
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
                          {formatDate(analysis.createdAt)}
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
              <span className="text-lg mr-2">💡</span>
              Palm Reading Tips
            </CardTitle>
            <CardDescription>
              Make the most of your readings with these insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">🖐️ Best Photo Practices</h4>
                <p className="text-xs text-muted-foreground">
                  Use natural lighting and keep your palm flat for the most accurate readings
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">💬 Ask Follow-up Questions</h4>
                <p className="text-xs text-muted-foreground">
                  Chat with AI about specific aspects of your reading for deeper insights
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">📊 Track Progress</h4>
                <p className="text-xs text-muted-foreground">
                  Compare readings over time to see how your life path evolves
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">🔮 Cultural Context</h4>
                <p className="text-xs text-muted-foreground">
                  Our AI uses traditional Indian palmistry principles for authentic readings
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}