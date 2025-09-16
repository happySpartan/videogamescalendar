import React, { useEffect, useMemo } from 'react';
import { Grid, Container, LoadingOverlay, Text, Center } from '@mantine/core';
import { useOptimisticGameData } from '../../hooks/useOptimisticGameData';
import { useGameFilters } from '../../hooks/useGameFilters';
import { useVideoHover } from '../../hooks/useVideoHover';
import { FilterBar } from '../FilterBar/FilterBar';
import { GameCard } from '../GameCard/GameCard';
import { Game } from '../../../../types';
import classes from './GameGrid.module.css';

interface GameGridProps {
  view: 'month' | 'week';
  searchQuery: string;
  period: { type: 'month' | 'week'; date: Date };
  onGamesLoaded?: (games: Game[]) => void;
}

export const GameGrid: React.FC<GameGridProps> = ({ 
  view, 
  searchQuery, 
  period, 
  onGamesLoaded 
}) => {  const { 
    games,
    loading,
    loadingMore,
    isPeriodChanging,
    error,
    hasMore,
    currentPeriod,
    changePeriod,
    loadNextPage
  } = useOptimisticGameData(period);

  const {
    filters,
    filterOptions,
    applyFilters,
    handlePlatformFilter,
    handleGenreFilter,
    handleLanguageFilter,
    clearFilters
  } = useGameFilters(games);

  const { handleMouseEnter, handleMouseLeave, isVideoPlaying } = useVideoHover();

  // Apply filters and search
  const filteredGames = useMemo(() => {
    return applyFilters(games, {
      searchQuery,
      platforms: filters.platforms,
      genres: filters.genres,
      languages: filters.languages
    });
  }, [games, searchQuery, filters, applyFilters]);

  // Notify parent about loaded games
  useEffect(() => {
    if (!loading && onGamesLoaded) {
      onGamesLoaded(games);
    }
  }, [games, loading, onGamesLoaded]);
  // Update period when parent prop changes
  useEffect(() => {
    // Only attempt to change periods if we're not already in a transition
    if ((period.type !== currentPeriod.type || 
        period.date.getTime() !== currentPeriod.date.getTime()) && 
        !isPeriodChanging && !loading) {
      changePeriod(period);
    }
  }, [period, currentPeriod, changePeriod, isPeriodChanging, loading]);

  return (
    <Container size="xl" className={classes.container}>
      <FilterBar
        games={games}
        filterOptions={filterOptions}
        onPlatformFilter={handlePlatformFilter}
        onGenreFilter={handleGenreFilter}
        onLanguageFilter={handleLanguageFilter}
        onClearFilters={clearFilters}
      />

      {error && (
        <Center>
          <Text color="red">{error}</Text>
        </Center>
      )}

      <LoadingOverlay visible={(loading && !loadingMore) || isPeriodChanging} />
      
      <Grid>
        {filteredGames.map((game: Game) => (
          <Grid.Col key={game.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
            <GameCard
              game={game}
              onMouseEnter={() => handleMouseEnter(game.id)}
              onMouseLeave={handleMouseLeave}
              isPlaying={isVideoPlaying(game.id)}
            />
          </Grid.Col>
        ))}
      </Grid>

      {hasMore && !loading && (
        <Center mt="xl">
          <button 
            onClick={loadNextPage}
            disabled={loadingMore}
            className={classes.loadMoreButton}
          >
            {loadingMore ? 'Loading...' : 'Load More'}
          </button>
        </Center>
      )}
    </Container>
  );
};
