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

/**
 * Returns the correct wizard path for the current device.
 * Safe to call client-side only (reads navigator.userAgent).
 */
export function getWizardPath(): '/desktop/wizard' | '/mobile/wizard' {
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : null;
  return detectDevice(ua) === 'mobile' ? '/mobile/wizard' : '/desktop/wizard';
}

/**
 * Returns the correct dashboard path for the current device.
 * Safe to call client-side only (reads navigator.userAgent).
 */
export function getDashboardPath(): '/desktop/dashboard' | '/mobile/dashboard' {
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : null;
  return detectDevice(ua) === 'mobile' ? '/mobile/dashboard' : '/desktop/dashboard';
}
