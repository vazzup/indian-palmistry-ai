'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Hand, 
  MessageCircle, 
  Calendar,
  Clock,
  ArrowLeft,
  Share2,
  Download,
  Trash2,
  Plus,
  Eye 
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AnalysisConversations } from '@/components/conversation/AnalysisConversations';
import { useAuth } from '@/lib/auth';

interface AnalysisDetail {
  id: number;
  createdAt: string;
  status: 'completed' | 'processing' | 'failed';
  summary: string;
  fullReport: string;
  conversationCount: number;
  leftImagePath?: string;
  rightImagePath?: string;
  cost?: number;
  tokensUsed?: number;
  processingTime?: number;
}

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const analysisId = parseInt(params.id as string);
  
  // TODO: Replace with actual API call
  const [analysis] = React.useState<AnalysisDetail>({
    id: analysisId,
    createdAt: '2024-01-15T10:30:00Z',
    status: 'completed',
    summary: 'Your life line shows strong vitality and a long, healthy life ahead. The depth and clarity indicate excellent physical constitution and natural resilience.',
    fullReport: `# Complete Palm Analysis Report

## Life Line Analysis
Your life line demonstrates exceptional vitality and longevity. The deep, clear line indicates:
- Strong physical constitution
- Natural resilience and healing ability
- Long, healthy life ahead
- Good energy levels throughout life

## Heart Line Insights
The heart line reveals your emotional nature:
- Passionate and deeply caring personality
- Strong capacity for meaningful relationships
- Intuitive understanding of others' emotions
- Loyalty and commitment in partnerships

## Head Line Characteristics  
Your head line indicates intellectual capabilities:
- Balanced analytical and creative thinking
- Practical problem-solving approach
- Clear decision-making abilities
- Good memory and learning capacity

## Fate Line Interpretation
The fate line suggests your life path:
- Strong sense of purpose and direction
- Career success through dedicated effort
- Ability to overcome obstacles
- Financial stability in later years

## Mount Analysis
The mounts of your palm reveal additional traits:
- Mount of Venus: Strong vitality and love of beauty
- Mount of Jupiter: Natural leadership qualities
- Mount of Saturn: Responsible and disciplined nature
- Mount of Apollo: Creative talents and appreciation for arts

## Overall Assessment
This palm reading indicates a well-balanced individual with strong life force, emotional depth, and intellectual capabilities. You have the potential for a fulfilling life with meaningful relationships and professional success.

Remember that palmistry provides insights into natural tendencies and potential paths. Your choices and actions ultimately shape your destiny.`,
    conversationCount: 3,
    leftImagePath: '/path/to/left.jpg',
    rightImagePath: '/path/to/right.jpg',
    cost: 0.12,
    tokensUsed: 1250,
    processingTime: 45,
  });

  const [activeTab, setActiveTab] = React.useState<'analysis' | 'conversations'>('analysis');

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDelete = () => {
    // TODO: Implement delete confirmation and API call
    console.log('Delete analysis:', analysisId);
  };

  const handleShare = () => {
    // TODO: Implement sharing functionality
    console.log('Share analysis:', analysisId);
  };

  const handleDownload = () => {
    // TODO: Implement download as PDF
    console.log('Download analysis:', analysisId);
  };

  if (!analysis) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-saffron-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Hand className="w-8 h-8 text-saffron-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Reading not found
          </h3>
          <p className="text-gray-600 mb-4">
            The requested palm reading could not be found.
          </p>
          <Button onClick={() => router.push('/analyses')}>
            Back to Readings
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title={`Reading #${analysis.id}`}
      description={`Created on ${formatDate(analysis.createdAt)}`}
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
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
            >
              <Share2 className="w-4 h-4 mr-1" />
              Share
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4 mr-1" />
              Download
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              className="text-red-600 hover:text-red-700 hover:border-red-300"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Analysis Overview */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-saffron-100 rounded-full flex items-center justify-center">
                  <Hand className="w-6 h-6 text-saffron-600" />
                </div>
                <div>
                  <CardTitle className="text-xl">Palm Reading #{analysis.id}</CardTitle>
                  <CardDescription className="mt-1">
                    Complete analysis of your palm patterns and lines
                  </CardDescription>
                </div>
              </div>
              <span className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-green-100 text-green-800">
                Completed
              </span>
            </div>
          </CardHeader>
          <CardContent>
            {/* Metadata */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <Calendar className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                <div className="text-xs text-gray-600">Created</div>
                <div className="text-sm font-medium">
                  {new Date(analysis.createdAt).toLocaleDateString()}
                </div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <MessageCircle className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                <div className="text-xs text-gray-600">Conversations</div>
                <div className="text-sm font-medium">{analysis.conversationCount}</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <Clock className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                <div className="text-xs text-gray-600">Processing Time</div>
                <div className="text-sm font-medium">{analysis.processingTime}s</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <Eye className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                <div className="text-xs text-gray-600">Images</div>
                <div className="text-sm font-medium">
                  {analysis.leftImagePath && analysis.rightImagePath 
                    ? 'Both palms' 
                    : analysis.leftImagePath 
                      ? 'Left palm' 
                      : 'Right palm'
                  }
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="bg-saffron-50 rounded-lg p-4">
              <h4 className="font-medium text-saffron-900 mb-2">Quick Summary</h4>
              <p className="text-saffron-700 text-sm">{analysis.summary}</p>
            </div>
          </CardContent>
        </Card>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'analysis'
                  ? 'border-saffron-500 text-saffron-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Full Analysis
            </button>
            <button
              onClick={() => setActiveTab('conversations')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'conversations'
                  ? 'border-saffron-500 text-saffron-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Conversations ({analysis.conversationCount})
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'analysis' ? (
          <Card>
            <CardHeader>
              <CardTitle>Complete Analysis Report</CardTitle>
              <CardDescription>
                Detailed insights based on traditional Indian palmistry
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <div 
                  className="text-gray-700 leading-relaxed"
                  dangerouslySetInnerHTML={{ 
                    __html: analysis.fullReport.replace(/\n/g, '<br />') 
                  }}
                />
              </div>
            </CardContent>
          </Card>
        ) : (
          <AnalysisConversations analysisId={analysis.id} />
        )}
      </div>
    </DashboardLayout>
  );
}