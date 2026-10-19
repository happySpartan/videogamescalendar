// "Subscribe" dialog for the calendar feeds the static export writes
// (calendar.ics + one feed per platform). Calendar apps re-fetch the feed, so
// date changes and new releases show up without re-importing.
import { useState } from 'react';
import { Anchor, Button, CopyButton, Group, Modal, Select, Stack, Text, TextInput } from '@mantine/core';
import { IconBrandGoogle, IconCalendarPlus, IconCheck, IconCopy } from '@tabler/icons-react';
import { calendarFeedUrl } from '../api/client';
import { usePlatforms } from '../hooks/queries';

const SubscribeButton: React.FC = () => {
  const [opened, setOpened] = useState(false);
  const [platformId, setPlatformId] = useState<string | null>(null);
  const { data: platforms } = usePlatforms();

  const feedUrl = calendarFeedUrl(platformId ? Number(platformId) : undefined);
  const webcalUrl = feedUrl.replace(/^https?:/, 'webcal:');
  const googleUrl = `https://calendar.google.com/calendar/render?cid=${encodeURIComponent(webcalUrl)}`;
  // Every platform in platforms.json has a feed file (both come from the same export).
  const platformOptions = (platforms ?? []).map((p) => ({ value: String(p.id), label: p.name }));

  return (
    <>
      <Button
        ml="md"
        leftSection={<IconCalendarPlus size={16} />}
        variant="filled"
        color="grape"
        onClick={() => setOpened(true)}
      >
        Subscribe
      </Button>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Subscribe to releases" size="lg" centered>
        <Stack gap="md">
          <Text size="sm">
            Add release dates to Google, Apple or Outlook Calendar. The feed refreshes on its own
            when dates change.
          </Text>

          <Select
            label="Platform"
            placeholder="All platforms"
            data={platformOptions}
            value={platformId}
            onChange={setPlatformId}
            searchable
            clearable
          />

          <Group grow>
            <Button component="a" href={webcalUrl} leftSection={<IconCalendarPlus size={16} />}>
              Open in calendar app
            </Button>
            <Button
              component="a"
              href={googleUrl}
              target="_blank"
              rel="noopener noreferrer"
              variant="light"
              leftSection={<IconBrandGoogle size={16} />}
            >
              Google Calendar
            </Button>
          </Group>

          <TextInput
            label="Feed URL"
            description="For Outlook or other apps: add a calendar from the internet and paste this."
            value={feedUrl}
            readOnly
            onFocus={(e) => e.currentTarget.select()}
            rightSectionWidth={90}
            rightSection={
              <CopyButton value={feedUrl}>
                {({ copied, copy }) => (
                  <Button
                    size="compact-xs"
                    variant="subtle"
                    color={copied ? 'teal' : 'blue'}
                    onClick={copy}
                    leftSection={copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </Button>
                )}
              </CopyButton>
            }
          />

          <Text size="xs" c="dimmed">
            Or download it once: <Anchor href={feedUrl} size="xs">{feedUrl.split('/').pop()}</Anchor>
          </Text>
        </Stack>
      </Modal>
    </>
  );
};

export default SubscribeButton;
