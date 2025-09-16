import { useState, useCallback, useEffect } from 'react';
import { Game, FilterOption } from '../../../types';
import gameService from '../../../services/game.service';

interface GameFilters {
  platforms: string[];
  genres: string[];
  languages: string[];
}

interface FilterParams {
  searchQuery: string;
  platforms: string[];
  genres: string[];
  languages: string[];
}

interface FilterOptionsState {
  platforms: { value: string; label: string }[];
  genres: { value: string; label: string }[];
  languages: { value: string; label: string }[];
}

export function useGameFilters(games: Game[] = []) {
  const [filters, setFilters] = useState<GameFilters>({
    platforms: [],
    genres: [],
    languages: []
  });

  const [filterOptions, setFilterOptions] = useState<FilterOptionsState>({
    platforms: [],
    genres: [],
    languages: []
  });

  // Load filter options
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const options = await gameService.getFilterOptions();
        setFilterOptions({
          platforms: options.platforms.map(p => ({
            value: p.id.toString(),
            label: p.name
          })),
          genres: options.genres.map(g => ({
            value: g.id.toString(),
            label: g.name
          })),
          languages: options.languages.map(l => ({
            value: l.id.toString(),
            label: l.name
          }))
        });
      } catch (err) {
        console.error('Error loading filter options:', err);
      }
    };

    loadOptions();
  }, []);

  const applyFilters = useCallback((allGames: Game[], params: FilterParams): Game[] => {
    return allGames.filter(game => {
      // Search filter
      if (params.searchQuery) {
        const searchLower = params.searchQuery.toLowerCase();
        const matchesSearch = game.name.toLowerCase().includes(searchLower) ||
                            game.summary?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Platform filter
      if (params.platforms.length > 0 && game.platforms) {
        const hasPlatform = game.platforms.some(p => 
          params.platforms.includes(p.id.toString())
        );
        if (!hasPlatform) return false;
      }

      // Genre filter
      if (params.genres.length > 0 && game.genre) {
        if (!params.genres.includes(game.genre.id.toString())) {
          return false;
        }
      }

      // Language filter
      if (params.languages.length > 0 && game.language) {
        if (!params.languages.includes(game.language.id.toString())) {
          return false;
        }
      }

      return true;
    });
  }, []);

  const handlePlatformFilter = useCallback((platformIds: string[]) => {
    setFilters(prev => ({ ...prev, platforms: platformIds }));
  }, []);

  const handleGenreFilter = useCallback((genreIds: string[]) => {
    setFilters(prev => ({ ...prev, genres: genreIds }));
  }, []);

  const handleLanguageFilter = useCallback((languageIds: string[]) => {
    setFilters(prev => ({ ...prev, languages: languageIds }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      platforms: [],
      genres: [],
      languages: []
    });
  }, []);

  return {
    filters,
    filterOptions,
    applyFilters,
    handlePlatformFilter,
    handleGenreFilter,
    handleLanguageFilter,
    clearFilters
  };
}
