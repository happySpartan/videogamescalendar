import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import Layout from './components/Layout';
import CalendarPage from './pages/CalendarPage';
import GameGridPage from './pages/GameGridPage';
import ListPage from './pages/ListPage';
import GameDetailPage from './pages/GameDetailPage';
import appTheme from './theme/theme';

const App: React.FC = () => {
  return (
    <MantineProvider theme={appTheme} forceColorScheme="dark">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<CalendarPage />} />
          <Route path="home" element={<GameGridPage />} />
          <Route path="list" element={<ListPage />} />
          <Route path="game/:id" element={<GameDetailPage />} />
        </Route>
      </Routes>
    </MantineProvider>
  );
};

export default App;
