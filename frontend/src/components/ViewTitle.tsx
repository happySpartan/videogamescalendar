import React from 'react';
import { Title, Group, Text, Button } from '@mantine/core';
import { IconFilter, IconChevronLeft } from '@tabler/icons-react';
// Updated CSS import path
import classes from '../styles/ViewTitle.module.css';
// Import ViewTitleProps from types
import { ViewTitleProps } from '../types/viewTitle.types';

const ViewTitle: React.FC<ViewTitleProps> = ({ 
  title, 
  subtitle, 
  showBackButton = false, 
  onBack,
  showFilters = false,
  onToggleFilters
}) => {
  return (
    <div className={classes.titleContainer}>
      <Group justify="space-between" align="center">
        <Group>
          {showBackButton && (
            <Button 
              variant="subtle" 
              leftSection={<IconChevronLeft size={16} />} 
              onClick={onBack}
            >
              Back
            </Button>
          )}
          <div>
            <Title order={2}>{title}</Title>
            {subtitle && <Text c="dimmed">{subtitle}</Text>}
          </div>
        </Group>
        
        {showFilters && (
          <Button 
            variant="light" 
            leftSection={<IconFilter size={16} />}
            onClick={onToggleFilters}
          >
            Filters
          </Button>
        )}
      </Group>
    </div>
  );
};

export default ViewTitle;
