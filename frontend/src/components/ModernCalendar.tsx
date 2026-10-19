import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Group, Tooltip, Stack, Text, Loader, Center, Alert, UnstyledButton, Modal, ScrollArea } from '@mantine/core';
import type { Release } from '../api/types';
import { getWeekStart, useReleaseCalendar } from '../hooks/useReleaseCalendar';
import PeriodToolbar from './PeriodToolbar';
import classes from '../styles/ModernCalendar.module.css';

const pad = (n: number) => String(n).padStart(2, '0');
const isoDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

// Monday-first, the EU convention (the product is EU-centric).
const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

/** Month grid (or one week row) of releases, driven by the shared period, filters and search. */
const ModernCalendar: React.FC = () => {
  const { periods: period, filteredReleases, loading, isError, error } = useReleaseCalendar();
  // The day whose full list is open ("+N more"): a cell shows only 4 games.
  const [openDay, setOpenDay] = useState<{ date: Date; games: Release[] } | null>(null);
  const year = period.date.getFullYear();
  const month = period.date.getMonth();

  // Weeks of day-cells: every week touching the month, or just the selected week.
  const calendarData = useMemo(() => {
    const byDay = new Map<string, Release[]>();
    for (const r of filteredReleases) {
      const day = r.release_date?.slice(0, 10);
      if (day) byDay.set(day, [...(byDay.get(day) ?? []), r]);
    }

    const first = period.type === 'week' ? getWeekStart(period.date) : getWeekStart(new Date(year, month, 1));
    const last = period.type === 'week' ? first : getWeekStart(new Date(year, month + 1, 0));
    const weeks: Array<Array<{ date: Date; isCurrentMonth: boolean; games: Release[] }>> = [];
    for (const start = new Date(first); start <= last; start.setDate(start.getDate() + 7)) {
      weeks.push(
        Array.from({ length: 7 }, (_, i) => {
          const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
          return {
            date,
            isCurrentMonth: period.type === 'week' || date.getMonth() === month,
            games: byDay.get(isoDay(date)) ?? [],
          };
        }),
      );
    }
    return weeks;
  }, [filteredReleases, period, year, month]);

  const todayKey = isoDay(new Date());

  return (
    <div className={classes.calendarContainer}>
      <PeriodToolbar />

      {isError && (
        <Alert color="red" title="Failed to load releases" mb="md">
          {error ?? 'Could not reach the API'}
        </Alert>
      )}

      <div className={classes.calendarGrid}>
        <div className={classes.weekDaysHeader}>
          {weekDays.map((day) => (
            <div key={day} className={classes.weekDay}>
              {day.slice(0, 3)}
            </div>
          ))}
        </div>

        {loading ? (
          <Center py="xl">
            <Loader />
          </Center>
        ) : (
          calendarData.map((week, weekIdx) => (
            <div key={weekIdx} className={classes.calendarWeek}>
              {week.map((day) => (
                <div
                  key={isoDay(day.date)}
                  className={classes.dayCell}
                  data-other-month={!day.isCurrentMonth || undefined}
                  data-today={isoDay(day.date) === todayKey || undefined}
                >
                  <span className={classes.dayNumber}>{day.date.getDate()}</span>
                  {day.games.length > 0 && (
                    <div className={classes.gamesGrid}>
                      {day.games.slice(0, 4).map((game) => (
                        <Tooltip
                          key={game.id}
                          label={
                            <Stack gap={2}>
                              <Text fw={600} size="sm">{game.name}</Text>
                              <Text size="xs" c="dimmed">
                                {game.platforms.map((p) => p.abbreviation || p.name).join(' · ')}
                              </Text>
                            </Stack>
                          }
                          withArrow
                          position="top"
                          openDelay={150}
                        >
                          <Link to={`/game/${game.id}`} className={classes.gameImageWrapper} aria-label={game.name}>
                            {game.cover_url ? (
                              <img
                                src={game.cover_url.replace('t_cover_big', 't_cover_small')}
                                alt=""
                                loading="lazy"
                                className={classes.gameImage}
                              />
                            ) : (
                              <span className={classes.noCover}>{game.name}</span>
                            )}
                          </Link>
                        </Tooltip>
                      ))}
                    </div>
                  )}
                  {/* Desktop shows 4 covers per day, phones 1: separate counts. */}
                  {day.games.length > 4 && (
                    <UnstyledButton
                      onClick={() => setOpenDay({ date: day.date, games: day.games })}
                      className={`${classes.moreGames} ${classes.moreDesktop}`}
                    >
                      +{day.games.length - 4} more
                    </UnstyledButton>
                  )}
                  {day.games.length > 1 && (
                    <UnstyledButton
                      onClick={() => setOpenDay({ date: day.date, games: day.games })}
                      className={`${classes.moreGames} ${classes.moreMobile}`}
                      aria-label={`All ${day.games.length} releases`}
                    >
                      +{day.games.length - 1}
                    </UnstyledButton>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      <Modal
        opened={openDay !== null}
        onClose={() => setOpenDay(null)}
        title={
          openDay &&
          `${openDay.date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })} · ${openDay.games.length} releases`
        }
        size="lg"
        scrollAreaComponent={ScrollArea.Autosize}
      >
        <Stack gap={4}>
          {openDay?.games.map((game) => (
            <UnstyledButton key={game.id} component={Link} to={`/game/${game.id}`} className={classes.dayListItem}>
              <Group gap="sm" wrap="nowrap">
                <span className={classes.listThumb}>
                  {game.cover_url && <img src={game.cover_url.replace('t_cover_big', 't_cover_small')} alt="" />}
                </span>
                <div style={{ minWidth: 0 }}>
                  <Text fw={600} size="sm" truncate>{game.name}</Text>
                  <Text size="xs" c="dimmed" truncate>
                    {game.platforms.map((p) => p.abbreviation || p.name).join(' · ')}
                  </Text>
                </div>
              </Group>
            </UnstyledButton>
          ))}
        </Stack>
      </Modal>
    </div>
  );
};

export default ModernCalendar;
