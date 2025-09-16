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
    // Clear any existing timer
    if (hoverState.timer) {
      clearTimeout(hoverState.timer);
    }
    
    // Set a new timer for 1 second
    const timer = setTimeout(() => {
      setHoverState(prev => ({
        ...prev,
        isPlaying: true
      }));
    }, delayMs);
    
    // Update hover state
    setHoverState({
      gameId,
      timer,
      isPlaying: false
    });
  };
  
  // Clear hover state
  const handleMouseLeave = () => {
    // Clear the timer if exists
    if (hoverState.timer) {
      clearTimeout(hoverState.timer);
    }
    
    // Reset hover state
    setHoverState({
      gameId: null,
      timer: null,
      isPlaying: false
    });
  };

  // Check if video should play for a specific game
  const isVideoPlaying = (gameId: number) => {
    return hoverState.gameId === gameId && hoverState.isPlaying;
  };

  return {
    handleMouseEnter,
    handleMouseLeave,
    isVideoPlaying
  };
}

export default useVideoHover;
