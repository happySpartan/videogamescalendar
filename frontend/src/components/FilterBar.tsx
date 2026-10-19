import { MultiSelect, Paper, SimpleGrid } from '@mantine/core';
import classes from '../styles/FilterBar.module.css';
import { useReleaseCalendar } from '../hooks/useReleaseCalendar';

/** Platform + genre filters, bound to the shared calendar state. */
const FilterBar: React.FC = () => {
  const { filterOptions, filters, setPlatformFilter, setGenreFilter } = useReleaseCalendar();

  return (
    <Paper p="md" radius="md" withBorder className={classes.filterBar}>
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <MultiSelect
          label="Filter by Platform"
          placeholder="Select platforms..."
          data={filterOptions.platforms.map((p) => ({ value: String(p.id), label: p.name }))}
          value={filters.platforms.map(String)}
          onChange={(selected) => setPlatformFilter(selected.map(Number))}
          clearable
          searchable
          clearButtonProps={{ 'aria-label': 'Clear platforms' }}
          className={classes.filterSelect}
        />

        <MultiSelect
          label="Filter by Genre"
          placeholder="Select genres..."
          data={filterOptions.genres.map((g) => ({ value: String(g.id), label: g.name }))}
          value={filters.genres.map(String)}
          onChange={(selected) => setGenreFilter(selected.map(Number))}
          clearable
          searchable
          clearButtonProps={{ 'aria-label': 'Clear genres' }}
          className={classes.filterSelect}
        />
      </SimpleGrid>
    </Paper>
  );
};

export default FilterBar;
