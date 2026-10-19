import { Link } from 'react-router-dom';
import { Alert, LoadingOverlay, Text } from '@mantine/core';
import classes from '../styles/GameGrid.module.css';
import PeriodToolbar from './PeriodToolbar';
import PlatformChips from './PlatformChips';
import { formatDate } from '../utils/game.utils';
import { formatPeriodTitle } from '../utils/calendar.utils';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';

/** Cover grid of the current period's releases (shared period, filters and search). */
export const GameGrid = () => {
  const { games, filteredGames, loading, error, periods: period, searchQuery } = useReleaseCalendar();

  return (
    <div>
      <PeriodToolbar />

      {error && (
        <Alert color="red" title="Failed to load releases" mb="md">
          {error}
        </Alert>
      )}

      {searchQuery && (
        <Text mb="md" size="sm" c="dimmed">
          {filteredGames.length === 0
            ? `No games found matching "${searchQuery}"`
            : `${filteredGames.length} game${filteredGames.length === 1 ? '' : 's'} matching "${searchQuery}"`}
        </Text>
      )}

      <div className={classes.gridWrapper}>
        <LoadingOverlay visible={loading} overlayProps={{ backgroundOpacity: 0.3 }} />
        {filteredGames.length > 0 ? (
          <div className={classes.grid}>
            {filteredGames.map((game) => (
              <Link key={game.id} to={`/game/${game.id}`} className={classes.card}>
                <div className={classes.cover}>
                  {game.cover_url ? (
                    <img src={game.cover_url} alt="" loading="lazy" />
                  ) : (
                    <span className={classes.noCover}>{game.name}</span>
                  )}
                  <span className={classes.date}>{formatDate(game.release_date)}</span>
                </div>
                <div className={classes.body}>
                  <Text className={classes.title} lineClamp={2}>
                    {game.name}
                  </Text>
                  {game.platforms && game.platforms.length > 0 && <PlatformChips platforms={game.platforms} max={3} />}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          !loading && (
            <Text ta="center" c="dimmed" py="xl">
              {games.length > 0 ? 'No games match your filters.' : `No releases in ${formatPeriodTitle(period)}.`}
            </Text>
          )
        )}
      </div>
    </div>
  );
};

export default GameGrid;
