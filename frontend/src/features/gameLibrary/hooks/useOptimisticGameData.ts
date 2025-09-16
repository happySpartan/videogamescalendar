import { useState, useRef, useCallback, useEffect } from 'react';
import { Game } from '../../../types';
import gameService from '../../../services/game.service';
import useDebounce from '../../../hooks/useDebounce';

interface GameCache {
  [key: string]: {
    data: Game[];
    timestamp: number;
    expiration: number;
  }
}

interface PendingPeriod {
  type: 'month' | 'week';
  date: Date;
}

export function useOptimisticGameData(initialPeriod: { type: 'month' | 'week'; date: Date }) {
  const [currentPeriod, setCurrentPeriod] = useState(initialPeriod);
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [isPeriodChanging, setIsPeriodChanging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const loadingRef = useRef(false);
  
  // Track when the last period change was made to prevent rapid changes
  const lastPeriodChangeRef = useRef<number>(0);
  
  // Client-side cache with 5-minute expiration
  const cache = useRef<GameCache>({});
  const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  const getCacheKey = useCallback((period: { type: 'month' | 'week'; date: Date }) => {
    return `${period.type}-${period.date.getFullYear()}-${period.date.getMonth()}-${period.date.getDate()}`;
  }, []);

  const getFromCache = useCallback((period: { type: 'month' | 'week'; date: Date }) => {
    const key = getCacheKey(period);
    const cached = cache.current[key];
    if (!cached) return null;
    
    if (Date.now() - cached.timestamp > cached.expiration) {
      delete cache.current[key];
      return null;
    }
    
    return cached.data;
  }, [getCacheKey]);

  const setInCache = useCallback((period: { type: 'month' | 'week'; date: Date }, data: Game[]) => {
    const key = getCacheKey(period);
    cache.current[key] = {
      data,
      timestamp: Date.now(),
      expiration: CACHE_DURATION
    };
  }, [getCacheKey]);

  const prefetchAdjacentPeriods = useCallback(async (period: { type: 'month' | 'week'; date: Date }) => {
    const next = new Date(period.date);
    const prev = new Date(period.date);
    
    if (period.type === 'month') {
      next.setMonth(next.getMonth() + 1);
      prev.setMonth(prev.getMonth() - 1);
    } else {
      next.setDate(next.getDate() + 7);
      prev.setDate(prev.getDate() - 7);
    }

    const nextPeriod = { type: period.type, date: next };
    const prevPeriod = { type: period.type, date: prev };

    // Only prefetch if not in cache
    if (!getFromCache(nextPeriod)) {
      try {
        const data = await gameService.getGamesByPeriod(nextPeriod);
        setInCache(nextPeriod, data);
      } catch (err) {
        console.warn('Failed to prefetch next period:', err);
      }
    }

    if (!getFromCache(prevPeriod)) {
      try {
        const data = await gameService.getGamesByPeriod(prevPeriod);
        setInCache(prevPeriod, data);
      } catch (err) {
        console.warn('Failed to prefetch previous period:', err);
      }
    }
  }, [getFromCache, setInCache]);
  const fetchGamesForPeriod = useCallback(async (period: { type: 'month' | 'week'; date: Date }, pageNum = 1) => {
    // Don't start a new fetch if one is already in progress
    if (loadingRef.current) return;
    loadingRef.current = true;
    
    // Always ensure isPeriodChanging is set for first page loads to prevent UI interactions
    if (pageNum === 1) {
      setIsPeriodChanging(true);
    }

    try {
      // For initial page load (not pagination)
      if (pageNum === 1) {
        const cached = getFromCache(period);
        if (cached) {
          // Set cached data immediately
          setGames(cached);
          setError(null);
          
          try {
            // Still fetch in background to ensure fresh data
            const data = await gameService.getGamesByPeriod(period);
            setGames(data);
            setInCache(period, data);
            
            // Prefetch adjacent periods for smoother navigation
            prefetchAdjacentPeriods(period);
          } catch (err) {
            // Silent error for background refresh - keep showing cached data
            console.warn('Background refresh failed, using cached data:', err);
          } finally {
            // Always ensure loading states are reset after a short delay to allow UI to update
            setTimeout(() => {
              setLoading(false);
              setIsPeriodChanging(false);
              loadingRef.current = false;
            }, 300); // Slightly longer delay for better UI feedback
          }
          return;
        }
      }

      // If we reach here, either it's pagination or there was no cache hit
      const data = await gameService.getGamesByPeriod(period, pageNum);
      
      if (pageNum === 1) {
        // First page load - replace all data
        setGames(data);
        setInCache(period, data);
        prefetchAdjacentPeriods(period);
      } else {
        // Pagination - append to existing data
        setGames(prev => [...prev, ...data]);
      }
      
      setHasMore(data.length > 0);
      setPage(pageNum);
      setError(null);
    } catch (err) {
      console.error('Error loading games:', err);
      setError('Failed to load games. Please try again.');      // Don't clear games on error to maintain optimistic UI
    } finally {
      // Reset all loading states with a slight delay for better UI feedback
      // This ensures the UI has time to display loading indicators
      setTimeout(() => {
        loadingRef.current = false;
        setLoading(false);
        setLoadingMore(false);
        setIsPeriodChanging(false);
      }, 300);
    }
  }, [getFromCache, setInCache, prefetchAdjacentPeriods]);
  const changePeriod = useCallback((newPeriod: { type: 'month' | 'week'; date: Date }) => {
    // Get current timestamp
    const now = Date.now();
    
    // If a period change was made less than 500ms ago, ignore this request
    // This prevents multiple rapid changes that might occur from double-clicks
    // Increased from 300ms to 500ms to provide more protection
    if (now - lastPeriodChangeRef.current < 500) {
      return;
    }
    
    // If we're already in a period change or loading state, don't allow another change
    if (isPeriodChanging || loadingRef.current) {
      return;
    }
    
    // Update the last period change timestamp
    lastPeriodChangeRef.current = now;
    
    // Signal that period is changing to block UI interactions
    setIsPeriodChanging(true);
    setLoading(true); // Always set loading to true for consistent UI feedback
    
    // Always update the current period immediately for UI responsiveness
    setCurrentPeriod(newPeriod);
    setPage(1);
    setHasMore(true);
    
    // Check cache immediately for optimistic update
    const cached = getFromCache(newPeriod);
    if (cached) {
      setGames(cached);
      
      // Even with cache hit, we maintain a short loading period for visual consistency
      // This helps with the perception of state change
      setTimeout(() => {
        // Only fetch in background if we have cached data
        fetchGamesForPeriod(newPeriod);
      }, 50);
    } else {
      // No cache, do a normal fetch
      fetchGamesForPeriod(newPeriod);
    }
  }, [getFromCache, fetchGamesForPeriod, isPeriodChanging]);

  const loadNextPage = useCallback(() => {
    if (!loadingRef.current && !loadingMore && hasMore) {
      setLoadingMore(true);
      fetchGamesForPeriod(currentPeriod, page + 1);
    }
  }, [currentPeriod, page, hasMore, loadingMore, fetchGamesForPeriod]);

  // Initial load
  useEffect(() => {
    changePeriod(initialPeriod);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return {
    games,
    loading,
    loadingMore,
    isPeriodChanging,  // Export this new state to disable UI during transitions
    error,
    hasMore,
    currentPeriod,
    changePeriod,
    loadNextPage,
  };
}
