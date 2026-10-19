import { ActionIcon, Button, Group, MultiSelect, SegmentedControl, Title } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { useReleaseCalendar, type PeriodType } from '../hooks/useReleaseCalendar';
import { formatPeriodTitle } from '../utils/calendar.utils';
import classes from '../styles/PeriodToolbar.module.css';

/**
 * Top of every view: period title with previous/next, month/week toggle, and
 * console + genre filters. All of it drives the shared calendar state.
 */
const PeriodToolbar: React.FC = () => {
  const {
    periods: period,
    shiftPeriod,
    changePeriod,
    filterOptions,
    filters,
    setPlatformFilter,
    setGenreFilter,
  } = useReleaseCalendar();
  const filtered = filters.platforms.length > 0 || filters.genres.length > 0;

  return (
    <div className={classes.toolbar}>
      <Group gap="xs" wrap="nowrap" className={classes.period}>
        <ActionIcon variant="default" size="lg" onClick={() => shiftPeriod(-1)} aria-label={`Previous ${period.type}`}>
          <IconChevronLeft size={18} />
        </ActionIcon>
        <Title order={2} className={classes.title}>
          {formatPeriodTitle(period)}
        </Title>
        <ActionIcon variant="default" size="lg" onClick={() => shiftPeriod(1)} aria-label={`Next ${period.type}`}>
          <IconChevronRight size={18} />
        </ActionIcon>
        <SegmentedControl
          ml="sm"
          value={period.type}
          onChange={(value) => changePeriod({ type: value as PeriodType, date: period.date })}
          data={[
            { label: 'Month', value: 'month' },
            { label: 'Week', value: 'week' },
          ]}
          size="xs"
        />
      </Group>

      <Group gap="xs" wrap="wrap" className={classes.filters}>
        <MultiSelect
          aria-label="Filter by console"
          placeholder={filters.platforms.length ? undefined : 'All consoles'}
          data={filterOptions.platforms.map((p) => ({ value: String(p.id), label: p.name }))}
          value={filters.platforms.map(String)}
          onChange={(selected) => setPlatformFilter(selected.map(Number))}
          searchable
          clearable
          size="sm"
          maxDropdownHeight={280}
          className={classes.filter}
          classNames={{ pillsList: classes.pillsList, inputField: classes.inputField }}
        />
        <MultiSelect
          aria-label="Filter by genre"
          placeholder={filters.genres.length ? undefined : 'All genres'}
          data={filterOptions.genres.map((g) => ({ value: String(g.id), label: g.name }))}
          value={filters.genres.map(String)}
          onChange={(selected) => setGenreFilter(selected.map(Number))}
          searchable
          clearable
          size="sm"
          maxDropdownHeight={280}
          className={classes.filter}
          classNames={{ pillsList: classes.pillsList, inputField: classes.inputField }}
        />
        {filtered && (
          <Button
            variant="subtle"
            size="sm"
            onClick={() => {
              setPlatformFilter([]);
              setGenreFilter([]);
            }}
          >
            Clear
          </Button>
        )}
      </Group>
    </div>
  );
};

export default PeriodToolbar;
