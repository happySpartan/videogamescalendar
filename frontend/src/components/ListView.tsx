import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Button, Collapse, Group, LoadingOverlay, Text, UnstyledButton } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { formatDate } from '../utils/game.utils';
import { formatDateRange, formatPeriodTitle, getWeekBounds } from '../utils/calendar.utils';
import PeriodToolbar from './PeriodToolbar';
import PlatformChips from './PlatformChips';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';
import type { Game } from '../types';
import classes from '../styles/ListView.module.css';

interface DateGroup {
  key: string;
  date: Date;
  games: Game[];
}

/** Local Date for a release's (UTC) day, so groups match the calendar's days. */
const releaseDay = (iso: string) => {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
};

/** Group by day or by (Monday-first) week, keeping the shared order inside groups. */
const groupGames = (games: Game[], groupBy: 'day' | 'week'): DateGroup[] => {
  const groups = new Map<string, DateGroup>();
  for (const game of games) {
    if (!game.release_date) continue;
    const day = releaseDay(game.release_date);
    const date = groupBy === 'day' ? day : getWeekBounds(day).start;
    const key = date.toDateString();
    if (!groups.has(key)) groups.set(key, { key, date, games: [] });
    groups.get(key)!.games.push(game);
  }
  return [...groups.values()].sort((a, b) => a.date.getTime() - b.date.getTime());
};

const groupLabel = (date: Date, groupBy: 'day' | 'week') => {
  if (groupBy === 'day') {
    return date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' });
  }
  const { start, end } = getWeekBounds(date);
  return `Week of ${formatDateRange(start, end)}`;
};

/** Releases of the current period grouped by day (week view) or week (month view). */
const ListView = () => {
  const { games, filteredGames, loading, error, periods: period, searchQuery } = useReleaseCalendar();
  const groupBy: 'day' | 'week' = period.type === 'week' ? 'day' : 'week';
  const groups = useMemo(() => groupGames(filteredGames, groupBy), [filteredGames, groupBy]);
  const groupKeys = groups.map((g) => g.key).join(',');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  // Open the first group whenever the set of groups changes (not on every
  // render, which would undo the user's own clicks).
  useEffect(() => {
    const first = groupKeys.split(',')[0];
    setExpanded(first ? new Set([first]) : new Set());
  }, [groupKeys]);

  const toggle = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  return (
    <div>
      <PeriodToolbar />

      {error && (
        <Text c="red" mb="md">
          {error}
        </Text>
      )}

      <Group justify="space-between" mb="sm" mih={30}>
        <Text size="sm" c="dimmed">
          {searchQuery
            ? `${filteredGames.length} game${filteredGames.length === 1 ? '' : 's'} matching "${searchQuery}"`
            : `${filteredGames.length} release${filteredGames.length === 1 ? '' : 's'}`}
        </Text>
        {groups.length > 1 && (
          <Group gap="xs">
            <Button variant="subtle" size="xs" onClick={() => setExpanded(new Set(groups.map((g) => g.key)))}>
              Expand all
            </Button>
            <Button variant="subtle" size="xs" onClick={() => setExpanded(new Set())}>
              Collapse all
            </Button>
          </Group>
        )}
      </Group>

      <div className={classes.groupList}>
        <LoadingOverlay visible={loading} overlayProps={{ backgroundOpacity: 0.3 }} />
        {groups.map((group) => {
          const open = expanded.has(group.key);
          return (
            <section key={group.key} className={classes.groupContainer}>
              <UnstyledButton onClick={() => toggle(group.key)} className={classes.groupHeader} aria-expanded={open}>
                {open ? <IconChevronDown size={16} /> : <IconChevronRight size={16} />}
                <span className={classes.groupTitle}>{groupLabel(group.date, groupBy)}</span>
                <span className={classes.groupCount}>{group.games.length}</span>
              </UnstyledButton>
              <Collapse in={open}>
                <div className={classes.gamesList}>
                  {group.games.map((game) => (
                    <Link key={game.id} to={`/game/${game.id}`} className={classes.gameRow}>
                      <span className={classes.thumb}>
                        {game.cover_url && (
                          <img src={game.cover_url.replace('t_cover_big', 't_cover_small')} alt="" loading="lazy" />
                        )}
                      </span>
                      <span className={classes.info}>
                        <Text fw={600} size="sm" truncate>
                          {game.name}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {formatDate(game.release_date)}
                          {game.genres && game.genres.length > 0 && ` · ${game.genres.map((g) => g.name).slice(0, 2).join(', ')}`}
                        </Text>
                      </span>
                      {game.platforms && game.platforms.length > 0 && (
                        <span className={classes.platforms}>
                          <PlatformChips platforms={game.platforms} max={4} />
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              </Collapse>
            </section>
          );
        })}
        {groups.length === 0 && !loading && (
          <Text ta="center" c="dimmed" py="xl">
            {games.length > 0 ? 'No games match your filters.' : `No releases in ${formatPeriodTitle(period)}.`}
          </Text>
        )}
      </div>
    </div>
  );
};

export default ListView;
