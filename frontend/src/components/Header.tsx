import { useCallback, memo } from 'react';
import { ActionIcon, Burger, Button, Group, SegmentedControl, Title, Tooltip } from '@mantine/core';
import { IconCalendar, IconChevronLeft, IconChevronRight, IconDownload } from '@tabler/icons-react';
import classes from '../styles/Header.module.css';
import { formatPeriodTitle, generateICS } from '../utils/calendar.utils';
import SearchBar from './SearchBar';
import SubscribeButton from './SubscribeButton';
import { STATIC_DATA } from '../api/client';
import { getPeriodBounds, useReleaseCalendar, type PeriodType } from '../hooks/useReleaseCalendar';

interface HeaderProps {
  navOpened: boolean;
  onToggleNav: () => void;
}

/**
 * App header: search, period navigation and month/week toggle drive the shared
 * calendar state (useReleaseCalendar), so they act on whichever view is open.
 * Desktop is one 60px row; below `md` it is two rows (see Layout header height).
 */
const MainHeader: React.FC<HeaderProps> = ({ navOpened, onToggleNav }) => {
  const {
    periods: period,
    filteredGames,
    searchQuery,
    setSearchQuery,
    changePeriod,
    shiftPeriod,
  } = useReleaseCalendar();

  const handleExportICS = useCallback(() => {
    generateICS(filteredGames, `game-releases-${getPeriodBounds(period).from}`);
  }, [period, filteredGames]);

  return (
    <header className={classes.header}>
      <div className={classes.inner}>
        <Group gap="xs" wrap="nowrap" className={classes.leftSection}>
          <Burger opened={navOpened} onClick={onToggleNav} hiddenFrom="sm" size="sm" aria-label="Toggle navigation" />
          <Group gap={6} wrap="nowrap" className={classes.titleSection}>
            <IconCalendar size={26} style={{ color: 'var(--mantine-color-violet-5)' }} />
            <Title order={2} size="h3" style={{ whiteSpace: 'nowrap' }}>
              Game Releases
            </Title>
          </Group>
          <div className={classes.searchSection}>
            <SearchBar value={searchQuery} onSearch={setSearchQuery} />
          </div>
        </Group>

        <Group gap="xs" wrap="nowrap" className={classes.centerGroup}>
          <ActionIcon variant="subtle" onClick={() => shiftPeriod(-1)} aria-label={`Previous ${period.type}`}>
            <IconChevronLeft size={18} />
          </ActionIcon>
          <Title order={3} className={classes.periodTitle}>
            {formatPeriodTitle(period)}
          </Title>
          <ActionIcon variant="subtle" onClick={() => shiftPeriod(1)} aria-label={`Next ${period.type}`}>
            <IconChevronRight size={18} />
          </ActionIcon>
        </Group>

        <Group gap="xs" wrap="nowrap" className={classes.rightSection}>
          <SegmentedControl
            value={period.type}
            onChange={(value) => changePeriod({ type: value as PeriodType, date: period.date })}
            data={[
              { label: 'Month', value: 'month' },
              { label: 'Week', value: 'week' },
            ]}
            size="xs"
          />
          <Tooltip label="Download the releases shown as an .ics file">
            <Button
              leftSection={<IconDownload size={16} />}
              variant="filled"
              size="xs"
              onClick={handleExportICS}
              disabled={filteredGames.length === 0}
            >
              Export
            </Button>
          </Tooltip>

          {/* Feeds exist only in the static build (ADR-0004), not behind the API. */}
          {STATIC_DATA && <SubscribeButton />}
        </Group>
      </div>
    </header>
  );
};

export default memo(MainHeader);
