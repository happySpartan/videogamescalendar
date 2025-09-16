import { useState, useEffect } from 'react';

interface HoverState {
  gameId: number | null;
  timer: NodeJS.Timeout | null;
  isPlaying: boolean;
}

export function useVideoHover(delayMs: number = 1000) {
  const [hoverState, setHoverState] = useState<HoverState>({
    gameId: null,
    timer: null,
    isPlaying: false
  });

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (hoverState.timer) {
        clearTimeout(hoverState.timer);
      }
    };
  }, [hoverState.timer]);

  // Start hover timer
  const handleMouseEnter = (gameId: number) => {
    if (hoverState.timer) {
      clearTimeout(hoverState.timer);
    }
    
    const timer = setTimeout(() => {
      setHoverState(prev => ({
        ...prev,
        isPlaying: true
      }));
    }, delayMs);
    
    setHoverState({
      gameId,
      timer,
      isPlaying: false
    });
  };

  // Clear hover state
  const handleMouseLeave = () => {
    if (hoverState.timer) {
      clearTimeout(hoverState.timer);
    }
    
    setHoverState({
      gameId: null,
      timer: null,
      isPlaying: false
    });
  };

  // Check if video should be playing for a specific game
  const isVideoPlaying = (gameId: number): boolean => {
    return hoverState.gameId === gameId && hoverState.isPlaying;
  };

  return {
    handleMouseEnter,
    handleMouseLeave,
    isVideoPlaying
  };
}
