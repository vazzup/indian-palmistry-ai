import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware to handle authentication-based redirects
 *
 * This middleware runs on the server before pages are rendered,
 * allowing us to redirect authenticated users away from the homepage
 * without client-side authentication checks.
 */
export function middleware(request: NextRequest) {
  // Only apply to the homepage
  if (request.nextUrl.pathname === '/') {
    // Check for the session cookie (set by backend)
    const sessionCookie = request.cookies.get('session_id')

    if (sessionCookie) {
      // User has a session cookie, redirect to dashboard
      console.log('Middleware: Authenticated user accessing homepage, redirecting to dashboard')
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }

    // No session cookie, let them see the landing page
    console.log('Middleware: Unauthenticated user, showing landing page')
  }

  // For all other routes, continue as normal
  return NextResponse.next()
}

export const config = {
  // Only run middleware on the homepage
  matcher: ['/']
}