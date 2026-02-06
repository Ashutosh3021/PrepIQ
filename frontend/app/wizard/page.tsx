'use client';

import React from 'react';
import WizardForm from '@/components/wizard/WizardForm';
import { useRouter } from 'next/navigation';

const WizardPage = () => {
  const router = useRouter();

  const handleWizardComplete = () => {
    // Redirect to dashboard after wizard completion
    router.push('/protected');
  };

  return (
    <div className="min-h-screen">
      <WizardForm onComplete={handleWizardComplete} />
    </div>
  );
};

export default WizardPage;