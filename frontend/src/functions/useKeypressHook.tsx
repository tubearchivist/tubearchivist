import { useEffect, useEffectEvent, useRef, useState } from 'react';

// source: https://thibault.sh/react-hooks/use-key-press
export function useKeyPress(targetKey: string, onKeyDown?: () => void, onKeyUp?: () => void) {
  const [isKeyPressed, setIsKeyPressed] = useState(false);
  const isKeyPressedRef = useRef(false);
  const handleKeyDownEvent = useEffectEvent(() => {
    onKeyDown?.();
  });
  const handleKeyUpEvent = useEffectEvent(() => {
    onKeyUp?.();
  });

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === targetKey &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey &&
        !event.altKey
      ) {
        if (isKeyPressedRef.current) {
          return;
        }

        isKeyPressedRef.current = true;
        setIsKeyPressed(true);
        handleKeyDownEvent();
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === targetKey) {
        isKeyPressedRef.current = false;
        setIsKeyPressed(false);
        handleKeyUpEvent();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [targetKey]);

  return isKeyPressed;
}
