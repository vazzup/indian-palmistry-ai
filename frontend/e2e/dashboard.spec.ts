import { test, expect } from '@playwright/test';

test.describe('Dashboard Functionality', () => {
  // Mock login to access protected pages
  test.beforeEach(async ({ page }) => {
    // Mock authentication state
    await page.addInitScript(() => {
      localStorage.setItem('auth-store', JSON.stringify({
        state: {
          user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User',
            created_at: '2024-01-01T00:00:00Z'
          },
          isAuthenticated: true
        },
        version: 0
      }));
    });
  });

  test('dashboard loads with user data', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check if dashboard content loads
    await expect(page.locator('text=/good morning|good afternoon|good evening/i')).toBeVisible();
    await expect(page.locator('text=/Test User/i').or(page.locator('text=/there/i'))).toBeVisible();
    
    // Check stats cards
    await expect(page.locator('text=/total readings/i')).toBeVisible();
    await expect(page.locator('text=/conversations/i')).toBeVisible();
    
    // Check quick actions
    await expect(page.locator('button:has-text("New Reading")')).toBeVisible();
  });

  test('analyses page functionality', async ({ page }) => {
    await page.goto('/analyses');
    
    // Should show analyses page
    await expect(page.locator('h1:has-text("My Readings"), h2:has-text("My Readings")')).toBeVisible();
    
    // Check for new reading button
    await expect(page.locator('button:has-text("New Reading")')).toBeVisible();
    
    // Check search functionality
    const searchInput = page.locator('input[placeholder*="Search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('test search');
      await expect(searchInput).toHaveValue('test search');
    }
    
    // Check filter options
    const statusFilter = page.locator('select').first();
    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('completed');
    }
  });

  test('profile page functionality', async ({ page }) => {
    await page.goto('/profile');
    
    // Should show profile page
    await expect(page.locator('h1:has-text("Profile"), h2:has-text("Profile")')).toBeVisible();
    
    // Check form fields
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
    
    // Test edit functionality
    const editButton = page.locator('button:has-text("Edit Profile")');
    if (await editButton.isVisible()) {
      await editButton.click();
      
      // Should enable form fields
      await expect(page.locator('input[name="name"]')).toBeEnabled();
      
      // Test cancel
      const cancelButton = page.locator('button:has-text("Cancel")');
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
      }
    }
  });

  test('navigation between dashboard pages', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test navigation to analyses
    const analysesLink = page.locator('a[href="/analyses"], button:has-text("My Analyses")');
    if (await analysesLink.isVisible()) {
      await analysesLink.click();
      await expect(page).toHaveURL(/.*analyses.*/);
    }
    
    // Test navigation to profile
    await page.goto('/dashboard');
    const profileLink = page.locator('a[href="/profile"], button:has-text("Profile")');
    if (await profileLink.isVisible()) {
      await profileLink.click();
      await expect(page).toHaveURL(/.*profile.*/);
    }
    
    // Test back to dashboard
    await page.goto('/dashboard');
    await expect(page.locator('text=/dashboard/i')).toBeVisible();
  });

  test('responsive dashboard layout', async ({ page }) => {
    // Test desktop layout
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/dashboard');
    
    // Should show sidebar on desktop
    await expect(page.locator('[class*="sidebar"], nav')).toBeVisible();
    
    // Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Should show mobile header/menu
    await expect(page.locator('button[aria-label*="menu"], button:has([class*="menu"])')).toBeVisible();
  });

  test('logout functionality', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Find and click logout button
    const logoutButton = page.locator('button:has-text("Sign out"), button:has-text("Logout")');
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      
      // Should redirect to home or login page
      await expect(page).toHaveURL(/.*\/(login|\/)?$/);
    }
  });

  test('error states handling', async ({ page }) => {
    // Mock API errors
    await page.route('**/api/**', route => route.abort());
    
    await page.goto('/dashboard');
    
    // Should handle failed API calls gracefully
    // The dashboard should still load with cached/default data
    await expect(page.locator('text=/dashboard/i, h1, h2')).toBeVisible();
  });
});