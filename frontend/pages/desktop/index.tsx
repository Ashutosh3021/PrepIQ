import { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    redirect: {
      destination: '/desktop/dashboard',
      permanent: false,
    },
  };
};

export default function DesktopIndex() {
  return null;
}
