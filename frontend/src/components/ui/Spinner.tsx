import React from 'react';
import { Loader2, Circle } from 'lucide-react';
import { getRandomMessage } from '@/lib/cultural-theme';
import type { ComponentSize } from '@/types';

interface SpinnerProps {
  size?: ComponentSize | 'xs';
  message?: string;
  type?: 'default' | 'cultural' | 'minimal';
  showMessage?: boolean;
}

const sizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

export const Spinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  message, 
  type = 'default',
  showMessage = false 
}) => {
  const [culturalMessage] = React.useState(() => 
    message || getRandomMessage('loading')
  );
  
  if (type === 'minimal') {
    return (
      <div className="inline-flex items-center gap-2">
        <Loader2 className={`${sizeClasses[size]} animate-spin text-saffron-500`} />
        {showMessage && (
          <span className="text-sm text-muted-foreground">{culturalMessage}</span>
        )}
      </div>
    );
  }
  
  if (type === 'cultural') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        {/* Cultural lotus-inspired spinner */}
        <div className="relative">
          <div className={`${sizeClasses[size]} cultural-spinner`} />
          <div 
            className={`${sizeClasses[size]} absolute inset-0 border-2 border-saffron-100 rounded-full opacity-50`}
            style={{
              animation: 'cultural-spin 2s linear infinite reverse',
            }}
          />
        </div>
        
        {showMessage && (
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-saffron-700">{culturalMessage}</p>
            <div className="flex space-x-1 justify-center">
              <Circle className="w-1 h-1 fill-saffron-400 text-saffron-400 animate-bounce" />
              <Circle className="w-1 h-1 fill-saffron-400 text-saffron-400 animate-bounce delay-75" />
              <Circle className="w-1 h-1 fill-saffron-400 text-saffron-400 animate-bounce delay-150" />
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // Default spinner
  return (
    <div className="inline-flex items-center gap-2">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-saffron-500`} />
      {showMessage && (
        <span className="text-sm text-muted-foreground">{culturalMessage}</span>
      )}
    </div>
  );
};

// Full page loading component
interface LoadingPageProps {
  message?: string;
}

export const LoadingPage: React.FC<LoadingPageProps> = ({ message }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Spinner 
        size="xl" 
        type="cultural" 
        message={message}
        showMessage={true}
      />
    </div>
  );
};

// Loading overlay component
interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  isVisible, 
  message 
}) => {
  if (!isVisible) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background rounded-lg p-8 shadow-lg max-w-sm mx-4">
        <Spinner 
          size="lg" 
          type="cultural" 
          message={message}
          showMessage={true}
        />
      </div>
    </div>
  );
};