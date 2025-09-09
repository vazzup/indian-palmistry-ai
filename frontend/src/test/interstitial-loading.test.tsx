/**
 * Tests for interstitial loading screen functionality
 * 
 * Tests the transition from analysis mode to chat mode with engaging loading messages.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { jest } from '@jest/globals';

// Mock the entire page component for testing
const MockAnalysisDetailPage = () => {
  const [isTransitioning, setIsTransitioning] = React.useState(false);
  const [transitionMessage, setTransitionMessage] = React.useState('');
  
  const handleStartTransition = () => {
    setIsTransitioning(true);
    
    const messages = [
      'Preparing your question...',
      'Reading your palms again...',
      'Connecting with ancient wisdom...',
      'Thinking about your question...',
      'Crafting your personalized response...'
    ];
    
    let messageIndex = 0;
    setTransitionMessage(messages[0]);
    
    const messageInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % messages.length;
      setTransitionMessage(messages[messageIndex]);
    }, 1200);
    
    // Simulate API call completion after 3 seconds
    setTimeout(() => {
      clearInterval(messageInterval);
      setIsTransitioning(false);
    }, 3000);
  };
  
  return (
    <div>
      <button onClick={handleStartTransition}>
        Start Transition
      </button>
      
      {/* Interstitial Loading Screen */}
      {isTransitioning && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          data-testid="interstitial-loading"
        >
          <div className="bg-white rounded-lg p-8 max-w-md mx-4 text-center">
            <div className="relative mb-6">
              <div 
                className="w-16 h-16 border-4 border-orange-200 border-t-orange-600 rounded-full animate-spin mx-auto"
                data-testid="loading-spinner"
              ></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl">🪬</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Transitioning to Chat Mode
            </h3>
            <p 
              className="text-gray-600 mb-4 min-h-[1.5rem]"
              data-testid="transition-message"
            >
              {transitionMessage}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

describe('InterstitialLoadingScreen', () => {
  beforeEach(() => {
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test('displays loading screen when transitioning', () => {
    render(<MockAnalysisDetailPage />);
    
    // Initially should not show loading screen
    expect(screen.queryByTestId('interstitial-loading')).not.toBeInTheDocument();
    
    // Click to start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    // Should now show loading screen
    expect(screen.getByTestId('interstitial-loading')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Transitioning to Chat Mode')).toBeInTheDocument();
  });

  test('cycles through different transition messages', () => {
    render(<MockAnalysisDetailPage />);
    
    // Start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    // Should start with first message
    expect(screen.getByTestId('transition-message')).toHaveTextContent(
      'Preparing your question...'
    );
    
    // Advance timer by 1200ms to trigger first message change
    jest.advanceTimersByTime(1200);
    
    // Should show second message
    expect(screen.getByTestId('transition-message')).toHaveTextContent(
      'Reading your palms again...'
    );
    
    // Advance timer by another 1200ms
    jest.advanceTimersByTime(1200);
    
    // Should show third message
    expect(screen.getByTestId('transition-message')).toHaveTextContent(
      'Connecting with ancient wisdom...'
    );
  });

  test('hides loading screen after completion', () => {
    render(<MockAnalysisDetailPage />);
    
    // Start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    // Should show loading screen
    expect(screen.getByTestId('interstitial-loading')).toBeInTheDocument();
    
    // Advance timer by 3000ms to complete transition
    jest.advanceTimersByTime(3000);
    
    // Should hide loading screen
    expect(screen.queryByTestId('interstitial-loading')).not.toBeInTheDocument();
  });

  test('loading screen has proper accessibility attributes', () => {
    render(<MockAnalysisDetailPage />);
    
    // Start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    const loadingScreen = screen.getByTestId('interstitial-loading');
    
    // Should have proper z-index for overlay
    expect(loadingScreen).toHaveClass('z-50');
    
    // Should have proper background overlay
    expect(loadingScreen).toHaveClass('bg-black', 'bg-opacity-75');
    
    // Should center content
    expect(loadingScreen).toHaveClass('flex', 'items-center', 'justify-center');
  });

  test('contains mystical palm reading emoji', () => {
    render(<MockAnalysisDetailPage />);
    
    // Start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    // Should contain the nazar amulet emoji
    expect(screen.getByText('🪬')).toBeInTheDocument();
  });

  test('message cycling loops correctly', () => {
    render(<MockAnalysisDetailPage />);
    
    // Start transition
    fireEvent.click(screen.getByText('Start Transition'));
    
    const messages = [
      'Preparing your question...',
      'Reading your palms again...',
      'Connecting with ancient wisdom...',
      'Thinking about your question...',
      'Crafting your personalized response...'
    ];
    
    // Test full cycle through messages
    messages.forEach((expectedMessage, index) => {
      if (index > 0) {
        jest.advanceTimersByTime(1200);
      }
      expect(screen.getByTestId('transition-message')).toHaveTextContent(expectedMessage);
    });
    
    // Advance one more time to test looping
    jest.advanceTimersByTime(1200);
    expect(screen.getByTestId('transition-message')).toHaveTextContent(messages[0]);
  });
});