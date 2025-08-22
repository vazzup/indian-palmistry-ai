'use client';

import React from 'react';
import { usePerformanceMonitoring } from '@/hooks/usePerformanceMonitoring';

interface PerformanceProviderProps {
  children: React.ReactNode;
}

export const PerformanceProvider: React.FC<PerformanceProviderProps> = ({ children }) => {
  usePerformanceMonitoring();
  
  return <>{children}</>;
};