# SecureForm Component

A security-enhanced form component that provides built-in CSRF protection, input sanitization, and rate limiting for the Indian Palmistry AI application.

## Overview

The `SecureForm` component wraps the standard HTML form element with additional security features, making it easy to create secure forms throughout the application without repeating security logic.

## Features

- **CSRF Protection**: Automatically includes CSRF tokens in form submissions
- **Input Sanitization**: Sanitizes form inputs to prevent XSS attacks
- **Rate Limiting**: Prevents form submission abuse with configurable limits
- **Loading States**: Disables form during submission to prevent double-submission
- **Error Handling**: Displays user-friendly error messages
- **Cultural Design**: Consistent with the saffron-based design system

## Usage

### Basic Form

```tsx
import { SecureForm } from '@/components/ui/SecureForm';

function MyForm() {
  const handleSubmit = async (formData: FormData, sanitizedData: Record<string, any>) => {
    // Form submission logic
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Submission failed');
    }
  };

  return (
    <SecureForm onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <input name="message" type="text" required />
      <button type="submit">Submit</button>
    </SecureForm>
  );
}
```

### Form with Rate Limiting

```tsx
<SecureForm
  onSubmit={handleSubmit}
  rateLimitKey="contact-form"
  maxAttempts={3}
>
  <input name="email" type="email" required />
  <textarea name="message" required />
  <button type="submit">Send Message</button>
</SecureForm>
```

### Form without Input Sanitization

```tsx
<SecureForm
  onSubmit={handleSubmit}
  sanitizeInputs={false}
>
  <input name="richText" type="text" />
  <button type="submit">Submit</button>
</SecureForm>
```

## Props

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `onSubmit` | `(formData: FormData, sanitizedData: Record<string, any>) => void \| Promise<void>` | Form submission handler |
| `children` | `React.ReactNode` | Form content and inputs |

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rateLimitKey` | `string` | `undefined` | Key for rate limiting this specific form |
| `maxAttempts` | `number` | `5` | Maximum submission attempts for rate limiting |
| `sanitizeInputs` | `boolean` | `true` | Whether to sanitize form inputs |
| `className` | `string` | `""` | Additional CSS classes |

All standard HTML form attributes are also supported and passed through to the underlying form element.

## Security Features

### CSRF Protection

The component automatically includes CSRF tokens in form submissions:

```tsx
// Automatically added hidden input
<input type="hidden" name="csrf_token" value="..." />
```

The CSRF token is:
- Fetched automatically via the `useCSRF` hook
- Included in both FormData and sanitized data objects
- Updated in DOM meta tags for axios interceptors

### Input Sanitization

By default, all string inputs are sanitized to remove:

- Script tags (`<script>...</script>`)
- JavaScript protocols (`javascript:...`)
- Event handlers (`onclick`, `onload`, etc.)

```tsx
// Example sanitization
const input = '<script>alert("xss")</script>Hello';
const sanitized = 'Hello'; // Script tag removed
```

### Rate Limiting

Rate limiting prevents form submission abuse:

```tsx
<SecureForm
  rateLimitKey="login-form"
  maxAttempts={5}
  onSubmit={handleLogin}
>
  {/* Form content */}
</SecureForm>
```

Rate limiting features:
- Per-form key tracking
- Configurable attempt limits
- 15-minute reset windows
- Graceful error messages

## Form States

### Loading State

During form submission:
- All form inputs are disabled via `<fieldset disabled>`
- Submit buttons show loading state
- Form cannot be resubmitted

### Error State

When submission fails:
- Error message displayed above form content
- Cultural error styling (red with warm tones)
- Error clears on next submission attempt

### Rate Limited State

When rate limit is exceeded:
- Submission prevented
- User-friendly error message shown
- Form remains functional after reset period

## Styling

The component uses Tailwind CSS classes following the cultural design system:

```css
/* Error message styling */
.error-message {
  @apply mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600;
}

/* Disabled form styling */
fieldset:disabled {
  @apply opacity-50 pointer-events-none;
}
```

## Accessibility

The component includes several accessibility features:

- **Error Messages**: Properly associated with the form
- **Loading States**: Communicated via disabled attributes
- **Focus Management**: Maintains focus flow during state changes
- **Screen Reader Support**: Error messages are announced

## Data Flow

1. **Form Submission**: User submits form
2. **Rate Limiting**: Check if submission is allowed
3. **CSRF Token**: Add token to form data
4. **Sanitization**: Clean user inputs (if enabled)
5. **Handler Call**: Execute `onSubmit` with both raw and sanitized data
6. **Error Handling**: Display any errors from submission
7. **State Reset**: Return form to normal state

## Integration with Backend

The component integrates seamlessly with the FastAPI backend:

```tsx
const handleSubmit = async (formData: FormData, sanitizedData: Record<string, any>) => {
  // FormData includes CSRF token automatically
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: formData, // Includes csrf_token
  });
  
  // Or use sanitized data for JSON requests
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sanitizedData), // Includes csrf_token
  });
};
```

## Testing

The component is thoroughly tested with:

- Form submission with and without CSRF tokens
- Input sanitization verification
- Rate limiting behavior
- Error state handling
- Loading state management
- Accessibility compliance

## Best Practices

1. **Always use for user input forms**
2. **Set appropriate rate limits** based on form type
3. **Handle submission errors gracefully**
4. **Test with various input types**
5. **Consider disabling sanitization only when necessary**
6. **Provide clear error messages**

## Related Components

- **[Input](./Input.md)** - Form input components
- **[Button](./Button.md)** - Submit buttons with loading states
- **[LoginForm](../auth/LoginForm.md)** - Example usage in authentication

## Hooks Used

- **[useCSRF](../../hooks/useCSRF.md)** - CSRF token management
- **[rateLimiter](../../lib/security.md)** - Rate limiting utilities
- **[sanitizeObject](../../lib/security.md)** - Input sanitization