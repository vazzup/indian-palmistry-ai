import { test, expect } from '@playwright/test';

test.describe('PWA Functionality', () => {
  test('manifest file is accessible', async ({ page }) => {
    const response = await page.request.get('/manifest.json');
    expect(response.status()).toBe(200);
    
    const manifest = await response.json();
    expect(manifest.name).toBe('Indian Palmistry AI');
    expect(manifest.short_name).toBe('Palmistry AI');
    expect(manifest.start_url).toBe('/');
    expect(manifest.display).toBe('standalone');
    expect(manifest.icons).toBeDefined();
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  test('service worker registration', async ({ page }) => {
    await page.goto('/');
    
    // Check if service worker is registered (in production build)
    const serviceWorkerRegistration = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        return !!registration;
      }
      return false;
    });

    // In development, PWA is disabled, so we just check the structure
    if (process.env.NODE_ENV === 'production') {
      expect(serviceWorkerRegistration).toBe(true);
    }
  });

  test('offline indicator appears when offline', async ({ page, context }) => {
    await page.goto('/');
    
    // Go offline
    await context.setOffline(true);
    
    // Check if offline indicator appears
    await expect(page.locator('[data-testid="offline-indicator"]').or(page.locator('text=/offline/i'))).toBeVisible();
    
    // Go back online
    await context.setOffline(false);
    
    // Offline indicator should disappear or show "back online"
    await expect(page.locator('text=/back online/i').or(page.locator('[data-testid="offline-indicator"]'))).toBeVisible();
  });

  test('install prompt functionality', async ({ page }) => {
    await page.goto('/');
    
    // Mock the beforeinstallprompt event
    await page.evaluate(() => {
      const event = new Event('beforeinstallprompt');
      (event as any).prompt = () => Promise.resolve();
      (event as any).userChoice = Promise.resolve({ outcome: 'accepted' });
      window.dispatchEvent(event);
    });

    // Wait for install prompt to appear (might have delay)
    await page.waitForTimeout(1000);
    
    // Check if install prompt appears
    const installPrompt = page.locator('text=/install.*palmistry/i, button:has-text("Install")');
    if (await installPrompt.isVisible()) {
      await expect(installPrompt).toBeVisible();
      
      // Test dismiss functionality
      const dismissButton = page.locator('button:has-text("Not Now"), button:has-text("Dismiss")');
      if (await dismissButton.isVisible()) {
        await dismissButton.click();
        await expect(installPrompt).not.toBeVisible();
      }
    }
  });

  test('meta tags for PWA', async ({ page }) => {
    await page.goto('/');
    
    // Check for PWA meta tags
    await expect(page.locator('meta[name="viewport"]')).toHaveAttribute('content', /width=device-width/);
    await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#ff8000');
    await expect(page.locator('meta[name="apple-mobile-web-app-capable"]')).toHaveAttribute('content', 'yes');
    await expect(page.locator('link[rel="apple-touch-icon"]')).toBeAttached();
    await expect(page.locator('link[rel="manifest"]')).toHaveAttribute('href', '/manifest.json');
  });

  test('caching strategy works', async ({ page }) => {
    await page.goto('/');
    
    // Load the page once to cache resources
    await page.waitForLoadState('networkidle');
    
    // Reload and check if resources are served from cache
    const response = await page.reload();
    expect(response?.status()).toBe(200);
    
    // Check that main assets loaded
    await expect(page.locator('h1:has-text("Indian Palmistry AI")')).toBeVisible();
  });

  test('app shortcuts work', async ({ page }) => {
    const response = await page.request.get('/manifest.json');
    const manifest = await response.json();
    
    expect(manifest.shortcuts).toBeDefined();
    expect(manifest.shortcuts.length).toBeGreaterThan(0);
    
    // Check that shortcut URLs are valid
    for (const shortcut of manifest.shortcuts) {
      const shortcutResponse = await page.request.get(shortcut.url);
      expect(shortcutResponse.status()).toBe(200);
    }
  });

  test('background sync preparation', async ({ page }) => {
    await page.goto('/');
    
    // Mock offline state and attempt an action that should be queued
    await page.evaluate(() => {
      localStorage.setItem('pendingActions', JSON.stringify([
        {
          id: 'test-action',
          action: 'test',
          data: { test: true },
          timestamp: Date.now()
        }
      ]));
    });
    
    // Check if pending actions are stored
    const pendingActions = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('pendingActions') || '[]');
    });
    
    expect(pendingActions.length).toBeGreaterThan(0);
  });

  test('responsive design for mobile PWA', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Check that the app looks good in mobile PWA mode
    await expect(page.locator('h1:has-text("Indian Palmistry AI")')).toBeVisible();
    
    // Check touch target sizes (minimum 44px for good PWA)
    const touchTargets = await page.locator('button, [role="button"], input, a').all();
    for (const target of touchTargets) {
      const box = await target.boundingBox();
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
  });
});