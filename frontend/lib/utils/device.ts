/**
 * Device detection utility (UTIL-01)
 *
 * UA-based device detection used by middleware (server-side) and
 * root index page (client-side via navigator.userAgent).
 *
 * Returns 'desktop' or 'mobile' based on the user agent string.
 */

export function detectDevice(userAgent: string | null | undefined): 'desktop' | 'mobile' {
  if (!userAgent) return 'desktop';
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i;
  return mobileRegex.test(userAgent) ? 'mobile' : 'desktop';
}
