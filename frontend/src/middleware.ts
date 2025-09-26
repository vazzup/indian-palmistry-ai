import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware to handle authentication-based redirects
 *
 * This middleware runs on the server before pages are rendered,
 * redirecting users to the appropriate pages based on auth status.
 * In the single reading model, authenticated users go directly to their reading.
 */
export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname

  // Enhanced cookie detection with debug logging
  const sessionCookie = request.cookies.get('palmistry_session')
  const allCookies = request.cookies.getAll()
  const isAuthenticated = !!sessionCookie?.value

  console.log(`[Middleware] Path: ${pathname}`)
  console.log(`[Middleware] Session cookie exists: ${!!sessionCookie}`)
  console.log(`[Middleware] Session value: ${sessionCookie?.value ? '[REDACTED]' : 'none'}`)
  console.log(`[Middleware] All cookies: ${allCookies.map(c => c.name).join(', ')}`)
  console.log(`[Middleware] Is authenticated: ${isAuthenticated}`)

  // Homepage: redirect authenticated users to their reading
  if (pathname === '/') {
    if (isAuthenticated) {
      console.log('[Middleware] Authenticated user accessing homepage, redirecting to reading')
      return NextResponse.redirect(new URL('/reading', request.url))
    }
    console.log('[Middleware] Unauthenticated user, showing landing page')
    return NextResponse.next()
  }

  // Dashboard: redirect authenticated users to reading (single reading model)
  if (pathname === '/dashboard') {
    if (isAuthenticated) {
      console.log('[Middleware] Redirecting dashboard to reading page (single reading model)')
      return NextResponse.redirect(new URL('/reading', request.url))
    }
    console.log('[Middleware] Unauthenticated user on dashboard - should redirect to login')
    return NextResponse.next()
  }

  // Auth pages: redirect authenticated users away from login/register
  if ((pathname === '/login' || pathname === '/register') && isAuthenticated) {
    console.log(`[Middleware] Authenticated user accessing ${pathname}, redirecting to reading`)
    return NextResponse.redirect(new URL('/reading', request.url))
  }

  // For all other routes, continue as normal
  return NextResponse.next()
}

export const config = {
  // Run middleware on homepage, dashboard, and auth pages
  matcher: ['/', '/dashboard', '/login', '/register']
}