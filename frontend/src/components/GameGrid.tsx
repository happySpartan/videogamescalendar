import { useEffect, useRef, useState } from 'react';
import { Grid, Card, Text, Container, Title, LoadingOverlay, Flex, Box, Image, Center, Loader, Badge } from '@mantine/core';
import classes from '../styles/GameGrid.module.css';
import FilterBar from './FilterBar';
import { getPlatformColor, formatDate } from '../utils/game.utils';
import { getWeekBounds } from '../utils/calendar.utils';
import { useGameLibrary } from '../context/GameLibraryContext';
import useVideoHover from '../hooks/useVideoHover';

// Define error message component
const ErrorMessage = ({ message }: { message: string }) => (
  <Container>
    <Text color="red">{message}</Text>
  </Container>
);

// Define search results info component
const SearchResultsInfo = ({ query, count }: { query: string; count: number }) => (
  <Text mb="md" size="sm" c="dimmed">
    {count === 0
      ? `No games found matching "${query}"`
      : `Found ${count} game${count === 1 ? '' : 's'} matching "${query}"`}
  </Text>
);

// Define empty state component
const EmptyState = ({ gamesExist, viewTitle }: { gamesExist: boolean; viewTitle: string }) => (
  <Container>
    <Text ta="center">
      {gamesExist
        ? "No games match your filters."
        : `No games found for ${viewTitle}.`}
    </Text>
  </Container>
);

// Define loading indicator component
const LoadingIndicator = () => (
  <Center py="md">
    <Loader size="md" />
  </Center>
);

// Define end of list message component
const EndOfListMessage = () => (
  <Text ta="center" my="md" c="dimmed">No more games to load</Text>
);

// Helper function to get title from period
const getViewTitleFromPeriod = (period: { type: 'month' | 'week'; date: Date }) => {
  if (period.type === 'month') {
    const monthNames = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"];
    return `${monthNames[period.date.getMonth()]} ${period.date.getFullYear()}`;
  } else if (period.type === 'week') {
    const { start, end } = getWeekBounds(period.date);
    return `Week of ${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
  }
  return '';
};

interface GameGridProps {
  view: string;
  searchQuery?: string;
  period?: {
    type: 'month' | 'week';
    date: Date;
  };
  onGamesLoaded?: (games: any[]) => void;
}

export const GameGrid = ({ view, searchQuery = '', period }: GameGridProps) => {  const { 
    state: { 
      games,
      filteredGames,
      loading, 
      loadingMore,
      isPeriodChanging,
      error,
      hasMore,
      filterOptions
    },
    dispatch,
    loadMoreGames 
  } = useGameLibrary();

  // Video hover handlers using the existing useVideoHover hook
  const {
    handleMouseEnter,
    handleMouseLeave,
    isVideoPlaying
  } = useVideoHover(1000); // 1 second delay

  // Set up intersection observer for infinite scrolling
  const lastGameElementRef = useRef<HTMLDivElement | null>(null);
  
  useEffect(() => {    const observer = new IntersectionObserver(
      entries => {
        // Don't load more games during period transitions or when loading
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore && !isPeriodChanging) {
          loadMoreGames();
        }
      },
      { threshold: 0.5 }
    );
    
    if (lastGameElementRef.current) {
      observer.observe(lastGameElementRef.current);
    }
    
    return () => {
      if (lastGameElementRef.current) {
        if (observer) {
          observer.unobserve(lastGameElementRef.current);
        }
      }    };
  }, [hasMore, loading, loadingMore, loadMoreGames, isPeriodChanging]);

  // Filter handlers
  const handlePlatformFilter = (platformIds: number[]) => {
    dispatch({ 
      type: 'SET_FILTER', 
      payload: { type: 'platforms', ids: platformIds } 
    });
  };

  const handleGenreFilter = (genreIds: number[]) => {
    dispatch({ 
      type: 'SET_FILTER', 
      payload: { type: 'genres', ids: genreIds } 
    });
  };

  const handleLanguageFilter = (languageIds: number[]) => {
    dispatch({ 
      type: 'SET_FILTER', 
      payload: { type: 'languages', ids: languageIds } 
    });
  };

  // Get a title for the current view
  const getViewTitle = () => {
    if (period) {
      return getViewTitleFromPeriod(period);
    }
    return view;
  };

  // Error display
  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <Container size="xl">
      <Title order={2} mb="md">{getViewTitle()}</Title>
      
      <FilterBar 
        platforms={filterOptions.platforms || []}
        genres={filterOptions.genres || []}
        languages={filterOptions.languages || []}
        onPlatformFilterChange={handlePlatformFilter}
        onGenreFilterChange={handleGenreFilter}
        onLanguageFilterChange={handleLanguageFilter}
      />
        <div style={{ position: 'relative', marginTop: '1rem' }}>
        <LoadingOverlay visible={loading || isPeriodChanging} />
        
        {searchQuery && (
          <SearchResultsInfo 
            query={searchQuery} 
            count={filteredGames.length} 
          />
        )}
        
        <Grid gutter={{ base: 'xs', sm: 'md', lg: 'lg' }}>
          {filteredGames.length > 0 ? (
            filteredGames.map((game, index) => (
              <Grid.Col 
                key={game.id} 
                span={{ base: 6, sm: 4, md: 3, lg: 2.4 }}
                ref={index === filteredGames.length - 5 ? lastGameElementRef : undefined}
              >
                <Card 
                  shadow="sm" 
                  padding="md" 
                  radius="md" 
                  withBorder
                  className={classes.gameCard}
                  pt={0}
                  styles={{
                    root: {
                      overflow: 'hidden'
                    }
                  }}
                >
                  <div 
                    className={classes.coverWrapper}
                    onMouseEnter={() => handleMouseEnter(game.id)}
                    onMouseLeave={handleMouseLeave}
                  >
                    {game.franchise && (
                      <div className={classes.franchiseBadge}>
                        {game.franchise.name}
                      </div>
                    )}
                    <Image 
                      src={game.cover_url ? game.cover_url.replace('t_thumb', 't_cover_big') : null}
                      height={280}
                      alt={game.name}
                      fit="cover"
                      className={classes.coverImage}
                      fallbackSrc="https://placehold.co/200x280?text=No+Image"
                    />
                    {game.video_id && isVideoPlaying(game.id) && (
                      <div className={classes.videoOverlay}>
                        <iframe
                          src={`https://www.youtube.com/embed/${game.video_id}?autoplay=1&mute=1&controls=0&modestbranding=1`}
                          title={`${game.name} trailer`}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                          className={classes.videoIframe}
                        ></iframe>
                      </div>
                    )}
                  </div>

                  <Text fw={700} size="md" mt="sm" lineClamp={1} className={classes.title} ta="center">
                    {game.name}
                  </Text>
                  
                  <Text size="md" fw={600} c="blue.7" mb="xs" ta="center">
                    {formatDate(game.release_date)}
                  </Text>
                  
                  {game.developer && (
                    <Text size="xs" lineClamp={1} mb="xs" ta="center">
                      {game.developer.name}
                    </Text>
                  )}

                  {game.genre && (
                    <Center mb="xs">
                      <Badge 
                        color="blue" 
                        variant="filled" 
                        radius="xl"
                        size="md"
                      >
                        {game.genre.name}
                      </Badge>
                    </Center>
                  )}
                  
                  {game.platforms && game.platforms.length > 0 && (
                    <Flex gap="xs" wrap="wrap" mt="auto" justify="center">
                      {game.platforms.slice(0, 3).map((platform) => (
                        <div
                          key={platform.id} 
                          className={classes.platformBadge}
                          style={{ backgroundColor: getPlatformColor(platform.name) }}
                        >
                          {platform.name}
                        </div>
                      ))}
                      {game.platforms.length > 3 && (
                        <div className={classes.platformBadge} style={{ backgroundColor: 'gray' }}>
                          +{game.platforms.length - 3}
                        </div>
                      )}
                    </Flex>
                  )}
                </Card>
              </Grid.Col>
            ))
          ) : !loading ? (
            <EmptyState gamesExist={games.length > 0} viewTitle={getViewTitle()} />
          ) : null}
        </Grid>
        
        {(loadingMore && hasMore) && (
          <LoadingIndicator />
        )}
        
        {!hasMore && filteredGames.length > 0 && !loading && !loadingMore && (
          <EndOfListMessage />
        )}
      </div>
    </Container>
  );
};

export default GameGrid;