import type { GetServerSideProps } from 'next';
import { detectDevice } from '@/lib/utils/device';

/**
 * Root page — redirects to /desktop or /mobile based on user-agent detection.
 * Uses getServerSideProps for server-side redirect (no flash of content).
 * This component should never actually render.
 */
export default function Root() {
  return null;
}

export const getServerSideProps: GetServerSideProps = async ({ req }) => {
  const ua = req.headers['user-agent'] || null;
  const device = detectDevice(ua);
  const destination = device === 'mobile' ? '/mobile' : '/desktop';
  return { redirect: { destination, permanent: false } };
};
