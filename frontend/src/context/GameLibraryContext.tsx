import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { Game, FilterOption } from '../types';
import gameService from '../services/game.service';

// Define the state structure
interface GameLibraryState {
  // Core data
  games: Game[];
  filteredGames: Game[];
  
  // UI state
  loading: boolean;
  loadingMore: boolean;
  isPeriodChanging: boolean; // Added to track period transitions
  error: string | null;
  
  // Pagination
  page: number;
  hasMore: boolean;
  
  // Filters
  filters: {
    platforms: number[];
    genres: number[];
    languages: number[];
  };
  
  // Search
  searchQuery: string;
  
  // Period
  period: {
    type: 'month' | 'week' | 'day';
    date: Date;
  };
  
  // Filter options (available filters)
  filterOptions: {
    platforms: FilterOption[];
    genres: FilterOption[];
    languages: FilterOption[];
  };
}

// Define action types
type GameLibraryAction =
  | { type: 'SET_GAMES'; payload: Game[] }
  | { type: 'SET_FILTERED_GAMES'; payload: Game[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_LOADING_MORE'; payload: boolean }
  | { type: 'SET_PERIOD_CHANGING'; payload: boolean } // Added action for period changing state
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_PAGE'; payload: number }
  | { type: 'INCREMENT_PAGE' }
  | { type: 'SET_HAS_MORE'; payload: boolean }
  | { type: 'SET_FILTER'; payload: { type: 'platforms' | 'genres' | 'languages'; ids: number[] } }
  | { type: 'RESET_FILTERS' }
  | { type: 'SET_SEARCH_QUERY'; payload: string }
  | { type: 'SET_PERIOD'; payload: { type: 'month' | 'week' | 'day'; date: Date } }
  | { type: 'SET_FILTER_OPTIONS'; payload: { type: 'platforms' | 'genres' | 'languages'; options: FilterOption[] } };

// Create the context
const GameLibraryContext = createContext<{
  state: GameLibraryState;
  dispatch: React.Dispatch<GameLibraryAction>;
  applyFilters: () => void;
  loadGames: () => Promise<void>;
  loadMoreGames: () => Promise<void>;
  changePeriod: (newPeriod: { type: 'month' | 'week' | 'day'; date: Date }) => void;
} | undefined>(undefined);

// Initial state
const initialState: GameLibraryState = {
  games: [],
  filteredGames: [],
  loading: true,
  loadingMore: false,
  isPeriodChanging: false,
  error: null,
  page: 1,
  hasMore: true,
  filters: {
    platforms: [],
    genres: [],
    languages: [],
  },
  searchQuery: '',
  period: {
    type: 'week',
    date: new Date(),
  },
  filterOptions: {
    platforms: [],
    genres: [],
    languages: [],
  },
};
function gameLibraryReducer(state: GameLibraryState, action: GameLibraryAction): GameLibraryState {
  switch (action.type) {
    case 'SET_GAMES':
      return { ...state, games: action.payload };
    
    case 'SET_FILTERED_GAMES':
      return { ...state, filteredGames: action.payload };
    
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
      case 'SET_LOADING_MORE':
      return { ...state, loadingMore: action.payload };
      
    case 'SET_PERIOD_CHANGING':
      return { ...state, isPeriodChanging: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    case 'SET_PAGE':
      return { ...state, page: action.payload };
    
    case 'INCREMENT_PAGE':
      return { ...state, page: state.page + 1 };
    
    case 'SET_HAS_MORE':
      return { ...state, hasMore: action.payload };
    
    case 'SET_FILTER':
      return {
        ...state,
        filters: {
          ...state.filters,
          [action.payload.type]: action.payload.ids,
        },
      };
    
    case 'RESET_FILTERS':
      return {
        ...state,
        filters: {
          platforms: [],
          genres: [],
          languages: [],
        },
      };
    
    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.payload };
    
    case 'SET_PERIOD':
      return { ...state, period: action.payload };
    
    case 'SET_FILTER_OPTIONS':
      return {
        ...state,
        filterOptions: {
          ...state.filterOptions,
          [action.payload.type]: action.payload.options,
        },
      };
    
    default:
      return state;
  }
}

// Provider component
export const GameLibraryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(gameLibraryReducer, initialState);
  
  // Load filter options on mount
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const options = await gameService.getFilterOptions();
        
        dispatch({ type: 'SET_FILTER_OPTIONS', payload: { type: 'platforms', options: options.platforms } });
        dispatch({ type: 'SET_FILTER_OPTIONS', payload: { type: 'genres', options: options.genres } });
        dispatch({ type: 'SET_FILTER_OPTIONS', payload: { type: 'languages', options: options.languages } });
      } catch (error) {
        console.error('Error loading filter options:', error);
      }
    };
    
    loadFilterOptions();
  }, []);
  
  // Apply filters function - separated from the effect to avoid stale closures
  const applyFilters = () => {
    const { games, filters, searchQuery } = state;
    
    if (games.length === 0) {
      dispatch({ type: 'SET_FILTERED_GAMES', payload: [] });
      return;
    }
    
    let result = [...games];
    
    // Apply search filter
    if (searchQuery && searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(
        game => game.name.toLowerCase().includes(query) || 
                (game.summary && game.summary.toLowerCase().includes(query))
      );
    }
    
    // Apply platform filter
    if (filters.platforms.length > 0) {
      result = result.filter(
        game => game.platforms?.some(platform => filters.platforms.includes(platform.id))
      );
    }
    
    // Apply genre filter
    if (filters.genres.length > 0) {
      result = result.filter(
        game => game.genre && filters.genres.includes(game.genre.id)
      );
    }
    
    // Apply language filter
    if (filters.languages.length > 0) {
      result = result.filter(
        game => game.language && filters.languages.includes(game.language.id)
      );
    }
    
    dispatch({ type: 'SET_FILTERED_GAMES', payload: result });
  };
  
  // Load games when filters or search query changes (but not during period changes)
  useEffect(() => {
    // Only reload if we have games loaded and not currently loading or changing periods
    // Also check if this is a fresh filter reset (all filters empty) to avoid triggering during period changes
    const hasActiveFilters = state.filters.platforms.length > 0 ||
                           state.filters.genres.length > 0 ||
                           state.filters.languages.length > 0 ||
                           state.searchQuery.trim() !== '';

    if (state.games.length > 0 && !state.loading && !state.isPeriodChanging && hasActiveFilters) {
      loadGames();
    }
  }, [state.filters, state.searchQuery]);

  // Apply client-side filters as backup (in case API filtering is incomplete)
  useEffect(() => {
    // For now, since API handles filtering, we just set filtered games same as games
    dispatch({ type: 'SET_FILTERED_GAMES', payload: state.games });
  }, [state.games]);
    // Load games function
  const loadGames = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_PERIOD_CHANGING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      dispatch({ type: 'SET_PAGE', payload: 1 });
      dispatch({ type: 'SET_HAS_MORE', payload: true });

      const { type, date } = state.period;
      const { filters, searchQuery } = state;

      // Prepare filters for API
      const apiFilters = {
        platforms: filters.platforms,
        genres: filters.genres,
        languages: filters.languages,
        search: searchQuery
      };

      const response = await gameService.getGamesByPeriod({ type, date }, 1, apiFilters);

      if (response) {
        dispatch({ type: 'SET_GAMES', payload: response });
        dispatch({ type: 'SET_FILTERED_GAMES', payload: response });
      } else {
        dispatch({ type: 'SET_GAMES', payload: [] });
        dispatch({ type: 'SET_FILTERED_GAMES', payload: [] });
        dispatch({ type: 'SET_ERROR', payload: 'No games found' });
      }
    } catch (error) {
      console.error('Error loading games:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load games' });
      dispatch({ type: 'SET_GAMES', payload: [] });
      dispatch({ type: 'SET_FILTERED_GAMES', payload: [] });
    } finally {
      // Add a small delay before resetting loading states to ensure UI updates
      setTimeout(() => {
        dispatch({ type: 'SET_LOADING', payload: false });
        dispatch({ type: 'SET_PERIOD_CHANGING', payload: false });
      }, 300);
    }
  };
    // Load more games function
  const loadMoreGames = async () => {
    // Don't try to load more if already loading, no more data, or during a period change
    if (state.loadingMore || !state.hasMore || state.isPeriodChanging || state.loading) return;
    
    try {
      dispatch({ type: 'SET_LOADING_MORE', payload: true });
      
      const { type, date } = state.period;
      const nextPage = state.page + 1;
      
      const response = await gameService.getGamesByPeriod({ type, date }, nextPage);
      
      if (response && response.length > 0) {
        dispatch({ type: 'SET_GAMES', payload: [...state.games, ...response] });
        dispatch({ type: 'INCREMENT_PAGE' });
      } else {
        dispatch({ type: 'SET_HAS_MORE', payload: false });
      }
    } catch (error) {
      console.error('Error loading more games:', error);
      dispatch({ type: 'SET_HAS_MORE', payload: false });    } finally {
      // Add a small delay for better UI experience
      setTimeout(() => {
        dispatch({ type: 'SET_LOADING_MORE', payload: false });
      }, 200);
    }
  };  // Period change handler
  const changePeriod = (newPeriod: { type: 'month' | 'week' | 'day'; date: Date }) => {
    // Only update if actually different to avoid unnecessary rerenders
    // Also check if we're already in a transition to prevent double updates
    if (
      (newPeriod.type !== state.period.type ||
      newPeriod.date.getTime() !== state.period.date.getTime()) &&
      !state.isPeriodChanging && !state.loading
    ) {
      dispatch({ type: 'SET_PERIOD_CHANGING', payload: true });
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_PERIOD', payload: newPeriod });
      
      // Reset state on period change
      dispatch({ type: 'RESET_FILTERS' });
      dispatch({ type: 'SET_SEARCH_QUERY', payload: '' });
      
      // Load games for new period
      // Small delay to let UI update before data fetching begins
      setTimeout(() => {
        loadGames();
      }, 50);
    }
  };
  
  // Initial load when period changes
  useEffect(() => {
    loadGames();
  }, []); // Only run once on mount, period changes are handled by changePeriod
  
  const value = {
    state,
    dispatch,
    applyFilters,
    loadGames,
    loadMoreGames,
    changePeriod,
  };
  
  return (
    <GameLibraryContext.Provider value={value}>
      {children}
    </GameLibraryContext.Provider>
  );
};

// Custom hook for using the context
export const useGameLibrary = () => {
  const context = useContext(GameLibraryContext);
  
  if (context === undefined) {
    throw new Error('useGameLibrary must be used within a GameLibraryProvider');
  }
  
  return context;
};
