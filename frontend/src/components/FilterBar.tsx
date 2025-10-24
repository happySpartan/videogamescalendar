import { useState, useEffect } from 'react';
import { MultiSelect, Group, Paper, SimpleGrid } from '@mantine/core';
import classes from '../styles/FilterBar.module.css';
import gameService from '../services/game.service';
import { FilterBarProps } from '../types/filterBar.types';
import { FilterOption } from '../types';

const FilterBar: React.FC<FilterBarProps> = ({ 
  platforms, 
  genres = [],
  languages = [],
  onPlatformFilterChange,
  onGenreFilterChange = () => {},
  onLanguageFilterChange = () => {}
}) => {
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [loading, setLoading] = useState({
    platforms: false,
    genres: false,
    languages: false
  });
  
  // Remove redundant filter fetching since GameLibraryContext handles it
  // useEffect(() => {
  //   fetchFilterData();
  // }, []);
  
  // Remove the merging logic since we now use props directly
  
  const handlePlatformChange = (selected: string[]) => {
    setSelectedPlatforms(selected);
    // Always pass the numeric IDs, even when empty
    const platformIds = selected.map(value => parseInt(value));
    onPlatformFilterChange(platformIds);
  };
  
  const handleGenreChange = (selected: string[]) => {
    setSelectedGenres(selected);
    // Always pass the numeric IDs, even when empty
    const genreIds = selected.map(value => parseInt(value));
    onGenreFilterChange(genreIds);
  };
  
  const handleLanguageChange = (selected: string[]) => {
    setSelectedLanguages(selected);
    // Always pass the numeric IDs, even when empty
    const languageIds = selected.map(value => parseInt(value));
    onLanguageFilterChange(languageIds);
  };
  
  return (
    <Paper p="md" radius="md" withBorder className={classes.filterBar}>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
        <MultiSelect
          label="Filter by Platform"
          placeholder="Select platforms..."
          data={platforms.map(p => ({ value: p.id.toString(), label: p.name }))}
          value={selectedPlatforms}
          onChange={handlePlatformChange}
          clearable={true}
          searchable={true}
          clearButtonProps={{ 'aria-label': 'Clear platforms' }}
          className={classes.filterSelect}
          disabled={loading.platforms}
        />

        <MultiSelect
          label="Filter by Genre"
          placeholder="Select genres..."
          data={genres.map(g => ({ value: g.id.toString(), label: g.name }))}
          value={selectedGenres}
          onChange={handleGenreChange}
          clearable={true}
          searchable={true}
          clearButtonProps={{ 'aria-label': 'Clear genres' }}
          className={classes.filterSelect}
          disabled={loading.genres}
        />

        <MultiSelect
          label="Filter by Language"
          placeholder="Select languages..."
          data={languages.map(l => ({ value: l.id.toString(), label: l.name }))}
          value={selectedLanguages}
          onChange={handleLanguageChange}
          clearable={true}
          searchable={true}
          clearButtonProps={{ 'aria-label': 'Clear languages' }}
          className={classes.filterSelect}
          disabled={loading.languages}
        />
      </SimpleGrid>
    </Paper>
  );
};

export default FilterBar;