import { useCallback, memo } from 'react';
import { Link } from 'react-router-dom';
import { Burger, Button, Group, Text, Tooltip } from '@mantine/core';
import { IconCalendarEvent, IconDownload } from '@tabler/icons-react';
import classes from '../styles/Header.module.css';
import { generateICS } from '../utils/calendar.utils';
import SearchBar from './SearchBar';
import SubscribeButton from './SubscribeButton';
import { STATIC_DATA } from '../api/client';
import { getPeriodBounds, useReleaseCalendar } from '../hooks/useReleaseCalendar';

interface HeaderProps {
  navOpened: boolean;
  onToggleNav: () => void;
}

/**
 * App header: brand, search (with suggestions) and the calendar actions.
 * Period navigation and filters live in each view's toolbar.
 */
const MainHeader: React.FC<HeaderProps> = ({ navOpened, onToggleNav }) => {
  const { periods: period, filteredGames, searchQuery, setSearchQuery } = useReleaseCalendar();

  const handleExportICS = useCallback(() => {
    generateICS(filteredGames, `game-releases-${getPeriodBounds(period).from}`);
  }, [period, filteredGames]);

  return (
    <header className={classes.header}>
      <Burger opened={navOpened} onClick={onToggleNav} hiddenFrom="sm" size="sm" aria-label="Toggle navigation" />
      <Link to="/" className={classes.brand} aria-label="Video game release calendar, home">
        <IconCalendarEvent size={22} stroke={1.8} className={classes.brandIcon} />
        <Text component="span" className={classes.brandName}>
          Release Calendar
        </Text>
      </Link>

      <div className={classes.search}>
        <SearchBar value={searchQuery} onSearch={setSearchQuery} />
      </div>

      <Group gap="xs" wrap="nowrap" className={classes.actions}>
        <Tooltip label="Download the releases shown as an .ics file">
          <Button
            leftSection={<IconDownload size={16} />}
            variant="default"
            size="sm"
            onClick={handleExportICS}
            disabled={filteredGames.length === 0}
          >
            Export
          </Button>
        </Tooltip>
        {/* Feeds exist only in the static build (ADR-0004), not behind the API. */}
        {STATIC_DATA && <SubscribeButton />}
      </Group>
    </header>
  );
};

export default memo(MainHeader);
