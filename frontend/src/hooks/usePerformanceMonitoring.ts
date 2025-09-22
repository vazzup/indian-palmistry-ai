import { useEffect } from 'react';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}

declare global {
  interface Window {
    gtag?: (command: string, action: string, params?: any) => void;
  }
}

export const usePerformanceMonitoring = () => {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const sendToAnalytics = (metric: PerformanceMetric) => {
      // Send to Google Analytics if available
      if (window.gtag) {
        window.gtag('event', metric.name, {
          event_category: 'Web Vitals',
          value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
          metric_rating: metric.rating,
          non_interaction: true,
        });
      }

    };

    const getRating = (name: string, value: number): 'good' | 'needs-improvement' | 'poor' => {
      const thresholds = {
        CLS: [0.1, 0.25],
        FCP: [1800, 3000],
        FID: [100, 300],
        LCP: [2500, 4000],
        TTFB: [800, 1800],
      };

      const [good, poor] = thresholds[name as keyof typeof thresholds] || [0, 0];
      
      if (value <= good) return 'good';
      if (value <= poor) return 'needs-improvement';
      return 'poor';
    };

    // Dynamically import web-vitals
    import('web-vitals').then((webVitals) => {
      // Handle both old and new web-vitals API
      const { onCLS, onFCP, onLCP, onTTFB } = webVitals;
      // onFID has been replaced with onINP in newer versions of web-vitals
      
      onCLS?.(metric => {
        sendToAnalytics({
          name: 'CLS',
          value: metric.value,
          rating: getRating('CLS', metric.value),
        });
      });

      // FID is deprecated in favor of INP, skip for now

      onFCP?.(metric => {
        sendToAnalytics({
          name: 'FCP',
          value: metric.value,
          rating: getRating('FCP', metric.value),
        });
      });

      onLCP?.(metric => {
        sendToAnalytics({
          name: 'LCP',
          value: metric.value,
          rating: getRating('LCP', metric.value),
        });
      });

      onTTFB?.(metric => {
        sendToAnalytics({
          name: 'TTFB',
          value: metric.value,
          rating: getRating('TTFB', metric.value),
        });
      });
    });
  }, []);

  const measureCustomMetric = (name: string, startTime: number, endTime?: number) => {
    const duration = endTime ? endTime - startTime : performance.now() - startTime;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`Custom Metric [${name}]:`, `${duration.toFixed(2)}ms`);
    }

    // Send to analytics
    if (window.gtag) {
      window.gtag('event', 'custom_metric', {
        event_category: 'Performance',
        metric_name: name,
        duration: Math.round(duration),
        non_interaction: true,
      });
    }

    return duration;
  };

  const measureApiCall = async <T>(
    name: string,
    apiCall: () => Promise<T>
  ): Promise<T> => {
    const startTime = performance.now();
    
    try {
      const result = await apiCall();
      const duration = performance.now() - startTime;
      
      measureCustomMetric(`api_${name}`, startTime, startTime + duration);
      
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      
      if (window.gtag) {
        window.gtag('event', 'api_error', {
          event_category: 'Performance',
          api_name: name,
          duration: Math.round(duration),
          non_interaction: true,
        });
      }
      
      throw error;
    }
  };

  return {
    measureCustomMetric,
    measureApiCall,
  };
};