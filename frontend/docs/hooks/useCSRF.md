# useCSRF Hook

A React hook that provides CSRF token management functionality for secure form submissions in the Indian Palmistry AI application.

## Overview

The `useCSRF` hook handles the fetching, caching, and automatic refreshing of CSRF tokens, ensuring all form submissions are protected against Cross-Site Request Forgery attacks.

## Features

- **Automatic Token Fetching**: Retrieves CSRF tokens from the backend API
- **Meta Tag Management**: Updates DOM meta tags for axios interceptors
- **Token Refresh**: Automatic token refresh on authentication state changes
- **Error Handling**: Graceful error handling with retry mechanisms
- **Loading States**: Provides loading indicators during token operations
- **Authentication Integration**: Works seamlessly with the auth store

## Usage

### Basic Usage

```tsx
import { useCSRF } from '@/hooks/useCSRF';

function MyForm() {
  const { token, isLoading, error, refreshToken } = useCSRF();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading security token</div>;

  const handleSubmit = async (formData: FormData) => {
    // Token is automatically included in SecureForm
    // or manually add it for custom requests
    formData.append('csrf_token', token || '');
    
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="hidden" name="csrf_token" value={token || ''} />
      {/* Other form fields */}
    </form>
  );
}
```

### Manual Token Refresh

```tsx
import { useCSRF } from '@/hooks/useCSRF';

function SecuritySettings() {
  const { refreshToken, isLoading } = useCSRF();

  const handleRefreshSecurity = async () => {
    await refreshToken();
    // Token is now refreshed
  };

  return (
    <button 
      onClick={handleRefreshSecurity} 
      disabled={isLoading}
    >
      Refresh Security Token
    </button>
  );
}
```

### Integration with API Calls

```tsx
import { useCSRF } from '@/hooks/useCSRF';

function ApiExample() {
  const { token } = useCSRF();

  const makeApiCall = async (data: any) => {
    const response = await fetch('/api/protected', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token || '',
      },
      body: JSON.stringify({
        ...data,
        csrf_token: token,
      }),
    });
  };
}
```

## Return Values

| Property | Type | Description |
|----------|------|-------------|
| `token` | `string \| null` | Current CSRF token or null if not loaded |
| `isLoading` | `boolean` | Whether a token fetch operation is in progress |
| `error` | `string \| null` | Error message if token fetch failed |
| `refreshToken` | `() => Promise<void>` | Function to manually refresh the token |

## Token Lifecycle

### Initial Load

1. Hook mounts and checks for existing token in meta tags
2. If no token exists, fetches from `/api/auth/csrf-token`
3. Updates DOM meta tags for axios interceptors
4. Stores token in component state

### Authentication Changes

1. Listens to auth store changes via `useAuthStore`
2. Automatically refreshes token when user logs in/out
3. Clears token on logout for security

### Error Handling

1. Network errors are caught and stored in error state
2. Invalid tokens trigger automatic refresh attempts
3. Failed refreshes show user-friendly error messages

## Backend Integration

The hook integrates with FastAPI backend endpoints:

```python
# Backend endpoint structure
@router.get("/csrf-token")
async def get_csrf_token():
    return {"csrf_token": generate_csrf_token()}
```

## DOM Meta Tag Management

The hook automatically manages CSRF meta tags:

```html
<!-- Updated automatically by the hook -->
<meta name="csrf-token" content="abc123...">
```

This allows axios interceptors to automatically include tokens:

```typescript
// Axios interceptor can read from meta tag
axios.interceptors.request.use((config) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (token) {
    config.headers['X-CSRF-Token'] = token;
  }
  return config;
});
```

## Error States

### Network Errors

```tsx
const { error } = useCSRF();

if (error === 'Failed to fetch CSRF token') {
  return <div>Please check your internet connection</div>;
}
```

### Authentication Errors

```tsx
const { error } = useCSRF();

if (error === 'Authentication required') {
  return <div>Please log in to continue</div>;
}
```

## Performance Considerations

- **Token Caching**: Tokens are cached to avoid unnecessary API calls
- **Automatic Cleanup**: Effect cleanup prevents memory leaks
- **Debounced Refresh**: Multiple refresh calls are debounced
- **Minimal Re-renders**: State updates are optimized

## Security Features

### Token Validation

- Validates token format before storing
- Checks token expiration (if provided by backend)
- Automatically refreshes expired tokens

### Secure Storage

- Tokens are stored in component state (memory only)
- No localStorage or sessionStorage usage for security
- Automatic cleanup on component unmount

## Testing

The hook is thoroughly tested with:

```typescript
// Mock auth store
const mockAuthStore = {
  isAuthenticated: false,
  user: null,
};

// Mock fetch responses
global.fetch = jest.fn();

// Test token fetching
it('should fetch CSRF token on mount', async () => {
  const { result } = renderHook(() => useCSRF());
  expect(fetch).toHaveBeenCalledWith('/api/auth/csrf-token');
});
```

## Best Practices

1. **Always use with forms** that modify server state
2. **Don't store tokens** in localStorage or cookies
3. **Handle loading states** gracefully in your UI
4. **Refresh tokens** after authentication changes
5. **Check for errors** and provide user feedback

## Related Components

- **[SecureForm](../components/ui/SecureForm.md)** - Uses this hook automatically
- **[SecurityProvider](../components/providers/SecurityProvider.md)** - Global CSRF context
- **[Auth Store](../lib/auth.md)** - Authentication state management

## Dependencies

- **React**: Hook functionality
- **Zustand**: Auth store integration
- **TypeScript**: Type safety

## Browser Support

Compatible with all modern browsers that support:
- Fetch API
- React Hooks
- DOM meta tag manipulation