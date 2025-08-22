import { test, expect } from '@playwright/test';

test.describe('Critical User Journey', () => {
  test('complete analysis flow with login gate', async ({ page, context }) => {
    // 1. Land on homepage
    await page.goto('/');
    await expect(page.locator('[data-testid="welcome-section"]').or(page.locator('h1:has-text("Indian Palmistry AI")'))).toBeVisible();

    // 2. Check that upload component is visible
    await expect(page.locator('input[type="file"]').or(page.locator('button:has-text("Upload")'))).toBeVisible();

    // For now, we'll test the UI elements since we don't have actual file upload working yet
    // In a real implementation, you would upload a test file here
    
    // 3. Test navigation to auth pages
    const loginButton = page.locator('a[href="/login"], button:has-text("Sign in"), button:has-text("Login")').first();
    if (await loginButton.isVisible()) {
      await loginButton.click();
      await expect(page).toHaveURL(/.*login.*/);
      
      // Check login form elements
      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    }

    // 4. Test registration page
    await page.goto('/register');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // 5. Test navigation back to home
    await page.goto('/');
    await expect(page.locator('h1:has-text("Indian Palmistry AI")')).toBeVisible();
  });

  test('authentication flow', async ({ page }) => {
    // Test login page
    await page.goto('/login');
    
    // Check form validation
    await page.fill('input[type="email"]', 'invalid-email');
    await page.click('button[type="submit"]');
    
    // Should show validation error
    await expect(page.locator('text=/.*valid email.*/i')).toBeVisible();

    // Fill correct format
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'testpass123');
    
    // Try to submit (will fail with API, but form should be valid)
    await page.click('button[type="submit"]');
    
    // Should show loading state or API error
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test('mobile experience optimized', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Test that all interactive elements are at least 44px (touch target minimum)
    const touchTargets = await page.locator('button, [role="button"], input, a').all();
    for (const target of touchTargets) {
      const box = await target.boundingBox();
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }

    // Test mobile navigation works
    await expect(page.locator('h1:has-text("Indian Palmistry AI")')).toBeVisible();
    
    // Test responsive design
    await expect(page.locator('body')).toHaveCSS('font-family', /.*sans.*/);
  });

  test('accessibility compliance', async ({ page }) => {
    await page.goto('/');
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus').first();
    await expect(focusedElement).toBeVisible();
    
    // Test heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
    
    // Test alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
    
    // Test form labels
    const inputs = await page.locator('input').all();
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledby = await input.getAttribute('aria-labelledby');
      
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).first();
        const hasLabel = await label.isVisible().catch(() => false);
        expect(hasLabel || ariaLabel || ariaLabelledby).toBeTruthy();
      }
    }
  });

  test('error handling', async ({ page }) => {
    // Test 404 page
    await page.goto('/non-existent-page');
    // Should either show 404 or redirect to home
    
    // Test network errors
    await page.route('**/api/**', route => route.abort());
    await page.goto('/login');
    
    // Try to submit form with network blocked
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    
    // Should handle network error gracefully
    await expect(page.locator('text=/.*error.*/i, text=/.*failed.*/i')).toBeVisible();
  });

  test('performance benchmarks', async ({ page }) => {
    // Navigate to home page and measure timing
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const endTime = Date.now();
    
    const loadTime = endTime - startTime;
    console.log(`Page load time: ${loadTime}ms`);
    
    // Should load within reasonable time (adjust threshold as needed)
    expect(loadTime).toBeLessThan(5000); // 5 seconds
    
    // Test that main content is visible quickly
    await expect(page.locator('h1:has-text("Indian Palmistry AI")')).toBeVisible();
  });
});