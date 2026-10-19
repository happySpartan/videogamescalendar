import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Container, Paper, Title, Group, Badge, Image, Tooltip, Box, Stack, Grid, Text, Loader, Center, Alert, UnstyledButton, Modal, ScrollArea } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import type { Release } from '../api/types';
import { getWeekStart, useReleaseCalendar } from '../hooks/useReleaseCalendar';
import { formatPeriodTitle } from '../utils/calendar.utils';
import classes from '../styles/ModernCalendar.module.css';

const pad = (n: number) => String(n).padStart(2, '0');
const isoDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

// Monday-first, the EU convention (the product is EU-centric).
const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

/** Month grid (or one week row) of releases, driven by the shared period, filters and search. */
const ModernCalendar: React.FC = () => {
  const { periods: period, filteredReleases, loading, isError, error, shiftPeriod } = useReleaseCalendar();
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

  return (
    <Container size="100%" className={classes.calendarContainer}>
      <Paper className={classes.header} p="lg" mb="md">
        <Group justify="space-between" align="center">
          <UnstyledButton className={classes.navButton} onClick={() => shiftPeriod(-1)} aria-label={`Previous ${period.type}`}>
            <IconChevronLeft size={24} />
          </UnstyledButton>
          <Title order={2} className={classes.monthTitle}>
            {formatPeriodTitle(period)}
          </Title>
          <UnstyledButton className={classes.navButton} onClick={() => shiftPeriod(1)} aria-label={`Next ${period.type}`}>
            <IconChevronRight size={24} />
          </UnstyledButton>
        </Group>
      </Paper>

      {isError && (
        <Alert color="red" title="Failed to load releases" mb="md">
          {error ?? 'Could not reach the API'}
        </Alert>
      )}

      <Paper className={classes.calendarGrid}>
        <Grid className={classes.weekDaysHeader} gutter={4}>
          {weekDays.map((day) => (
            <Grid.Col key={day} span={{ base: 12 / 7 }}>
              <Text className={classes.weekDay} ta="center" fw={600} size="sm">{day.slice(0, 3)}</Text>
            </Grid.Col>
          ))}
        </Grid>

        {loading ? (
          <Center py="xl"><Loader /></Center>
        ) : (
          calendarData.map((week, weekIdx) => (
            <Grid key={weekIdx} className={classes.calendarWeek} gutter={4}>
              {week.map((day, dayIdx) => (
                <Grid.Col key={dayIdx} span={{ base: 12 / 7 }}>
                  <Paper
                    className={`${classes.dayCell} ${!day.isCurrentMonth ? classes.otherMonth : ''} ${day.games.length > 0 ? classes.hasGames : ''}`}
                  >
                    <Text className={classes.dayNumber} fw={600}>{day.date.getDate()}</Text>
                    {day.games.length > 0 && (
                      <Box className={classes.gamesContainer}>
                        <Box className={classes.gamesGrid}>
                          {day.games.slice(0, 4).map((game) => (
                            <Tooltip
                              key={game.id}
                              label={
                                <Stack gap={4}>
                                  <Text fw={600} size="sm">{game.name}</Text>
                                  {game.genres.slice(0, 3).map((g) => (
                                    <Badge key={g.id} size="xs" variant="light">{g.name}</Badge>
                                  ))}
                                </Stack>
                              }
                              withArrow
                              position="top"
                            >
                              <Box component={Link} to={`/game/${game.id}`} className={classes.gameImageWrapper} aria-label={game.name}>
                                <Image
                                  src={game.cover_url?.replace('t_thumb', 't_cover_small') || 'https://placehold.co/90x120?text=No+Cover'}
                                  alt={game.name}
                                  className={classes.gameImage}
                                  fit="cover"
                                />
                                <div className={classes.auraEffect} />
                              </Box>
                            </Tooltip>
                          ))}
                        </Box>
                        {day.games.length > 4 && (
                          <Badge
                            component="button"
                            type="button"
                            onClick={() => setOpenDay({ date: day.date, games: day.games })}
                            className={classes.moreGamesBadge}
                            size="xs"
                            variant="filled"
                            color="blue"
                            style={{ cursor: 'pointer' }}
                          >
                            +{day.games.length - 4} more
                          </Badge>
                        )}
                      </Box>
                    )}
                    {day.games.length === 0 && day.isCurrentMonth && (
                      <Text className={classes.noGames} size="xs" c="dimmed" ta="center">No releases</Text>
                    )}
                  </Paper>
                </Grid.Col>
              ))}
            </Grid>
          ))
        )}
      </Paper>
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
                <Image
                  src={game.cover_url?.replace('t_cover_big', 't_cover_small') || 'https://placehold.co/45x64?text=%3F'}
                  w={36}
                  h={48}
                  radius="xs"
                  fit="cover"
                  alt=""
                />
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
    </Container>
  );
};

export default ModernCalendar;
