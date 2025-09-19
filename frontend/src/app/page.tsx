/**
 * @fileoverview Landing page for PalmistTalk - Marketing focused for unauthenticated users
 *
 * Authenticated users are automatically redirected to /dashboard via middleware
 * This page can now be prerendered since it has no server-side auth dependencies
 *
 * The actual homepage logic is in GuestHomepage component to maintain client-side functionality
 * while enabling the page itself to be statically rendered.
 */

import { GuestHomepage } from '@/components/homepage/GuestHomepage';

// Keep homepage dynamic like all other pages
export const dynamic = 'force-dynamic';

export default function HomePage() {
  return <GuestHomepage />;
}