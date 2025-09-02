/**
 * @fileoverview A/B Testing utility for conversion optimization
 * Simple client-side A/B testing with persistent storage
 */

interface ABTestConfig {
  testId: string;
  variants: string[];
  weights?: number[]; // Optional weights for each variant
}

interface ABTestResult {
  variant: string;
  testId: string;
}

/**
 * Get the assigned variant for a user
 * Uses localStorage to persist assignment across sessions
 */
export function getABTestVariant(config: ABTestConfig): ABTestResult {
  const { testId, variants, weights } = config;
  
  // Check if user already has an assigned variant
  const storageKey = `ab_test_${testId}`;
  const existingVariant = localStorage.getItem(storageKey);
  
  if (existingVariant && variants.includes(existingVariant)) {
    return { variant: existingVariant, testId };
  }
  
  // Assign new variant based on weights or equal distribution
  let variant: string;
  
  if (weights && weights.length === variants.length) {
    // Use weighted distribution
    const random = Math.random();
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
    let cumulativeWeight = 0;
    
    for (let i = 0; i < variants.length; i++) {
      cumulativeWeight += weights[i] / totalWeight;
      if (random <= cumulativeWeight) {
        variant = variants[i];
        break;
      }
    }
    variant = variants[variants.length - 1]; // Fallback
  } else {
    // Equal distribution
    const randomIndex = Math.floor(Math.random() * variants.length);
    variant = variants[randomIndex];
  }
  
  // Store assignment
  localStorage.setItem(storageKey, variant);
  
  return { variant, testId };
}

/**
 * Track A/B test events for analytics
 */
export function trackABTestEvent(
  testId: string, 
  variant: string, 
  event: string, 
  properties?: Record<string, any>
) {
  // Store event data (could be sent to analytics service)
  const eventData = {
    testId,
    variant,
    event,
    timestamp: new Date().toISOString(),
    properties: properties || {},
  };
  
  // Store locally for now (could be sent to analytics API)
  const eventsKey = 'ab_test_events';
  const existingEvents = JSON.parse(localStorage.getItem(eventsKey) || '[]');
  existingEvents.push(eventData);
  
  // Keep only last 100 events to prevent storage bloat
  const recentEvents = existingEvents.slice(-100);
  localStorage.setItem(eventsKey, JSON.stringify(recentEvents));
  
  // Optional: Send to analytics service
  console.log('AB Test Event:', eventData);
}

/**
 * Hook for using A/B tests in React components
 */
export function useABTest(config: ABTestConfig) {
  const [result, setResult] = React.useState<ABTestResult | null>(null);
  const [isClient, setIsClient] = React.useState(false);
  
  React.useEffect(() => {
    // Mark as client-side after hydration
    setIsClient(true);
  }, []);
  
  React.useEffect(() => {
    // Only run on client side after hydration
    if (isClient && typeof window !== 'undefined') {
      const testResult = getABTestVariant(config);
      setResult(testResult);
    }
  }, [isClient, config.testId]);
  
  const track = React.useCallback((event: string, properties?: Record<string, any>) => {
    if (result && typeof window !== 'undefined') {
      trackABTestEvent(result.testId, result.variant, event, properties);
    }
  }, [result]);
  
  return { 
    variant: result?.variant || config.variants[0], // Fallback to first variant
    testId: result?.testId || config.testId,
    isReady: result !== null && isClient,
    track
  };
}

// Import React for the hook
import React from 'react';