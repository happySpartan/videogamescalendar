import { useMemo, useState } from 'react';
import { Container, Paper, Title, Group, Badge, Image, Tooltip, Box, Stack, Grid, Text, Loader, Center, Alert } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { useReleases } from '../hooks/queries';
import type { Release } from '../api/types';
import classes from '../styles/ModernCalendar.module.css';

const pad = (n: number) => String(n).padStart(2, '0');

const ModernCalendar: React.FC = () => {
  const [monthDate, setMonthDate] = useState<Date>(() => new Date());

  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const monthStart = `${year}-${pad(month + 1)}-01`;
  const lastDay = new Date(year, month + 1, 0).getDate();
  const monthEnd = `${year}-${pad(month + 1)}-${pad(lastDay)}`;

  const { data, isPending, isError, error } = useReleases({ from: monthStart, to: monthEnd, limit: 300 });
  const releases: Release[] = data?.releases ?? [];

  // Build the calendar grid (weeks of day-cells) for the current month.
  const calendarData = useMemo(() => {
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    const weeks: Array<Array<{ date: Date; isCurrentMonth: boolean; games: Release[] }>> = [];
    let currentWeek: Array<{ date: Date; isCurrentMonth: boolean; games: Release[] }> = [];

    for (let i = firstDay - 1; i >= 0; i--) {
      currentWeek.push({ date: new Date(year, month - 1, daysInPrevMonth - i), isCurrentMonth: false, games: [] });
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateString = `${year}-${pad(month + 1)}-${pad(day)}`;
      const gamesOnDay = releases.filter((g) => g.release_date?.slice(0, 10) === dateString);
      currentWeek.push({ date, isCurrentMonth: true, games: gamesOnDay });
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        const day = currentWeek.length + 1;
        currentWeek.push({ date: new Date(year, month + 1, day), isCurrentMonth: false, games: [] });
      }
      weeks.push(currentWeek);
    }
    return weeks;
  }, [releases, year, month]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];
  const weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const shiftMonth = (delta: number) => {
    setMonthDate((d) => new Date(d.getFullYear(), d.getMonth() + delta, 1));
  };

  return (
    <Container size="100%" className={classes.calendarContainer}>
      <Paper className={classes.header} p="lg" mb="md">
        <Group justify="space-between" align="center">
          <Box className={classes.navButton} onClick={() => shiftMonth(-1)}>
            <IconChevronLeft size={24} />
          </Box>
          <Title order={2} className={classes.monthTitle}>
            {monthNames[monthDate.getMonth()]} {monthDate.getFullYear()}
          </Title>
          <Box className={classes.navButton} onClick={() => shiftMonth(1)}>
            <IconChevronRight size={24} />
          </Box>
        </Group>
      </Paper>

      {isError && (
        <Alert color="red" title="Failed to load releases" mb="md">
          {error instanceof Error ? error.message : 'Could not reach the API'}
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

        {isPending ? (
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
                              <Box className={classes.gameImageWrapper}>
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
                          <Badge className={classes.moreGamesBadge} size="xs" variant="filled" color="blue">
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
    </Container>
  );
};

export default ModernCalendar;
