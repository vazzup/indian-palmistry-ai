'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Crown, History, MessageCircle, Shield, Sparkles, Star } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
// import { useABTest } from '@/lib/ab-testing';

interface ValuePropCardProps {
  className?: string;
  onSignUp?: () => void;
  enableABTest?: boolean;
}

/**
 * ValuePropCard - Component highlighting benefits of signing up
 * Features:
 * - Clear value propositions for authenticated users
 * - Cultural design with saffron theme
 * - Compelling call-to-action
 * - Mobile-optimized layout
 * - Benefits that differentiate from guest experience
 */
export const ValuePropCard: React.FC<ValuePropCardProps> = ({ 
  className = '',
  onSignUp,
  enableABTest = true
}) => {
  const router = useRouter();
  
  // A/B Test for value proposition messaging (temporarily disabled)
  // const { variant, track, isReady } = useABTest({
  //   testId: 'valueprop_messaging',
  //   variants: ['benefits', 'social_proof'],
  //   weights: [0.5, 0.5]
  // });
  const variant = 'benefits';
  const track = (_event: string, _properties?: Record<string, any>) => {};
  
  const handleSignUp = () => {
    // Track conversion event
    if (enableABTest) {
      // track('signup_clicked', { source: 'value_prop_card' });
    }
    
    if (onSignUp) {
      onSignUp();
    } else {
      router.push('/register');
    }
  };
  
  const benefits = [
    {
      icon: <History className="w-5 h-5 text-saffron-600" />,
      title: 'Save Your Readings',
      description: 'Keep all your palm readings and revisit insights anytime'
    },
    {
      icon: <MessageCircle className="w-5 h-5 text-saffron-600" />,
      title: 'Ask Questions',
      description: 'Get personalized answers about your palm reading results'
    },
    {
      icon: <Crown className="w-5 h-5 text-saffron-600" />,
      title: 'Premium Features',
      description: 'Access advanced analysis and detailed compatibility reports'
    },
    {
      icon: <Shield className="w-5 h-5 text-saffron-600" />,
      title: 'Secure & Private',
      description: 'Your personal readings are encrypted and kept confidential'
    }
  ];
  
  return (
    <Card className={`bg-gradient-to-br from-saffron-50 via-orange-50 to-amber-50 border-saffron-200 ${className}`}>
      <CardHeader className="text-center pb-4">
        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-saffron-400 to-saffron-600 rounded-full flex items-center justify-center mb-3">
          <Star className="w-8 h-8 text-white" />
        </div>
        <CardTitle className="text-xl text-gray-900">
          Unlock Your Full Reading Experience
        </CardTitle>
        <CardDescription className="text-gray-600">
          Sign up to save your readings, ask questions, and access premium features
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Benefits Grid */}
        <div className="space-y-4">
          {benefits.map((benefit, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
                {benefit.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 text-sm">
                  {benefit.title}
                </h4>
                <p className="text-xs text-gray-600 mt-1">
                  {benefit.description}
                </p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Call to Action */}
        <div className="pt-4 border-t border-saffron-200">
          <Button 
            onClick={handleSignUp}
            size="lg"
            className="w-full bg-gradient-to-r from-saffron-500 to-saffron-600 hover:from-saffron-600 hover:to-saffron-700 text-white shadow-lg"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Create Free Account
          </Button>
          
          <p className="text-xs text-center text-gray-600 mt-2">
            Free to join • No credit card required • 30-second signup
          </p>
        </div>
      </CardContent>
    </Card>
  );
};