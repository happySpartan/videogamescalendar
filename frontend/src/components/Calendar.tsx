import React, { useState, useEffect } from 'react';
import './Calendar.css';
import { Grid, Paper, Title, Container, Select, Text, Loader, Center } from '@mantine/core';
import { Game } from '../types';
import useApi from '../hooks/useApi';

const Calendar: React.FC = (): JSX.Element => {
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const api = useApi();

  // Fetch games data from the backend
  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      setError(null);
      try {
        // Format the date for API request: YYYY-MM
        const yearMonth = `${currentYear}-${(currentMonth + 1).toString().padStart(2, '0')}`;
        const response = await api.get<Game[]>(`/api/games?period=current_month`);
        setGames(response);
      } catch (err) {
        console.error('Error fetching games:', err);
        setError('Failed to load games data');
      } finally {
        setLoading(false);
      }
    };

    fetchGames();
  }, [currentMonth, currentYear, api]);

  // Helper function to get days in month
  const getDaysInMonth = (month: number, year: number): number => {
    return new Date(year, month + 1, 0).getDate();
  };

  // Helper function to get the first day of the month (0 = Sunday, 1 = Monday, etc.)
  const getFirstDayOfMonth = (month: number, year: number): number => {
    return new Date(year, month, 1).getDay();
  };

  const renderCalendarDays = (): JSX.Element[] => {
    const daysInMonth = getDaysInMonth(currentMonth, currentYear);
    const firstDay = getFirstDayOfMonth(currentMonth, currentYear);
    const days: React.ReactElement[] = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(
        <Grid.Col span={1.71} key={`empty-${i}`}>
          <Paper p="md" withBorder></Paper>
        </Grid.Col>
      );
    }

    // Add cells for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentYear, currentMonth, day);
      const dateString = date.toISOString().split('T')[0];
      const gamesOnThisDay = games.filter(game => {
        // Extract only date part from the game's release_date
        const gameDate = game.release_date ? game.release_date.split('T')[0] : '';
        return gameDate === dateString;
      });

      days.push(
        <Grid.Col span={1.71} key={day}>
          <Paper p="md" withBorder style={{ minHeight: '150px' }}>
            <Title order={4} style={{ marginBottom: '8px' }}>{day}</Title>
            {gamesOnThisDay.length > 0 ? (
              gamesOnThisDay.map(game => (
                <Paper p="xs" key={game.id} withBorder mb="xs">
                  <Text size="sm" fw={500}>{game.name}</Text>
                  {game.developer && <Text size="xs">{game.developer.name}</Text>}
                  {game.genre && <Text size="xs">{game.genre.name}</Text>}
                </Paper>
              ))
            ) : (
              <Text size="sm" color="dimmed">No releases</Text>
            )}
          </Paper>
        </Grid.Col>
      );
    }

    return days;
  };

  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  return (
    <div>
      <div className="calendar-select-container">
        <Select
          value={currentMonth.toString()}
          onChange={(value) => setCurrentMonth(Number(value))}
          data={months.map((month, index) => ({ 
            value: index.toString(), 
            label: month 
          }))}
          label="Select Month"
          style={{ width: 200 }}
        />
      </div>

      {loading ? (
        <Center h={200}>
          <Loader />
        </Center>
      ) : error ? (
        <Center h={200}>
          <Text color="red">{error}</Text>
        </Center>
      ) : (
        <Grid gutter="xs">
          {/* Week days header */}
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <Grid.Col span={1.71} key={day}>
              <Paper p="xs" bg="blue.1">
                <Title order={6}>{day}</Title>
              </Paper>
            </Grid.Col>
          ))}
          {renderCalendarDays()}
        </Grid>
      )}
    </div>
  );
};

export default Calendar;