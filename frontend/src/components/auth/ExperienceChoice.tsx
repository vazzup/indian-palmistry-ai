'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ChevronRight, Eye, User, Zap } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
// import { useABTest } from '@/lib/ab-testing';

interface ExperienceChoiceProps {
  className?: string;
  onGuestChoice?: () => void;
  onAuthChoice?: () => void;
  enableABTest?: boolean;
}

/**
 * ExperienceChoice - Dual path selection component
 * Features:
 * - Clear choice between guest and authenticated experience
 * - Visual comparison of features
 * - Cultural design elements
 * - Mobile-first responsive design
 * - A/B testing ready structure
 */
export const ExperienceChoice: React.FC<ExperienceChoiceProps> = ({ 
  className = '',
  onGuestChoice,
  onAuthChoice,
  enableABTest = true
}) => {
  const router = useRouter();
  
  // A/B Test for experience choice presentation (temporarily disabled)
  // const { variant, track, isReady } = useABTest({
  //   testId: 'experience_choice_layout',
  //   variants: ['side_by_side', 'recommended_first'],
  //   weights: [0.5, 0.5]
  // });
  const variant = 'side_by_side';
  const track = (_event: string, _properties?: Record<string, any>) => {};
  
  const handleGuestChoice = () => {
    if (enableABTest) {
      // track('guest_experience_chosen', { layout: variant });
    }
    
    if (onGuestChoice) {
      onGuestChoice();
    }
    // The parent component (HomePage) handles the guest flow
  };
  
  const handleAuthChoice = () => {
    if (enableABTest) {
      // track('auth_experience_chosen', { layout: variant });
    }
    
    if (onAuthChoice) {
      onAuthChoice();
    } else {
      router.push('/register');
    }
  };
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Section Header */}
      <div className="text-center space-y-2 mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Choose Your Experience
        </h3>
        <p className="text-sm text-gray-600">
          Start with a quick reading or create an account for the full experience
        </p>
      </div>
      
      {/* Choice Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Guest Experience */}
        <Card className="relative border-2 border-gray-200 hover:border-gray-300 transition-colors">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                <Eye className="w-5 h-5 text-gray-600" />
              </div>
              <div>
                <CardTitle className="text-base text-gray-900">Quick Reading</CardTitle>
                <CardDescription className="text-xs">Try it now</CardDescription>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Instant palm reading summary</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Basic personality insights</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                <span className="text-gray-400">No saving or history</span>
              </div>
            </div>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleGuestChoice}
              className="w-full group border-gray-300 hover:border-gray-400"
            >
              Start Reading
              <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
            </Button>
          </CardContent>
        </Card>
        
        {/* Authenticated Experience */}
        <Card className="relative border-2 border-saffron-300 bg-gradient-to-br from-saffron-50 to-orange-50 hover:border-saffron-400 transition-colors">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-saffron-100 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-saffron-600" />
              </div>
              <div>
                <CardTitle className="text-base text-gray-900">Full Experience</CardTitle>
                <CardDescription className="text-xs text-saffron-700">Recommended</CardDescription>
              </div>
            </div>
            {/* Popular Badge */}
            <div className="absolute -top-2 -right-2">
              <div className="bg-saffron-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                Popular
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-gray-700">
                <div className="w-1.5 h-1.5 bg-saffron-500 rounded-full"></div>
                <span>Complete detailed reading</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-700">
                <div className="w-1.5 h-1.5 bg-saffron-500 rounded-full"></div>
                <span>Save and revisit readings</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-700">
                <div className="w-1.5 h-1.5 bg-saffron-500 rounded-full"></div>
                <span>Ask follow-up questions</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-700">
                <div className="w-1.5 h-1.5 bg-saffron-500 rounded-full"></div>
                <span>Premium features & insights</span>
              </div>
            </div>
            
            <Button 
              size="sm"
              onClick={handleAuthChoice}
              className="w-full bg-saffron-500 hover:bg-saffron-600 text-white group"
            >
              <Zap className="w-4 h-4 mr-1" />
              Sign Up Free
              <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
            </Button>
            
            <p className="text-xs text-center text-gray-600">
              30-second signup • No credit card
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Bottom Note */}
      <div className="text-center mt-4">
        <p className="text-xs text-gray-600">
          You can always upgrade to the full experience later
        </p>
      </div>
    </div>
  );
};