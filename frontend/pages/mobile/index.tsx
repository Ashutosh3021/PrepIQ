import { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    redirect: {
      destination: '/mobile/dashboard',
      permanent: false,
    },
  };
};

export default function MobileIndex() {
  return null;
}
