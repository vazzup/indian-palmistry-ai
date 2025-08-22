'use client';

import React, { Suspense, lazy } from 'react';
import { Spinner } from './Spinner';

interface LazyLoadProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  className?: string;
}

export const LazyLoad: React.FC<LazyLoadProps> = ({ 
  children, 
  fallback,
  className = '' 
}) => {
  const defaultFallback = (
    <div className={`flex items-center justify-center py-8 ${className}`}>
      <Spinner message="Loading..." />
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      {children}
    </Suspense>
  );
};

// Utility function to create lazy-loaded components
export const createLazyComponent = <T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
): React.ComponentType<React.ComponentProps<T>> => {
  const LazyComponent = lazy(importFn);
  
  return (props: React.ComponentProps<T>) => (
    <LazyLoad>
      <LazyComponent {...props} />
    </LazyLoad>
  );
};

// Pre-defined lazy components for common heavy components
export const LazyDashboard = createLazyComponent(
  () => import('@/app/(dashboard)/dashboard/page')
);

export const LazyAnalysisDetail = createLazyComponent(
  () => import('@/app/(dashboard)/analyses/[id]/page')
);

export const LazyConversationInterface = createLazyComponent(
  () => import('@/components/conversation/AnalysisConversations')
);