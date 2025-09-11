'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface LegalDocumentProps {
  title: string;
  content: string;
  lastUpdated?: string;
  effectiveDate?: string;
  onBack?: () => void;
}

/**
 * LegalDocument component for rendering Terms, Privacy Policy, and Disclaimer pages.
 * 
 * Features:
 * - Consistent saffron theming matching app design
 * - Markdown rendering with custom styling
 * - Mobile-responsive layout
 * - Print-friendly styling
 * - Back navigation support
 * - Professional legal document formatting
 */
export const LegalDocument: React.FC<LegalDocumentProps> = ({
  title,
  content,
  lastUpdated,
  effectiveDate,
  onBack
}) => {
  return (
    <div className="min-h-screen bg-background py-6 px-4 md:px-6 lg:px-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-4">
          {onBack && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              icon={<ArrowLeft className="w-4 h-4" />}
              className="text-saffron-600 hover:text-saffron-700"
            >
              Back
            </Button>
          )}
          <div className="flex-1" />
        </div>
        
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">{title}</h1>
          <div className="text-sm text-muted-foreground space-x-4">
            {effectiveDate && (
              <span>Effective Date: {effectiveDate}</span>
            )}
            {lastUpdated && (
              <span>Last Updated: {lastUpdated}</span>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-8 md:p-12">
            <div className="prose prose-lg max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Main headings with saffron theming
                  h1: ({children}) => (
                    <h1 className="text-2xl font-bold text-gray-900 mb-6 mt-8 first:mt-0 border-b border-saffron-200 pb-3">
                      {children}
                    </h1>
                  ),
                  h2: ({children}) => (
                    <h2 className="text-xl font-bold text-gray-900 mb-4 mt-8 first:mt-0 text-saffron-700">
                      {children}
                    </h2>
                  ),
                  h3: ({children}) => (
                    <h3 className="text-lg font-semibold text-gray-800 mb-3 mt-6 first:mt-0">
                      {children}
                    </h3>
                  ),
                  h4: ({children}) => (
                    <h4 className="text-base font-semibold text-gray-800 mb-2 mt-4 first:mt-0">
                      {children}
                    </h4>
                  ),
                  // Paragraphs with proper spacing
                  p: ({children}) => (
                    <p className="text-gray-700 mb-4 leading-relaxed">
                      {children}
                    </p>
                  ),
                  // Lists with proper styling
                  ul: ({children}) => (
                    <ul className="list-disc ml-6 mb-4 space-y-2 text-gray-700">
                      {children}
                    </ul>
                  ),
                  ol: ({children}) => (
                    <ol className="list-decimal ml-6 mb-4 space-y-2 text-gray-700">
                      {children}
                    </ol>
                  ),
                  li: ({children}) => (
                    <li className="leading-relaxed">{children}</li>
                  ),
                  // Emphasis and strong text
                  strong: ({children}) => (
                    <strong className="font-semibold text-gray-900">
                      {children}
                    </strong>
                  ),
                  em: ({children}) => (
                    <em className="italic text-gray-800">{children}</em>
                  ),
                  // Code styling
                  code: ({children}) => (
                    <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">
                      {children}
                    </code>
                  ),
                  // Blockquotes
                  blockquote: ({children}) => (
                    <blockquote className="border-l-4 border-saffron-300 pl-4 my-4 italic text-gray-600">
                      {children}
                    </blockquote>
                  ),
                  // Links with saffron theming
                  a: ({children, href}) => (
                    <a 
                      href={href}
                      className="text-saffron-600 hover:text-saffron-700 underline"
                      target={href?.startsWith('http') ? '_blank' : undefined}
                      rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
                    >
                      {children}
                    </a>
                  ),
                  // Tables (if any)
                  table: ({children}) => (
                    <div className="overflow-x-auto my-6">
                      <table className="min-w-full divide-y divide-gray-200">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({children}) => (
                    <thead className="bg-saffron-50">
                      {children}
                    </thead>
                  ),
                  th: ({children}) => (
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      {children}
                    </th>
                  ),
                  td: ({children}) => (
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                      {children}
                    </td>
                  ),
                  // Horizontal rules
                  hr: () => (
                    <hr className="my-8 border-t border-saffron-200" />
                  )
                }}
              >
                {content}
              </ReactMarkdown>
            </div>

            {/* Footer notice */}
            <div className="mt-12 pt-8 border-t border-saffron-200">
              <div className="text-center text-sm text-muted-foreground space-y-2">
                <p>
                  This document is part of the Indian Palmistry AI service terms.
                </p>
                <p>
                  For questions about this document, please contact us through our support channels.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Print styles */}
      <style jsx>{`
        @media print {
          .no-print { display: none !important; }
          .prose { font-size: 12pt; line-height: 1.4; }
          .prose h1 { font-size: 18pt; margin-top: 0; }
          .prose h2 { font-size: 16pt; }
          .prose h3 { font-size: 14pt; }
          .prose h4 { font-size: 12pt; }
          .max-w-4xl { max-width: none; }
          .px-4, .px-6, .px-8, .px-12 { padding-left: 1rem; padding-right: 1rem; }
        }
      `}</style>
    </div>
  );
};