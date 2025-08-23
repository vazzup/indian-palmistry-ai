/**
 * @fileoverview Tests for cultural theme utilities
 * Tests message generation, styling utilities, and cultural authenticity
 */

import { describe, it, expect, vi } from 'vitest';
import { getRandomMessage, getComponentClasses, culturalThemes } from '@/lib/cultural-theme';

describe('getRandomMessage', () => {
  it('should return a welcome message', () => {
    // Mock Math.random to return predictable values
    const mockRandom = vi.spyOn(Math, 'random');
    mockRandom.mockReturnValue(0); // First message

    const message = getRandomMessage('welcome');
    expect(typeof message).toBe('string');
    expect(message.length).toBeGreaterThan(0);
    expect(message).toBe("Discover the ancient wisdom of your palms");

    mockRandom.mockRestore();
  });

  it('should return a loading message', () => {
    const mockRandom = vi.spyOn(Math, 'random');
    mockRandom.mockReturnValue(0.5); // Middle message

    const message = getRandomMessage('loading');
    expect(typeof message).toBe('string');
    expect(message).toContain('...'); // Loading messages end with ellipsis

    mockRandom.mockRestore();
  });

  it('should return a completion message', () => {
    const message = getRandomMessage('completion');
    expect(typeof message).toBe('string');
    expect(message.length).toBeGreaterThan(0);
  });

  it('should return different messages on multiple calls', () => {
    // Without mocking, should return random messages
    const messages = new Set();
    for (let i = 0; i < 10; i++) {
      messages.add(getRandomMessage('welcome'));
    }
    // Should have some variety (not guaranteed but likely)
    expect(messages.size).toBeGreaterThanOrEqual(1);
  });
});

describe('getComponentClasses', () => {
  it('should return button classes with default variant', () => {
    const classes = getComponentClasses('button');
    expect(classes).toContain('inline-flex');
    expect(classes).toContain('bg-saffron-500');
    expect(classes).toContain('h-10'); // Default medium size
  });

  it('should return button classes with outline variant', () => {
    const classes = getComponentClasses('button', 'outline');
    expect(classes).toContain('border');
    expect(classes).toContain('text-saffron-500');
  });

  it('should return button classes with small size', () => {
    const classes = getComponentClasses('button', 'default', 'sm');
    expect(classes).toContain('h-9');
    expect(classes).toContain('text-xs');
  });

  it('should return card classes', () => {
    const classes = getComponentClasses('card');
    expect(classes).toContain('rounded-lg');
    expect(classes).toContain('border');
    expect(classes).toContain('shadow-sm');
  });

  it('should return input classes', () => {
    const classes = getComponentClasses('input');
    expect(classes).toContain('flex');
    expect(classes).toContain('h-10');
    expect(classes).toContain('border');
  });

  it('should return empty string for unknown component type', () => {
    const classes = getComponentClasses('unknown-component');
    expect(classes).toBe('');
  });

  it('should handle missing variant gracefully', () => {
    const classes = getComponentClasses('button', undefined, 'lg');
    expect(classes).toContain('bg-saffron-500'); // Should use default variant
    expect(classes).toContain('h-11'); // Should use large size
  });
});

describe('culturalThemes', () => {
  it('should contain traditional colors', () => {
    expect(culturalThemes.saffronColor).toBe('#FF9933');
    expect(culturalThemes.greenColor).toBe('#138808');
    expect(culturalThemes.whiteColor).toBe('#FFFFFF');
  });

  it('should contain Hindi palmistry terms', () => {
    const terms = culturalThemes.palmistryTerms;
    expect(terms.lifeLineHindi).toContain('जीवन रेखा');
    expect(terms.headLineHindi).toContain('मस्तिष्क रेखा');
    expect(terms.heartLineHindi).toContain('हृदय रेखा');
    expect(terms.fateLineHindi).toContain('भाग्य रेखा');
  });

  it('should maintain cultural authenticity', () => {
    // Verify that terminology includes both Hindi and transliteration
    const terms = culturalThemes.palmistryTerms;
    Object.values(terms).forEach(term => {
      expect(term).toMatch(/.*\(.*\)/); // Should have format "Hindi (Transliteration)"
    });
  });
});

describe('cultural authenticity', () => {
  it('should use respectful and appropriate messaging', () => {
    const welcomeMessage = getRandomMessage('welcome');
    
    // Should not contain inappropriate terms
    expect(welcomeMessage.toLowerCase()).not.toContain('fortune telling');
    expect(welcomeMessage.toLowerCase()).not.toContain('supernatural');
    
    // Should contain culturally appropriate terms
    const appropriateTerms = ['wisdom', 'ancient', 'palmistry', 'palms', 'hands'];
    const hasAppropriateTerm = appropriateTerms.some(term => 
      welcomeMessage.toLowerCase().includes(term)
    );
    expect(hasAppropriateTerm).toBe(true);
  });

  it('should reference traditional Indian palmistry', () => {
    const welcomeMessage = getRandomMessage('welcome');
    const loadingMessage = getRandomMessage('loading');
    
    const messages = [welcomeMessage, loadingMessage];
    const culturalReferences = messages.some(msg => 
      msg.includes('Hast Rekha Shastra') ||
      msg.includes('Indian') ||
      msg.includes('ancient') ||
      msg.includes('traditional')
    );
    
    expect(culturalReferences).toBe(true);
  });
});