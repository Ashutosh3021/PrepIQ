import React from 'react';

/**
 * TutorThinkingLoader — shown while the AI tutor is generating a response.
 * Uses the CSS-only bouncing dots animation from tutor_Loading(thinking).txt
 */
export const TutorThinkingLoader: React.FC = () => {
  return (
    <div className="flex items-start">
      <div className="p-4 md:p-6 bg-surface border-l-4 border-primary">
        {/* Label */}
        {/* <p className="text-[0.6rem] uppercase tracking-widest text-tertiary mb-3">
          PrepIQ Assistant is thinking…
        </p> */}
        {/* The loader from tutor_Loading(thinking).txt */}
        <div
          style={{
            '--s': '48px',
            width: 'var(--s)',
            aspectRatio: '2',
            background: `
              radial-gradient(farthest-side, var(--color-primary) 90%, transparent) 0 50% / 25% 50%,
              radial-gradient(farthest-side at bottom, var(--color-primary) 90%, transparent) 50% calc(50% - var(--s)/16) / 25% 25%,
              radial-gradient(farthest-side at top,    var(--color-primary) 90%, transparent) 50% calc(50% + var(--s)/16) / 25% 25%,
              radial-gradient(farthest-side at bottom, var(--color-primary) 90%, transparent) 100% calc(50% - var(--s)/16) / 25% 25%,
              radial-gradient(farthest-side at top,    var(--color-primary) 90%, transparent) 100% calc(50% + var(--s)/16) / 25% 25%
            `,
            backgroundRepeat: 'no-repeat',
            animation: 'tutorThinking 1s infinite',
          } as React.CSSProperties}
        />
        <style>{`
          @keyframes tutorThinking {
            25%  { background-position: 0 50%, 50% 0, 50% 100%, 100% 0, 100% 100%; }
            50%  { background-position: 100% 50%, 0 0, 0 100%, 50% 0, 50% 100%; }
            75%, 100% {
              background-position:
                100% 50%,
                0 calc(50% - var(--s)/16),
                0 calc(50% + var(--s)/16),
                50% calc(50% - var(--s)/16),
                50% calc(50% + var(--s)/16);
            }
          }
        `}</style>
      </div>
    </div>
  );
};

export default TutorThinkingLoader;
