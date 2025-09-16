import { useState, useEffect, useRef } from 'react';
import gameService from '../../../services/game.service';
import { Game } from '../../../types';

// Custom hook to fetch and manage game data
export function useGameData(period: { type: 'month' | 'week'; date: Date }) {
  const [games, setGames] = useState<Game[]>([]);
  const [filteredGames, setFilteredGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Create a string representation of the period for comparison
  const periodKey = `${period.type}-${period.date.getFullYear()}-${period.date.getMonth()}-${period.date.getDate()}`;
  const prevPeriodRef = useRef<string>('');
  const loadingRef = useRef<boolean>(false);

  // Data fetching - games data based on selected view and period
  useEffect(() => {
    // Prevent multiple simultaneous loading states
    if (loadingRef.current) {
      return;
    }

    // Only fetch if the period has changed
    if (periodKey === prevPeriodRef.current) {
      return;
    }
    
    const fetchGames = async () => {
      loadingRef.current = true;
      setLoading(true);
      setError(null);
      setPage(1);
      setHasMore(true);
      
      try {
        // Start loading new data
        const response = await gameService.getGamesByPeriod(period);
        
        if (response) {
          // Clear old data first, then set new data
          setGames([]);
          setFilteredGames([]);
          // Small delay to ensure UI clears before new data
          await new Promise(resolve => setTimeout(resolve, 50));
          setGames(response);
          setFilteredGames(response);
        } else {
          setGames([]);
          setFilteredGames([]);
          setError('Failed to fetch games');
        }
        
        // Update the previous period ref
        prevPeriodRef.current = periodKey;
      } catch (err) {
        console.error('Error fetching games:', err);
        setError('Failed to load games. Please try again later.');
        setGames([]);
        setFilteredGames([]);
      } finally {
        loadingRef.current = false;
        setLoading(false);
      }
    };

    fetchGames();
  }, [periodKey]);

  // Load more games function
  const loadMoreGames = async () => {
    if (page === 1 || loading || loadingMore || !hasMore || loadingRef.current) return;
    
    setLoadingMore(true);
    loadingRef.current = true;
    
    try {
      const nextPageGames = await gameService.getGamesByPeriod(period, page);
      
      if (!nextPageGames.length) {
        setHasMore(false);
      } else {
        setGames(prevGames => [...prevGames, ...nextPageGames]);
        setFilteredGames(prevGames => [...prevGames, ...nextPageGames]);
        setPage(prevPage => prevPage + 1);
      }
    } catch (err) {
      console.error('Error fetching more games:', err);
      setHasMore(false);
    } finally {
      loadingRef.current = false;
      setLoadingMore(false);
    }
  };

  // Function to request next page
  const loadNextPage = () => {
    if (!loading && !loadingMore && hasMore && !loadingRef.current) {
      loadMoreGames();
    }
  };

  return {
    games,
    filteredGames,
    setFilteredGames,
    loading,
    loadingMore,
    error,
    hasMore,
    loadNextPage,
    loadMoreGames,
    page
  };
}
