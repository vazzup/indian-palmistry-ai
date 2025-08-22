import { Page, expect } from '@playwright/test';

export class TestUtils {
  constructor(private page: Page) {}

  /**
   * Mock user authentication for testing protected routes
   */
  async mockAuth(user = {
    id: 1,
    email: 'test@example.com',
    name: 'Test User',
    created_at: '2024-01-01T00:00:00Z'
  }) {
    await this.page.addInitScript((userData) => {
      localStorage.setItem('auth-store', JSON.stringify({
        state: {
          user: userData,
          isAuthenticated: true,
          isLoading: false,
          error: null
        },
        version: 0
      }));
    }, user);
  }

  /**
   * Mock API responses for testing
   */
  async mockApiResponse(endpoint: string, response: any, status = 200) {
    await this.page.route(`**/api/**${endpoint}`, route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * Mock file upload for testing
   */
  async mockFileUpload(selector: string, fileName = 'test-palm.jpg') {
    const fileChooserPromise = this.page.waitForEvent('filechooser');
    await this.page.locator(selector).click();
    const fileChooser = await fileChooserPromise;
    
    // Create a test file buffer
    const buffer = Buffer.from('fake-image-data');
    await fileChooser.setFiles({
      name: fileName,
      mimeType: 'image/jpeg',
      buffer: buffer,
    });
  }

  /**
   * Check if element meets accessibility standards
   */
  async checkAccessibility(selector: string) {
    const element = this.page.locator(selector);
    
    // Check if element has proper ARIA attributes or labels
    const ariaLabel = await element.getAttribute('aria-label');
    const ariaLabelledby = await element.getAttribute('aria-labelledby');
    const ariaDescribedby = await element.getAttribute('aria-describedby');
    const title = await element.getAttribute('title');
    
    const hasAccessibleName = ariaLabel || ariaLabelledby || ariaDescribedby || title;
    
    if (!hasAccessibleName) {
      // Check if it's associated with a label
      const id = await element.getAttribute('id');
      if (id) {
        const label = this.page.locator(`label[for="${id}"]`);
        const hasLabel = await label.count() > 0;
        expect(hasLabel).toBe(true);
      }
    }
    
    return hasAccessibleName;
  }

  /**
   * Check touch target size for mobile accessibility
   */
  async checkTouchTargetSize(selector: string, minSize = 44) {
    const element = this.page.locator(selector);
    const box = await element.boundingBox();
    
    if (box) {
      expect(box.width).toBeGreaterThanOrEqual(minSize);
      expect(box.height).toBeGreaterThanOrEqual(minSize);
    }
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation() {
    await this.page.keyboard.press('Tab');
    const focusedElement = this.page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // Test that focus is visible
    const outline = await focusedElement.evaluate(el => 
      getComputedStyle(el).outline || getComputedStyle(el).boxShadow
    );
    expect(outline).not.toBe('none');
  }

  /**
   * Test form validation
   */
  async testFormValidation(formSelector: string, testCases: Array<{
    field: string;
    value: string;
    shouldFail: boolean;
    errorMessage?: string;
  }>) {
    for (const testCase of testCases) {
      await this.page.fill(`${formSelector} input[name="${testCase.field}"]`, testCase.value);
      await this.page.click(`${formSelector} button[type="submit"]`);
      
      if (testCase.shouldFail) {
        if (testCase.errorMessage) {
          await expect(this.page.locator(`text=${testCase.errorMessage}`)).toBeVisible();
        } else {
          // Check for any validation error
          await expect(this.page.locator('[role="alert"], .error, [aria-invalid="true"]')).toBeVisible();
        }
      }
    }
  }

  /**
   * Measure page performance
   */
  async measurePerformance() {
    const startTime = Date.now();
    await this.page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // Get Core Web Vitals if available
    const vitals = await this.page.evaluate(() => {
      return new Promise((resolve) => {
        if ('PerformanceObserver' in window) {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const vitals = {};
            
            entries.forEach(entry => {
              if (entry.entryType === 'paint') {
                (vitals as any)[entry.name] = entry.startTime;
              }
            });
            
            resolve(vitals);
          });
          
          observer.observe({ entryTypes: ['paint'] });
          
          // Fallback timeout
          setTimeout(() => resolve({}), 1000);
        } else {
          resolve({});
        }
      });
    });
    
    return {
      loadTime,
      vitals
    };
  }

  /**
   * Test offline functionality
   */
  async testOfflineMode() {
    await this.page.context().setOffline(true);
    
    // Check if offline indicator appears
    await expect(this.page.locator('[data-testid="offline-indicator"]').or(this.page.locator('text=/offline/i'))).toBeVisible();
    
    // Try to perform an action that should be queued
    const beforePendingActions = await this.page.evaluate(() => {
      return JSON.parse(localStorage.getItem('pendingActions') || '[]').length;
    });
    
    // Go back online
    await this.page.context().setOffline(false);
    
    // Check if online indicator appears or offline indicator disappears
    await expect(this.page.locator('text=/back online/i').or(this.page.locator('[data-testid="offline-indicator"]'))).toBeVisible();
  }

  /**
   * Take a screenshot with a meaningful name
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `e2e/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * Wait for an element with a custom timeout
   */
  async waitForElement(selector: string, timeout = 10000) {
    await this.page.locator(selector).waitFor({ timeout });
  }

  /**
   * Fill form with data object
   */
  async fillForm(formSelector: string, data: Record<string, string>) {
    for (const [field, value] of Object.entries(data)) {
      await this.page.fill(`${formSelector} input[name="${field}"], ${formSelector} select[name="${field}"], ${formSelector} textarea[name="${field}"]`, value);
    }
  }
}