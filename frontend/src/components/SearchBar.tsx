import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CloseButton, Combobox, Group, Loader, Text, TextInput, useCombobox } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useDebounce } from '../hooks/useDebounce';
import { useSearchSuggestions } from '../hooks/queries';
import classes from '../styles/SearchBar.module.css';

interface SearchBarProps {
  /** Current search text held by the parent; the input follows it when it changes. */
  value?: string;
  /** Called (debounced) with the text, to filter the open view. */
  onSearch: (query: string) => void;
}

const formatDay = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'TBA';

/**
 * Search box: filters the open view as you type and suggests matching games
 * from every exported month; picking a suggestion opens its page.
 */
const SearchBar: React.FC<SearchBarProps> = ({ value: externalValue, onSearch }) => {
  const navigate = useNavigate();
  const combobox = useCombobox({ onDropdownClose: () => combobox.resetSelectedOption() });
  const [text, setText] = useState(externalValue ?? '');
  const debounced = useDebounce(text, 250);
  const { data: hits = [], isFetching } = useSearchSuggestions(debounced);

  // Follow outside changes (e.g. filters reset); only fires when the parent's
  // value changes, which while typing happens after the debounce.
  useEffect(() => {
    if (externalValue !== undefined) setText(externalValue);
  }, [externalValue]);

  useEffect(() => {
    onSearch(debounced);
  }, [debounced, onSearch]);

  const open = (id: string) => {
    combobox.closeDropdown();
    setText('');
    onSearch('');
    navigate(`/game/${id}`);
  };

  const showDropdown = text.trim().length > 0;

  return (
    <Combobox store={combobox} onOptionSubmit={open} withinPortal position="bottom-start" width="target">
      <Combobox.Target>
        <TextInput
          className={classes.searchInput}
          placeholder="Search games…"
          aria-label="Search games"
          value={text}
          radius="md"
          leftSection={<IconSearch size={16} />}
          rightSection={
            isFetching && showDropdown ? (
              <Loader size={14} />
            ) : text ? (
              <CloseButton
                size="sm"
                aria-label="Clear search"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  setText('');
                  onSearch('');
                  combobox.closeDropdown();
                }}
              />
            ) : null
          }
          onChange={(e) => {
            setText(e.currentTarget.value);
            combobox.openDropdown();
            combobox.updateSelectedOptionIndex();
          }}
          onFocus={() => showDropdown && combobox.openDropdown()}
          onBlur={() => combobox.closeDropdown()}
          onKeyDown={(e) => {
            if (e.key === 'Escape') combobox.closeDropdown();
          }}
        />
      </Combobox.Target>

      <Combobox.Dropdown hidden={!showDropdown}>
        <Combobox.Options>
          {hits.length === 0 ? (
            <Combobox.Empty>{isFetching ? 'Searching…' : 'No games match'}</Combobox.Empty>
          ) : (
            hits.map((hit) => (
              <Combobox.Option value={String(hit.id)} key={hit.id}>
                <Group gap="sm" wrap="nowrap">
                  <span className={classes.thumb}>
                    {hit.cover_url && <img src={hit.cover_url.replace('t_cover_big', 't_cover_small')} alt="" />}
                  </span>
                  <div style={{ minWidth: 0 }}>
                    <Text size="sm" fw={500} truncate>
                      {hit.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {formatDay(hit.release_date)}
                    </Text>
                  </div>
                </Group>
              </Combobox.Option>
            ))
          )}
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
};

export default SearchBar;
