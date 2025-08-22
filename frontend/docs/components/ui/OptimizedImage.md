# OptimizedImage Component

A performance-optimized image component built on Next.js Image with loading states, error handling, and smooth transitions for the Indian Palmistry AI application.

## Overview

The `OptimizedImage` component extends Next.js Image component with enhanced UX features including skeleton loading animations, graceful error handling, and smooth opacity transitions during image load.

## Features

- **Next.js Image Integration**: Built on Next.js Image for automatic optimization
- **Loading Skeleton**: Animated skeleton placeholder during image load
- **Error Handling**: Graceful fallback when images fail to load
- **Smooth Transitions**: Opacity transitions for professional loading experience
- **Responsive Support**: Full support for Next.js responsive image features
- **Accessibility**: Proper alt text and loading states for screen readers
- **Cultural Styling**: Consistent with saffron-based design system

## Usage

### Basic Image

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

function ProfilePicture() {
  return (
    <OptimizedImage
      src="/images/profile.jpg"
      alt="User profile picture"
      width={200}
      height={200}
      className="rounded-full"
    />
  );
}
```

### Responsive Image with Sizes

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

function HeroImage() {
  return (
    <OptimizedImage
      src="/images/hero-palm.jpg"
      alt="Palm reading analysis"
      width={1200}
      height={800}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      priority
      className="w-full h-auto"
    />
  );
}
```

### Fill Container with Aspect Ratio

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

function AnalysisImage() {
  return (
    <div className="relative w-full aspect-[4/3]">
      <OptimizedImage
        src="/images/palm-analysis.jpg"
        alt="Palm analysis result"
        fill
        sizes="(max-width: 768px) 100vw, 50vw"
        className="object-cover rounded-lg"
      />
    </div>
  );
}
```

### Custom Error Message

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

function GalleryImage({ src, alt }: { src: string; alt: string }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={300}
      height={300}
      errorMessage="Image could not be loaded"
      className="rounded-lg shadow-sm"
    />
  );
}
```

### Priority Loading for Above-the-Fold

```tsx
import { OptimizedImage } from '@/components/ui/OptimizedImage';

function FeaturedAnalysis() {
  return (
    <OptimizedImage
      src="/images/featured-analysis.jpg"
      alt="Featured palm analysis"
      width={600}
      height={400}
      priority
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      className="w-full rounded-xl"
    />
  );
}
```

## Props

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `src` | `string` | Image source URL |
| `alt` | `string` | Alternative text for accessibility |
| `width` | `number` | Image width (required unless using `fill`) |
| `height` | `number` | Image height (required unless using `fill`) |

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `errorMessage` | `string` | `"Failed to load image"` | Custom error message when image fails to load |
| `className` | `string` | `""` | Additional CSS classes for the container |

All other props from Next.js Image component are supported and passed through, including:

- `fill` - Fill the parent container
- `sizes` - Responsive sizes attribute
- `priority` - Load image with high priority
- `placeholder` - Placeholder type (`blur`, `empty`)
- `blurDataURL` - Base64 encoded placeholder image
- `quality` - Image quality (1-100)
- `loading` - Loading behavior (`lazy`, `eager`)

## Loading States

### Skeleton Animation

The component displays an animated skeleton placeholder while the image loads:

```tsx
// Skeleton styling
<div
  className="absolute inset-0 bg-gray-200 animate-pulse rounded transition-opacity duration-300"
  style={{ width, height }}
  data-testid="image-skeleton"
/>
```

### Smooth Transitions

Images fade in smoothly when loaded:

```tsx
// Image with opacity transition
<Image
  className="transition-opacity duration-300"
  style={{ opacity: loaded ? 1 : 0 }}
  onLoad={() => setLoaded(true)}
  // ... other props
/>
```

## Error Handling

When an image fails to load, the component displays a user-friendly error message:

```tsx
// Error state display
{hasError && (
  <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500 text-sm rounded">
    {errorMessage}
  </div>
)}
```

Common error scenarios:
- Network connectivity issues
- Invalid image URLs
- Server errors (404, 500)
- Corrupted image files
- Authentication/permission issues

## Responsive Behavior

### Mobile-First Design

The component follows mobile-first responsive principles:

```tsx
<OptimizedImage
  src="/images/responsive-palm.jpg"
  alt="Palm reading"
  width={800}
  height={600}
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  className="w-full h-auto"
/>
```

### Touch Target Optimization

When used as interactive elements, ensures 44px minimum touch targets:

```tsx
<button className="min-w-[44px] min-h-[44px] p-2">
  <OptimizedImage
    src="/icons/action.png"
    alt="Action button"
    width={24}
    height={24}
  />
</button>
```

## Performance Optimization

### Lazy Loading

Images are lazy-loaded by default unless `priority` is set:

```tsx
// Lazy loaded (default)
<OptimizedImage src="/image.jpg" alt="..." width={400} height={300} />

// Priority loaded (above-the-fold)
<OptimizedImage 
  src="/hero.jpg" 
  alt="..." 
  width={1200} 
  height={800} 
  priority 
/>
```

### Image Formats

Next.js automatically serves modern image formats (WebP, AVIF) when supported:

```tsx
// Automatically optimized formats
<OptimizedImage
  src="/palm.jpg"  // Served as WebP/AVIF if supported
  alt="Palm analysis"
  width={600}
  height={400}
  quality={85}  // Balanced quality/size
/>
```

### Placeholder Blur

Use placeholder blur for smooth loading experience:

```tsx
<OptimizedImage
  src="/analysis.jpg"
  alt="Analysis result"
  width={500}
  height={375}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."  // Generated at build time
/>
```

## Accessibility Features

### Screen Reader Support

- Proper `alt` text descriptions
- Loading states communicated to assistive technology
- Error messages are accessible

```tsx
<OptimizedImage
  src="/palm-reading.jpg"
  alt="Detailed palm reading showing major lines and mounts"
  width={400}
  height={300}
/>
```

### Focus Management

The component maintains proper focus flow and doesn't interfere with keyboard navigation.

## Styling Integration

### Cultural Design System

The component integrates with the saffron-based design system:

```tsx
<OptimizedImage
  src="/cultural-pattern.jpg"
  alt="Indian cultural pattern"
  width={200}
  height={200}
  className="rounded-lg border-2 border-saffron-200 shadow-saffron-100/50"
/>
```

### Tailwind Classes

Common styling patterns:

```tsx
// Rounded with shadow
<OptimizedImage className="rounded-xl shadow-lg" />

// Full width responsive
<OptimizedImage className="w-full h-auto" />

// Aspect ratio container
<div className="aspect-square">
  <OptimizedImage fill className="object-cover" />
</div>
```

## Testing

The component includes comprehensive tests:

```typescript
// Test loading states
it('should show loading skeleton initially', () => {
  render(<OptimizedImage src="/test.jpg" alt="Test" width={400} height={300} />);
  expect(screen.getByTestId('image-skeleton')).toBeInTheDocument();
});

// Test error handling
it('should show error message when image fails to load', () => {
  render(<OptimizedImage src="/invalid.jpg" alt="Test" width={400} height={300} />);
  fireEvent.error(screen.getByRole('img'));
  expect(screen.getByText('Failed to load image')).toBeInTheDocument();
});

// Test smooth transitions
it('should fade in when image loads', () => {
  render(<OptimizedImage src="/test.jpg" alt="Test" width={400} height={300} />);
  const image = screen.getByRole('img');
  
  expect(image).toHaveStyle('opacity: 0');
  fireEvent.load(image);
  expect(image).toHaveStyle('opacity: 1');
});
```

## Best Practices

### Image Optimization

1. **Use appropriate dimensions** - Don't load oversized images
2. **Set quality wisely** - Balance quality vs file size (75-85 is often optimal)
3. **Use priority loading** for above-the-fold images
4. **Provide blur placeholders** for important images

### Accessibility

1. **Write descriptive alt text** - Describe the image content, not just its purpose
2. **Use empty alt for decorative images** - `alt=""` for purely decorative content
3. **Consider context** - Alt text should make sense within the surrounding content

### Performance

1. **Use responsive sizing** - Provide appropriate sizes attribute
2. **Lazy load by default** - Only use priority for critical images
3. **Optimize source images** - Start with high-quality, properly sized images
4. **Monitor Core Web Vitals** - Use performance monitoring to track image loading

## Common Patterns

### Image Gallery

```tsx
function ImageGallery({ images }: { images: Array<{src: string, alt: string}> }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {images.map((image, index) => (
        <OptimizedImage
          key={index}
          src={image.src}
          alt={image.alt}
          width={300}
          height={300}
          className="rounded-lg hover:scale-105 transition-transform"
        />
      ))}
    </div>
  );
}
```

### Avatar with Fallback

```tsx
function UserAvatar({ user }: { user: { avatar?: string, name: string } }) {
  return (
    <div className="relative w-12 h-12">
      {user.avatar ? (
        <OptimizedImage
          src={user.avatar}
          alt={`${user.name} avatar`}
          fill
          className="rounded-full object-cover"
          errorMessage={user.name.charAt(0)}
        />
      ) : (
        <div className="w-full h-full bg-saffron-100 text-saffron-600 rounded-full flex items-center justify-center font-medium">
          {user.name.charAt(0).toUpperCase()}
        </div>
      )}
    </div>
  );
}
```

## Related Components

- **[LazyLoad](./LazyLoad.md)** - Component-level lazy loading
- **[Card](./Card.md)** - Often contains OptimizedImage components
- **[Spinner](./Spinner.md)** - Alternative loading indicator

## Dependencies

- **Next.js** - Built on Next.js Image component
- **React** - React hooks for state management
- **Tailwind CSS** - Styling and animations