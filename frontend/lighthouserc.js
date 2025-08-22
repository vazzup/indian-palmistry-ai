module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/login',
        'http://localhost:3000/register',
        'http://localhost:3000/dashboard',
      ],
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'ready',
      startServerReadyTimeout: 30000,
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.9 }],
        'categories:pwa': ['warn', { minScore: 0.8 }],
        
        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        
        // Additional performance metrics
        'speed-index': ['warn', { maxNumericValue: 3000 }],
        'interactive': ['warn', { maxNumericValue: 3800 }],
        
        // Security and best practices
        'uses-https': 'error',
        'is-on-https': 'error',
        'redirects-http': 'warn',
        
        // PWA specific
        'installable-manifest': 'warn',
        'apple-touch-icon': 'warn',
        'themed-omnibox': 'warn',
        
        // Accessibility
        'color-contrast': 'error',
        'image-alt': 'error',
        'label': 'error',
        'link-name': 'error',
        'button-name': 'error',
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};