/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { OptimizedImage } from '@/components/ui/OptimizedImage';

// Mock Next.js Image component
jest.mock('next/image', () => {
  return function MockImage({ src, alt, onLoad, onError, ...props }: any) {
    return (
      <img
        src={src}
        alt={alt}
        onLoad={onLoad}
        onError={onError}
        data-testid="next-image"
        {...props}
      />
    );
  };
});

describe('OptimizedImage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render with basic props', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', '/test-image.jpg');
    expect(image).toHaveAttribute('alt', 'Test image');
  });

  it('should show loading skeleton initially', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  it('should hide loading skeleton when image loads', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');
    const skeleton = screen.getByTestId('image-skeleton');

    expect(skeleton).toBeVisible();

    // Simulate image load
    fireEvent.load(image);

    expect(skeleton).toHaveStyle('opacity: 0');
  });

  it('should show error message when image fails to load', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');

    // Simulate image error
    fireEvent.error(image);

    expect(screen.getByText('Failed to load image')).toBeInTheDocument();
    expect(screen.queryByTestId('image-skeleton')).not.toBeVisible();
  });

  it('should use custom error message', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        errorMessage="Custom error message"
      />
    );

    const image = screen.getByTestId('next-image');
    fireEvent.error(image);

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
  });

  it('should apply correct container classes', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        className="custom-class"
      />
    );

    const container = screen.getByTestId('next-image').parentElement;
    expect(container).toHaveClass('relative', 'overflow-hidden', 'custom-class');
  });

  it('should set correct skeleton dimensions', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toHaveStyle({ width: '400px', height: '300px' });
  });

  it('should handle responsive dimensions with aspect ratio', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        fill
        sizes="(max-width: 768px) 100vw, 50vw"
      />
    );

    const container = screen.getByTestId('next-image').parentElement;
    expect(container).toHaveClass('relative');
  });

  it('should show loading skeleton with proper animation', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toHaveClass('animate-pulse', 'bg-gray-200', 'rounded');
  });

  it('should maintain aspect ratio during loading', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={800}
        height={600}
      />
    );

    const skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toHaveStyle({
      width: '800px',
      height: '600px',
    });
  });

  it('should handle image load transition smoothly', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');
    const skeleton = screen.getByTestId('image-skeleton');

    // Initially skeleton is visible, image is hidden
    expect(skeleton).toHaveStyle('opacity: 1');
    expect(image).toHaveStyle('opacity: 0');

    // After load, image becomes visible, skeleton fades
    fireEvent.load(image);

    expect(image).toHaveStyle('opacity: 1');
    expect(skeleton).toHaveStyle('opacity: 0');
  });

  it('should apply transition classes', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');
    const skeleton = screen.getByTestId('image-skeleton');

    expect(image).toHaveClass('transition-opacity', 'duration-300');
    expect(skeleton).toHaveClass('transition-opacity', 'duration-300');
  });

  it('should handle placeholder blur with Next.js Image props', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,..."
      />
    );

    const image = screen.getByTestId('next-image');
    expect(image).toHaveAttribute('placeholder', 'blur');
    expect(image).toHaveAttribute('blurDataURL', 'data:image/jpeg;base64,...');
  });

  it('should pass through all Next.js Image props', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        quality={85}
        priority
        loading="eager"
        sizes="100vw"
      />
    );

    const image = screen.getByTestId('next-image');
    expect(image).toHaveAttribute('quality', '85');
    expect(image).toHaveAttribute('priority', '');
    expect(image).toHaveAttribute('loading', 'eager');
    expect(image).toHaveAttribute('sizes', '100vw');
  });

  it('should handle error state styling', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');
    fireEvent.error(image);

    const errorContainer = screen.getByText('Failed to load image').parentElement;
    expect(errorContainer).toHaveClass(
      'flex',
      'items-center',
      'justify-center',
      'bg-gray-100',
      'text-gray-500',
      'text-sm'
    );
  });

  it('should handle multiple load/error cycles', () => {
    const { rerender } = render(
      <OptimizedImage
        src="/test-image-1.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    const image = screen.getByTestId('next-image');

    // First load succeeds
    fireEvent.load(image);
    expect(screen.queryByTestId('image-skeleton')).toHaveStyle('opacity: 0');

    // Change src (new image)
    rerender(
      <OptimizedImage
        src="/test-image-2.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    // Should show skeleton again for new image
    expect(screen.getByTestId('image-skeleton')).toHaveStyle('opacity: 1');

    // New image fails to load
    fireEvent.error(screen.getByTestId('next-image'));
    expect(screen.getByText('Failed to load image')).toBeInTheDocument();
  });

  it('should handle dynamic dimensions', () => {
    const { rerender } = render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={200}
        height={200}
      />
    );

    let skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toHaveStyle({ width: '200px', height: '200px' });

    // Change dimensions
    rerender(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
      />
    );

    skeleton = screen.getByTestId('image-skeleton');
    expect(skeleton).toHaveStyle({ width: '400px', height: '300px' });
  });
});