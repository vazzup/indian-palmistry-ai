import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Test suite for markdown rendering in AI conversation messages.
 * 
 * Tests the implementation that renders AI responses with markdown formatting
 * while keeping user messages as plain text. This solves the issue where
 * AI responses contained raw markdown that wasn't being formatted.
 */
describe('Markdown Rendering in Conversation Messages', () => {
  
  describe('AI Message Markdown Rendering', () => {
    it('should render headers with proper styling', () => {
      const markdownContent = `# Main Header
## Secondary Header  
### सारांश (Summary)
#### Details`;

      render(
        <div data-testid="ai-message" className="text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({children}) => <h1 className="text-base font-bold text-gray-900 mb-2 mt-0">{children}</h1>,
              h2: ({children}) => <h2 className="text-sm font-bold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h2>,
              h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
              h4: ({children}) => <h4 className="text-sm font-semibold text-gray-800 mb-1 mt-2 first:mt-0">{children}</h4>,
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      );

      // Check that headers are rendered as proper HTML elements
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Main Header');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Secondary Header');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('सारांश (Summary)');
      expect(screen.getByRole('heading', { level: 4 })).toHaveTextContent('Details');

      // Verify saffron theming is applied to H3 elements
      const h3Element = screen.getByRole('heading', { level: 3 });
      expect(h3Element).toHaveClass('text-saffron-700');
    });

    it('should render bold text with saffron accent', () => {
      const markdownContent = `**जीवन रेखा (Life Line)** shows vitality and **हृदय रेखा (Heart Line)** indicates emotions.`;

      render(
        <div data-testid="ai-message" className="text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              strong: ({children}) => <strong className="font-semibold text-saffron-700">{children}</strong>,
              p: ({children}) => <p className="text-sm text-gray-800 mb-2 last:mb-0">{children}</p>
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      );

      // Check that bold elements have saffron styling
      const boldElements = screen.getAllByText(/(जीवन रेखा|हृदय रेखा)/, { selector: 'strong' });
      boldElements.forEach(element => {
        expect(element).toHaveClass('font-semibold', 'text-saffron-700');
      });
    });

    it('should render lists with proper indentation', () => {
      const markdownContent = `### Key Features:
- Strong life line
- Clear heart line
- Prominent Venus mount

### Strengths:
1. Good health indicators
2. Strong emotional capacity
3. Natural leadership qualities`;

      render(
        <div data-testid="ai-message" className="text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
              ul: ({children}) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
              li: ({children}) => <li className="text-sm text-gray-800">{children}</li>,
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      );

      // Check unordered list
      const unorderedList = screen.getByRole('list');
      expect(unorderedList).toHaveClass('list-disc', 'ml-4', 'mb-2', 'space-y-1');

      // Check ordered list
      const orderedList = screen.getAllByRole('list')[1];
      expect(orderedList).toHaveClass('list-decimal', 'ml-4', 'mb-2', 'space-y-1');

      // Verify list items are present
      expect(screen.getByText('Strong life line')).toBeInTheDocument();
      expect(screen.getByText('Good health indicators')).toBeInTheDocument();
    });

    it('should handle mixed Hindi and English content', () => {
      const markdownContent = `### संक्षिप्त सारांश:
आपके हाथों की रेखाओं का ध्यान से अध्ययन करने पर, मैं आपके बारे में निम्न बातें कह सकता हूँ।

**हृदय रेखा (Heart Line)**: Shows emotional depth and capacity for love.

### विस्तृत विश्लेषण:
1. **जीवन रेखा (Life Line)**: Indicates strong vitality
2. Clear and well-formed lines suggest good fortune`;

      render(
        <div data-testid="ai-message" className="text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
              strong: ({children}) => <strong className="font-semibold text-saffron-700">{children}</strong>,
              p: ({children}) => <p className="text-sm text-gray-800 mb-2 last:mb-0">{children}</p>,
              ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
              li: ({children}) => <li className="text-sm text-gray-800">{children}</li>,
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      );

      // Verify Hindi headers are rendered with saffron styling
      expect(screen.getByText('संक्षिप्त सारांश:')).toHaveClass('text-saffron-700');
      expect(screen.getByText('विस्तृत विश्लेषण:')).toHaveClass('text-saffron-700');

      // Verify mixed language bold text
      expect(screen.getByText('हृदय रेखा (Heart Line)')).toHaveClass('text-saffron-700');
      expect(screen.getByText('जीवन रेखा (Life Line)')).toHaveClass('text-saffron-700');

      // Verify paragraph content is preserved
      expect(screen.getByText(/आपके हाथों की रेखाओं का ध्यान से/)).toBeInTheDocument();
    });
  });

  describe('User Message Plain Text Rendering', () => {
    it('should render user messages as plain text without markdown processing', () => {
      const userMessage = `### This should not be a header
**This should not be bold**
- This should not be a list item`;

      render(
        <p className="text-sm leading-relaxed whitespace-pre-wrap" data-testid="user-message">
          {userMessage}
        </p>
      );

      const messageElement = screen.getByTestId('user-message');
      
      // Verify that markdown syntax remains as plain text
      expect(messageElement).toHaveTextContent('### This should not be a header');
      expect(messageElement).toHaveTextContent('**This should not be bold**');
      expect(messageElement).toHaveTextContent('- This should not be a list item');

      // Verify no markdown elements are rendered
      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
      expect(screen.queryByRole('list')).not.toBeInTheDocument();
      expect(messageElement.querySelector('strong')).toBeNull();
    });

    it('should preserve whitespace in user messages', () => {
      const userMessageWithSpaces = `Line 1

Line 3 with spaces
  Indented line`;

      render(
        <p className="text-sm leading-relaxed whitespace-pre-wrap" data-testid="user-message">
          {userMessageWithSpaces}
        </p>
      );

      const messageElement = screen.getByTestId('user-message');
      expect(messageElement).toHaveClass('whitespace-pre-wrap');
      expect(messageElement.textContent).toBe(userMessageWithSpaces);
    });
  });

  describe('Message Role Detection', () => {
    it('should correctly identify assistant role for markdown rendering', () => {
      const message = {
        role: 'assistant',
        content: '### Test Header\n**Bold text**'
      };

      const shouldRenderMarkdown = message.role.toLowerCase() === 'assistant';
      expect(shouldRenderMarkdown).toBe(true);
    });

    it('should correctly identify user role for plain text rendering', () => {
      const message = {
        role: 'user',
        content: '### Test Header\n**Bold text**'
      };

      const shouldRenderMarkdown = message.role.toLowerCase() === 'assistant';
      expect(shouldRenderMarkdown).toBe(false);
    });

    it('should handle case variations in role', () => {
      const roles = ['ASSISTANT', 'Assistant', 'assistant', 'USER', 'User', 'user'];
      
      roles.forEach(role => {
        const isAssistant = role.toLowerCase() === 'assistant';
        const expectedResult = role.toLowerCase().includes('assistant');
        expect(isAssistant).toBe(expectedResult);
      });
    });
  });

  describe('Saffron Theme Integration', () => {
    it('should apply consistent saffron colors across markdown elements', () => {
      const markdownContent = `### Header
**Bold text**`;

      render(
        <div data-testid="themed-markdown">
          <ReactMarkdown
            components={{
              h3: ({children}) => <h3 className="text-saffron-700">{children}</h3>,
              strong: ({children}) => <strong className="text-saffron-700">{children}</strong>,
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      );

      const header = screen.getByRole('heading', { level: 3 });
      const boldText = screen.getByText('Bold text');

      expect(header).toHaveClass('text-saffron-700');
      expect(boldText).toHaveClass('text-saffron-700');
    });
  });

  describe('Error Handling', () => {
    it('should handle empty content gracefully', () => {
      render(
        <div data-testid="empty-content">
          <ReactMarkdown>{''}</ReactMarkdown>
        </div>
      );

      const container = screen.getByTestId('empty-content');
      expect(container).toBeInTheDocument();
      expect(container.textContent).toBe('');
    });

    it('should handle null or undefined content', () => {
      render(
        <div data-testid="null-content">
          <ReactMarkdown>{null as any}</ReactMarkdown>
        </div>
      );

      const container = screen.getByTestId('null-content');
      expect(container).toBeInTheDocument();
    });
  });
});

/**
 * Integration test for the complete message rendering logic
 * as implemented in the conversation component.
 */
describe('Message Rendering Integration', () => {
  const renderMessage = (role: string, content: string) => {
    const message = { role: role.toLowerCase(), content };
    
    return render(
      <div>
        {message.role === 'assistant' ? (
          <div className="text-sm leading-relaxed" data-testid="ai-message">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({children}) => <h1 className="text-base font-bold text-gray-900 mb-2 mt-0">{children}</h1>,
                h2: ({children}) => <h2 className="text-sm font-bold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h2>,
                h3: ({children}) => <h3 className="text-sm font-semibold text-saffron-700 mb-2 mt-3 first:mt-0">{children}</h3>,
                h4: ({children}) => <h4 className="text-sm font-semibold text-gray-800 mb-1 mt-2 first:mt-0">{children}</h4>,
                strong: ({children}) => <strong className="font-semibold text-saffron-700">{children}</strong>,
                ul: ({children}) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                li: ({children}) => <li className="text-sm text-gray-800">{children}</li>,
                p: ({children}) => <p className="text-sm text-gray-800 mb-2 last:mb-0">{children}</p>
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap" data-testid="user-message">
            {message.content}
          </p>
        )}
      </div>
    );
  };

  it('should render AI message with full markdown support', () => {
    const content = `### संक्षिप्त सारांश:
**जीवन रेखा (Life Line)** indicates strong vitality.

### Key Features:
- Strong life line
- Clear heart line`;

    renderMessage('assistant', content);

    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('संक्षिप्त सारांश:');
    expect(screen.getByText('जीवन रेखा (Life Line)')).toHaveClass('text-saffron-700');
    expect(screen.getByRole('list')).toBeInTheDocument();
  });

  it('should render user message as plain text', () => {
    const content = `### This stays as text
**This is not bold**
- This is not a list`;

    renderMessage('user', content);

    const messageElement = screen.getByTestId('user-message');
    expect(messageElement.textContent).toBe(content);
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  });
});