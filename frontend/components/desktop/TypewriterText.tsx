import React, { useEffect, useRef, useState } from 'react';

interface TypewriterTextProps {
  text: string;
  /** Characters per second. Default 40 */
  speed?: number;
  /** Called when typing is complete */
  onDone?: () => void;
  className?: string;
}

/**
 * TypewriterText — reveals text character by character.
 * Used for AI tutor responses so they appear gradually rather than all at once.
 * Based on tutor_typing.txt concept, adapted as a React component.
 */
export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  speed = 40,
  onDone,
  className,
}) => {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track which text we're currently typing so prop changes restart cleanly
  const textRef = useRef(text);

  useEffect(() => {
    // New text — reset and start over
    textRef.current = text;
    indexRef.current = 0;
    setDisplayed('');
    setDone(false);

    const delay = Math.max(10, Math.round(1000 / speed));

    const type = () => {
      // Guard: if text changed while typing, stop this cycle
      if (textRef.current !== text) return;

      if (indexRef.current < text.length) {
        indexRef.current += 1;
        setDisplayed(text.slice(0, indexRef.current));
        timerRef.current = setTimeout(type, delay);
      } else {
        setDone(true);
        onDone?.();
      }
    };

    timerRef.current = setTimeout(type, delay);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, speed]);

  return (
    <span className={className}>
      {displayed}
      {/* Blinking cursor while typing */}
      {!done && (
        <span
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: '2px',
            height: '1em',
            background: 'currentColor',
            marginLeft: '1px',
            verticalAlign: 'text-bottom',
            animation: 'tutorCursorBlink 0.7s step-end infinite',
          }}
        />
      )}
      <style>{`
        @keyframes tutorCursorBlink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0; }
        }
      `}</style>
    </span>
  );
};

export default TypewriterText;
