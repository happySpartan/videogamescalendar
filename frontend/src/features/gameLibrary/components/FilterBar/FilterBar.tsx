import React from 'react';
import { Box, MultiSelect, Button } from '@mantine/core';
import { Game } from '../../../../types';
import classes from './FilterBar.module.css';

interface FilterBarProps {
  games: Game[];
  filterOptions: {
    platforms: { value: string; label: string }[];
    genres: { value: string; label: string }[];
    languages: { value: string; label: string }[];
  };
  onPlatformFilter: (value: string[]) => void;
  onGenreFilter: (value: string[]) => void;
  onLanguageFilter: (value: string[]) => void;
  onClearFilters: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filterOptions,
  onPlatformFilter,
  onGenreFilter,
  onLanguageFilter,
  onClearFilters,
}) => {
  return (
    <Box className={classes.filterBar}>
      <MultiSelect
        data={filterOptions.platforms}
        placeholder="Filter by platform"
        onChange={onPlatformFilter}
        searchable
        clearable
        className={classes.select}
      />
      <MultiSelect
        data={filterOptions.genres}
        placeholder="Filter by genre"
        onChange={onGenreFilter}
        searchable
        clearable
        className={classes.select}
      />
      <MultiSelect
        data={filterOptions.languages}
        placeholder="Filter by language"
        onChange={onLanguageFilter}
        searchable
        clearable
        className={classes.select}
      />
      <Button 
        onClick={onClearFilters}
        variant="outline"
        className={classes.clearButton}
      >
        Clear Filters
      </Button>
    </Box>
  );
};

export default FilterBar;
