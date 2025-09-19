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

// Override global dynamic setting to enable prerendering for homepage only
export const dynamic = 'auto';

export default function HomePage() {
  return <GuestHomepage />;
}