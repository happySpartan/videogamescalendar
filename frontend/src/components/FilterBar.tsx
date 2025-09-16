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
  const [allPlatforms, setAllPlatforms] = useState<FilterOption[]>(platforms);
  const [allGenres, setAllGenres] = useState<FilterOption[]>(genres);
  const [allLanguages, setAllLanguages] = useState<FilterOption[]>(languages);
  const [loading, setLoading] = useState({
    platforms: false,
    genres: false,
    languages: false
  });
  
  // Fetch filter data on component mount
  useEffect(() => {
    async function fetchFilterData() {
      try {
        setLoading({
          platforms: true,
          genres: true,
          languages: true
        });
        
        // Fetch all filter data in parallel
        const [platformData, genreData, languageData] = await Promise.all([
          gameService.getPlatforms(),
          gameService.getGenres(),
          gameService.getLanguages()
        ]);
        
        // Update state with fetched data
        setAllPlatforms(platformData);
        setAllGenres(genreData);
        setAllLanguages(languageData);
      } catch (error) {
        console.error('Error fetching filter data:', error);
      } finally {
        setLoading({
          platforms: false,
          genres: false,
          languages: false
        });
      }
    }
    
    fetchFilterData();
  }, []);
  
  // When props change, merge with our fetched data
  useEffect(() => {
    // Merge with existing platforms without duplicates
    if (platforms.length > 0) {
      setAllPlatforms(prev => {
        const merged = [...prev];
        platforms.forEach(platform => {
          if (!merged.some(p => p.id === platform.id)) {
            merged.push(platform);
          }
        });
        return merged;
      });
    }
    
    if (genres.length > 0) {
      setAllGenres(prev => {
        const merged = [...prev];
        genres.forEach(genre => {
          if (!merged.some(g => g.id === genre.id)) {
            merged.push(genre);
          }
        });
        return merged;
      });
    }
    
    if (languages.length > 0) {
      setAllLanguages(prev => {
        const merged = [...prev];
        languages.forEach(language => {
          if (!merged.some(l => l.id === language.id)) {
            merged.push(language);
          }
        });
        return merged;
      });
    }
  }, [platforms, genres, languages]);
  
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
          data={allPlatforms.map(p => ({ value: p.id.toString(), label: p.name }))}
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
          data={allGenres.map(g => ({ value: g.id.toString(), label: g.name }))}
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
          data={allLanguages.map(l => ({ value: l.id.toString(), label: l.name }))}
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