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
import { readingApi, handleApiError } from '@/lib/api';
import { LoadingPage } from '@/components/ui/Spinner';
import type { Reading } from '@/types';

export default function ReadingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const analysisId = params.id as string;
  
  const [reading, setReading] = React.useState<Reading | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  
  React.useEffect(() => {
    const fetchReading = async () => {
      try {
        setLoading(true);
        const readingData = await readingApi.getReading(analysisId);
        setReading(readingData);
      } catch (err: any) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    
    if (analysisId) {
      fetchReading();
    }
  }, [analysisId]);
  
  // Redirect anonymous users to summary page to encourage signup
  React.useEffect(() => {
    if (!isAuthenticated) {
      router.push(`/reading/${analysisId}/summary`);
    }
  }, [isAuthenticated, analysisId, router]);
  
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
  
  if (error || !reading) {
    return (
      <DashboardLayout
        title="Reading Not Found"
        description="Unable to load this palm reading"
      >
        <Card>
          <CardContent className="py-12 text-center">
            <Eye className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Reading Not Found
            </h3>
            <p className="text-gray-600 mb-4">
              {error || 'This palm reading could not be found or you may not have access to it.'}
            </p>
            <Button onClick={() => router.push('/readings')}>
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
      title={`Reading #${reading.id}`}
      description={`Created on ${formatDate(reading.created_at)}`}
    >
      <div className="space-y-6">
        {/* Back Button */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => router.push('/readings')}
            className="flex items-center"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Readings
          </Button>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              Status: 
              <span className={`ml-1 font-medium ${
                reading.status === 'COMPLETED' ? 'text-green-600' :
                reading.status === 'PROCESSING' ? 'text-yellow-600' : 
                'text-red-600'
              }`}>
                {reading.status}
              </span>
            </span>
          </div>
        </div>

        {/* Reading Summary */}
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
                {reading.summary || 'No summary available.'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Full Report */}
        {reading.full_report && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-saffron-600" />
                Detailed Reading
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-wrap text-gray-700">
                  {reading.full_report}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Reading Metadata */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">
              Reading Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <div>
                  <p className="text-sm font-medium">Created</p>
                  <p className="text-xs text-gray-600">
                    {formatDate(reading.created_at)}
                  </p>
                </div>
              </div>
              
              {reading.processing_started_at && reading.processing_completed_at && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium">Processing Time</p>
                    <p className="text-xs text-gray-600">
                      {Math.round((new Date(reading.processing_completed_at).getTime() - 
                                   new Date(reading.processing_started_at).getTime()) / 1000)} seconds
                    </p>
                  </div>
                </div>
              )}
              
              {reading.cost && (
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium">Cost</p>
                    <p className="text-xs text-gray-600">
                      ${reading.cost.toFixed(4)}
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