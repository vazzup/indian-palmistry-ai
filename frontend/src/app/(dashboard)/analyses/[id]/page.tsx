'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Hand, 
  ArrowLeft,
  Eye,
  Calendar,
  Clock,
  DollarSign
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';
import { analysisApi, handleApiError } from '@/lib/api';
import { LoadingPage } from '@/components/ui/Spinner';
import type { Analysis } from '@/types';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const analysisId = params.id as string;
  
  const [analysis, setAnalysis] = React.useState<Analysis | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  
  React.useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const analysisData = await analysisApi.getAnalysis(analysisId);
        setAnalysis(analysisData);
      } catch (err: any) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    
    if (analysisId) {
      fetchAnalysis();
    }
  }, [analysisId]);
  
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
  
  if (loading) {
    return <LoadingPage message="Loading your full palm reading..." />;
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
          
          <div className="flex items-center space-x-2">
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
              
              {analysis.cost && (
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium">Cost</p>
                    <p className="text-xs text-gray-600">
                      ${analysis.cost.toFixed(4)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* TODO: Add conversation section when ready */}
      </div>
    </DashboardLayout>
  );
}