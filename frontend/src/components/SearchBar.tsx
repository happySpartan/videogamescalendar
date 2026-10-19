import { useState, useRef, useEffect } from 'react';
import { TextInput, ActionIcon } from '@mantine/core';
import { IconSearch, IconX } from '@tabler/icons-react';
// Updated CSS import path
import classes from '../styles/SearchBar.module.css';

interface SearchBarProps {
  /** Current search text held by the parent; the input follows it when it changes. */
  value?: string;
  onSearch: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ value: externalValue, onSearch }) => {
  const [value, setValue] = useState(externalValue ?? '');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Follow outside changes (e.g. filters reset). Only fires when the parent's
  // value changes, which while typing happens after the debounce, so it does
  // not overwrite what is being typed.
  useEffect(() => {
    if (externalValue !== undefined) setValue(externalValue);
  }, [externalValue]);

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
        size="sm"
      />
    </div>
  );
};

export default SearchBar;
