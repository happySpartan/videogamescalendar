import React, { useMemo } from 'react';
import { Container, Paper, Title, Group, Badge, Image, Tooltip, Box, Stack, Grid, Text } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { useGameLibrary } from '../context/GameLibraryContext';
import { Game } from '../types';
import classes from '../styles/ModernCalendar.module.css';

const ModernCalendar: React.FC = () => {
  const { filteredGames, period, changePeriod } = useGameLibrary();

  // Get the current month's calendar grid
  const calendarData = useMemo(() => {
    const year = period.date.getFullYear();
    const month = period.date.getMonth();

    // Get first day of month and total days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    const weeks: Array<Array<{ date: Date; isCurrentMonth: boolean; games: Game[] }>> = [];
    let currentWeek: Array<{ date: Date; isCurrentMonth: boolean; games: Game[] }> = [];

    // Fill in days from previous month
    for (let i = firstDay - 1; i >= 0; i--) {
      const date = new Date(year, month - 1, daysInPrevMonth - i);
      currentWeek.push({
        date,
        isCurrentMonth: false,
        games: []
      });
    }

    // Fill in days of current month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateString = date.toISOString().split('T')[0];

      // Filter games for this day
      const gamesOnDay = filteredGames.filter(game => {
        if (!game.release_date) return false;
        const gameDate = game.release_date.split('T')[0];
        return gameDate === dateString;
      });

      currentWeek.push({
        date,
        isCurrentMonth: true,
        games: gamesOnDay
      });

      // Start new week on Sunday
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    }

    // Fill in days from next month
    if (currentWeek.length > 0) {
      const remainingDays = 7 - currentWeek.length;
      for (let day = 1; day <= remainingDays; day++) {
        const date = new Date(year, month + 1, day);
        currentWeek.push({
          date,
          isCurrentMonth: false,
          games: []
        });
      }
      weeks.push(currentWeek);
    }

    return weeks;
  }, [filteredGames, period.date]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const handlePrevMonth = () => {
    const newDate = new Date(period.date);
    newDate.setMonth(newDate.getMonth() - 1);
    changePeriod('month', newDate);
  };

  const handleNextMonth = () => {
    const newDate = new Date(period.date);
    newDate.setMonth(newDate.getMonth() + 1);
    changePeriod('month', newDate);
  };

  return (
    <Container size="100%" className={classes.calendarContainer}>
      {/* Header with Month Navigation */}
      <Paper className={classes.header} p="lg" mb="md">
        <Group justify="space-between" align="center">
          <Box
            className={classes.navButton}
            onClick={handlePrevMonth}
          >
            <IconChevronLeft size={24} />
          </Box>

          <Title order={2} className={classes.monthTitle}>
            {monthNames[period.date.getMonth()]} {period.date.getFullYear()}
          </Title>

          <Box
            className={classes.navButton}
            onClick={handleNextMonth}
          >
            <IconChevronRight size={24} />
          </Box>
        </Group>
      </Paper>

      {/* Calendar Grid */}
      <Paper className={classes.calendarGrid}>
        {/* Week Days Header */}
        <Grid className={classes.weekDaysHeader} gutter={4}>
          {weekDays.map((day) => (
            <Grid.Col key={day} span={{ base: 12 / 7 }}>
              <Text className={classes.weekDay} ta="center" fw={600} size="sm">
                {day.slice(0, 3)}
              </Text>
            </Grid.Col>
          ))}
        </Grid>

        {/* Calendar Weeks */}
        {calendarData.map((week, weekIdx) => (
          <Grid key={weekIdx} className={classes.calendarWeek} gutter={4}>
            {week.map((day, dayIdx) => (
              <Grid.Col key={dayIdx} span={{ base: 12 / 7 }}>
                <Paper
                  className={`${classes.dayCell} ${
                    !day.isCurrentMonth ? classes.otherMonth : ''
                  } ${day.games.length > 0 ? classes.hasGames : ''}`}
                >
                  {/* Day Number */}
                  <Text className={classes.dayNumber} fw={600}>
                    {day.date.getDate()}
                  </Text>

                  {/* Games for this day */}
                  {day.games.length > 0 && (
                    <Box className={classes.gamesContainer}>
                      <Box className={classes.gamesGrid}>
                        {day.games.slice(0, 4).map((game) => (
                          <Tooltip
                            key={game.id}
                            label={
                              <Stack gap={4}>
                                <Text fw={600} size="sm">{game.name}</Text>
                                {game.developer && (
                                  <Text size="xs" c="dimmed">{game.developer.name}</Text>
                                )}
                                {game.genre && (
                                  <Badge size="xs" variant="light">{game.genre.name}</Badge>
                                )}
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
                              {/* Aura effect */}
                              <div className={classes.auraEffect} />
                            </Box>
                          </Tooltip>
                        ))}
                      </Box>

                      {/* Show count if more than 4 games */}
                      {day.games.length > 4 && (
                        <Badge
                          className={classes.moreGamesBadge}
                          size="xs"
                          variant="filled"
                          color="blue"
                        >
                          +{day.games.length - 4} more
                        </Badge>
                      )}
                    </Box>
                  )}

                  {/* No games indicator */}
                  {day.games.length === 0 && day.isCurrentMonth && (
                    <Text className={classes.noGames} size="xs" c="dimmed" ta="center">
                      No releases
                    </Text>
                  )}
                </Paper>
              </Grid.Col>
            ))}
          </Grid>
        ))}
      </Paper>
    </Container>
  );
};

export default ModernCalendar;
