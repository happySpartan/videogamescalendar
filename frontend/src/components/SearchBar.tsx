import { useState, useRef, useEffect } from 'react';
import { TextInput, ActionIcon } from '@mantine/core';
import { IconSearch, IconX } from '@tabler/icons-react';
// Updated CSS import path
import classes from '../styles/SearchBar.module.css';

interface SearchBarProps {
  onSearch: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Use debouncing to prevent too many search events
  useEffect(() => {
    // Clear any existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    // Set a new timer for the search
    timerRef.current = setTimeout(() => {
      onSearch(value);
    }, 300);

    // Cleanup function to clear the timer if component unmounts or value changes again
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [value, onSearch]);

  const handleFocus = () => {
    setFocused(true);
  };

  const handleBlur = () => {
    if (value === '') {
      setFocused(false);
    }
  };

  const clearSearch = () => {
    setValue('');
    onSearch('');
    inputRef.current?.focus();
  };

  return (
    <div className={`${classes.searchContainer} ${focused || value ? classes.expanded : ''}`}>
      <TextInput
        ref={inputRef}
        placeholder="Search games..."
        value={value}
        onChange={(event) => setValue(event.currentTarget.value)}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className={classes.searchInput}
        leftSection={<IconSearch size={18} />}
        rightSection={
          value && (
            <ActionIcon onClick={clearSearch} variant="subtle" color="gray">
              <IconX size={18} />
            </ActionIcon>
          )
        }
        radius="xl"
        size="md"
      />
    </div>
  );
};

export default SearchBar;
