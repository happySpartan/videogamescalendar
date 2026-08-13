import { useEffect, useRef, useState } from 'react';
import { Grid, Card, Text, Container, Title, LoadingOverlay, Flex, Box, Image, Center, Loader, Badge } from '@mantine/core';
import classes from '../styles/GameGrid.module.css';
import FilterBar from './FilterBar';
import { getPlatformColor, formatDate, getPlatformIcon, getPlatformShortName } from '../utils/game.utils';
import { getWeekBounds } from '../utils/calendar.utils';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';
import useVideoHover from '../hooks/useVideoHover';
import type { FilterOption } from '../types';

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
        ? 'No games match your filters.'
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
const getViewTitleFromPeriod = (period: { type: 'month' | 'week' | 'day'; date: Date }) => {
  if (period.type === 'month') {
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'];
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
  onGamesLoaded?: (games: any[]) => void;
}

export const GameGrid = ({ view, searchQuery = '' }: GameGridProps) => {
  const {
    games,
    filteredGames,
    loading,
    error,
    hasMore,
    filterOptions,
    periods: period,
    changePeriod,
    loadMore,
    setSearchQuery,
    setPlatformFilter,
    setGenreFilter,
  } = useReleaseCalendar();

  // Video hover handlers using the existing useVideoHover hook
  const {
    handleMouseEnter,
    handleMouseLeave,
    isVideoPlaying,
  } = useVideoHover(1000); // 1 second delay

  // Keep the view's local search text in sync with the shared hook when the
  // parent passes it down (e.g. from SearchBar via Layout in the old design).
  const [localSearch, setLocalSearch] = useState(searchQuery);
  useEffect(() => {
    setLocalSearch(searchQuery);
    setSearchQuery(searchQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Set up intersection observer for infinite scrolling
  const lastGameElementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        // Don't load more during loading
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.5 },
    );

    if (lastGameElementRef.current) {
      observer.observe(lastGameElementRef.current);
    }

    return () => {
      if (lastGameElementRef.current) {
        if (observer) {
          observer.unobserve(lastGameElementRef.current);
        }
      }
    };
  }, [hasMore, loading, loadMore]);

  // Filter handlers
  const handlePlatformFilter = (platformIds: number[]) => {
    setPlatformFilter(platformIds);
  };

  const handleGenreFilter = (genreIds: number[]) => {
    setGenreFilter(genreIds);
  };

  const handleLanguageFilter = (_languageIds: number[]) => {
    // Languages are not exposed by the /releases contract; keep a no-op.
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
      <Title order={2} mb="md" className={classes.viewTitle}>{getViewTitle()}</Title>

      <FilterBar
        platforms={filterOptions.platforms as FilterOption[] || []}
        genres={filterOptions.genres as FilterOption[] || []}
        languages={filterOptions.languages || []}
        onPlatformFilterChange={handlePlatformFilter}
        onGenreFilterChange={handleGenreFilter}
        onLanguageFilterChange={handleLanguageFilter}
      />
      <div style={{ position: 'relative', marginTop: '1rem' }}>
        <LoadingOverlay visible={loading} />

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
                      overflow: 'hidden',
                    },
                  }}
                >
                  <div className={classes.imageContainer}>
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

                      {/* Release Date Badge */}
                      {game.first_release_date && (
                        <div className={classes.releaseDateBadge}>
                          {formatDate(game.first_release_date)}
                        </div>
                      )}

                      <Image
                        src={game.cover_url ? game.cover_url.replace('t_thumb', 't_cover_big') : null}
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
                  </div>

                  <div className={classes.contentContainer}>
                    <Text className={classes.title}>
                      {game.name}
                    </Text>

                    {game.summary && (
                      <Text className={classes.summary}>
                        {game.summary}
                      </Text>
                    )}

                    {game.developer && (
                      <div className={classes.developersSection}>
                        <Text className={classes.developerName}>
                          by {game.developer.name}
                        </Text>
                      </div>
                    )}

                    {game.genre && (
                      <div className={classes.badgeContainer}>
                        <div className={classes.genreBadge}>
                          {game.genre.name}
                        </div>
                      </div>
                    )}

                    {game.platforms && game.platforms.length > 0 && (
                      <div className={classes.platformContainer}>
                        {game.platforms.slice(0, 4).map((platform) => (
                          <div
                            key={platform.id}
                            className={classes.platformBadge}
                            data-platform={platform.name.toLowerCase()}
                            style={{ backgroundColor: getPlatformColor(platform.name) }}
                            title={platform.name}
                          >
                            <span className={classes.platformIcon}>
                              {getPlatformIcon(platform.name)}
                            </span>
                            <span className={classes.platformText}>
                              {getPlatformShortName(platform.name)}
                            </span>
                          </div>
                        ))}
                        {game.platforms.length > 4 && (
                          <div
                            className={classes.platformBadge}
                            style={{ backgroundColor: 'rgba(255, 255, 255, 0.15)' }}
                            title={`+${game.platforms.length - 4} more platforms`}
                          >
                            <span className={classes.platformIcon}>⚡</span>
                            <span className={classes.platformText}>
                              +{game.platforms.length - 4}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              </Grid.Col>
            ))
          ) : !loading ? (
            <EmptyState gamesExist={games.length > 0} viewTitle={getViewTitle()} />
          ) : null}
        </Grid>

        {filteredGames.length === 0 && !loading && (
          <LoadingIndicator />
        )}

        {!hasMore && filteredGames.length > 0 && !loading && (
          <EndOfListMessage />
        )}
      </div>
    </Container>
  );
};

export default GameGrid;
