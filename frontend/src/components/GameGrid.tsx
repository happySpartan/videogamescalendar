import { Link } from 'react-router-dom';
import { Grid, Card, Text, Container, Title, LoadingOverlay, Image } from '@mantine/core';
import classes from '../styles/GameGrid.module.css';
import FilterBar from './FilterBar';
import { getPlatformColor, formatDate, getPlatformIcon, getPlatformShortName } from '../utils/game.utils';
import { formatPeriodTitle } from '../utils/calendar.utils';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';
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
        ? 'No games match your filters.'
        : `No games found for ${viewTitle}.`}
    </Text>
  </Container>
);

/** Card grid of the current period's releases (shared period, filters and search). */
export const GameGrid = () => {
  const { games, filteredGames, loading, error, periods: period, searchQuery } = useReleaseCalendar();

  // Video hover handlers using the existing useVideoHover hook
  const {
    handleMouseEnter,
    handleMouseLeave,
    isVideoPlaying,
  } = useVideoHover(1000); // 1 second delay

  const viewTitle = formatPeriodTitle(period);

  // Error display
  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <Container size="xl">
      <Title order={2} mb="md" className={classes.viewTitle}>{viewTitle}</Title>

      <FilterBar />
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
            filteredGames.map((game) => (
              <Grid.Col key={game.id} span={{ base: 6, sm: 4, md: 3, lg: 2.4 }}>
                <Card
                  component={Link}
                  to={`/game/${game.id}`}
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
            <EmptyState gamesExist={games.length > 0} viewTitle={viewTitle} />
          ) : null}
        </Grid>

      </div>
    </Container>
  );
};

export default GameGrid;
