import Head from 'next/head';
import WizardForm from '@/components/common/WizardForm';

export default function MobileWizard() {
  return (
    <>
      <Head>
        <title>Setup | PrepIQ</title>
        <meta name="description" content="Complete your PrepIQ onboarding" />
      </Head>
      <WizardForm />
    </>
  );
}
