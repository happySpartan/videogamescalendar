import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Alert,
  Anchor,
  AspectRatio,
  Badge,
  Button,
  Container,
  Flex,
  Group,
  Image,
  Loader,
  Modal,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from '@mantine/core';
import { IconArrowLeft, IconExternalLink, IconPlayerPlayFilled } from '@tabler/icons-react';
import { useRelease } from '../hooks/queries';
import { formatDate } from '../utils/game.utils';
import type { GameVideo, GameWebsite } from '../api/types';
import classes from '../styles/GameDetail.module.css';

/** IGDB image URL at another size, e.g. t_screenshot_big -> t_screenshot_med. */
const resize = (url: string, size: string) => url.replace(/\/t_[a-z0-9_]+\//, `/${size}/`);

/** YouTube player that loads only when clicked (thumbnail until then). */
const Trailer: React.FC<{ video: GameVideo }> = ({ video }) => {
  const [playing, setPlaying] = useState(false);
  return (
    <AspectRatio ratio={16 / 9} className={classes.trailer} maw={860}>
      {playing ? (
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${video.video_id}?autoplay=1`}
          title={video.name ?? 'Trailer'}
          allow="autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <UnstyledButton onClick={() => setPlaying(true)} className={classes.trailerPoster} aria-label={`Play ${video.name ?? 'trailer'}`}>
          <img src={`https://i.ytimg.com/vi/${video.video_id}/hqdefault.jpg`} alt="" loading="lazy" />
          <IconPlayerPlayFilled size={56} className={classes.playIcon} />
        </UnstyledButton>
      )}
    </AspectRatio>
  );
};

/** Social/community hosts, labelled by name and listed after official sites. */
const SOCIAL: Record<string, string> = {
  'discord.gg': 'Discord',
  'discord.com': 'Discord',
  'youtube.com': 'YouTube',
  'x.com': 'X',
  'twitter.com': 'X',
  'instagram.com': 'Instagram',
  'twitch.tv': 'Twitch',
  'facebook.com': 'Facebook',
  'bsky.app': 'Bluesky',
  'reddit.com': 'Reddit',
  'tiktok.com': 'TikTok',
  'en.wikipedia.org': 'Wikipedia',
};

/** Host without "www."; empty if the URL does not parse. */
const hostOf = (url: string) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
};

/** Store buttons, then official sites before social links (up to four). */
const Links: React.FC<{ websites: GameWebsite[] }> = ({ websites }) => {
  const stores = websites.filter((w) => w.store);
  const others = websites
    .filter((w) => !w.store && hostOf(w.url))
    .map((w) => ({ url: w.url, social: SOCIAL[hostOf(w.url)] }))
    .sort((a, b) => Number(Boolean(a.social)) - Number(Boolean(b.social)))
    .filter((w, i, all) => !w.social || all.findIndex((x) => x.social === w.social) === i)
    .slice(0, 4);
  if (stores.length === 0 && others.length === 0) return null;
  return (
    <Stack gap="xs">
      {stores.length > 0 && (
        <Group gap="xs">
          {stores.map((w) => (
            <Button
              key={w.url}
              component="a"
              href={w.url}
              target="_blank"
              rel="noopener noreferrer"
              variant="light"
              size="xs"
              rightSection={<IconExternalLink size={14} />}
            >
              {w.store}
            </Button>
          ))}
        </Group>
      )}
      {others.length > 0 && (
        <Group gap="md">
          {others.map((w) => (
            <Anchor key={w.url} href={w.url} target="_blank" rel="noopener noreferrer" size="sm">
              {w.social ?? hostOf(w.url)}
            </Anchor>
          ))}
        </Group>
      )}
    </Stack>
  );
};

const GameDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: game, isPending, isError, error } = useRelease(id ?? '');
  const [videoIndex, setVideoIndex] = useState(0);
  const [shown, setShown] = useState<string | null>(null);

  if (isPending) {
    return (
      <Container py="xl" ta="center">
        <Loader />
      </Container>
    );
  }

  if (isError || !game) {
    return (
      <Container py="xl">
        <Alert color="red" title="Could not load game">
          {error instanceof Error ? error.message : 'Game not found'}
        </Alert>
        <Link to="/">Back to calendar</Link>
      </Container>
    );
  }

  const videos = game.videos ?? [];
  const screenshots = game.screenshots ?? [];
  const companies = game.companies ?? [];

  return (
    <Container size="lg" py="xl">
      <Button component={Link} to="/" variant="subtle" leftSection={<IconArrowLeft size={16} />} mb="sm">
        Back to calendar
      </Button>

      <Paper p="lg" radius="md" withBorder>
        <Stack gap="lg">
          <Flex gap="lg" direction={{ base: 'column', sm: 'row' }} align={{ base: 'center', sm: 'flex-start' }}>
            <Image
              src={game.cover_url?.replace('t_thumb', 't_cover_big') || 'https://placehold.co/264x352?text=No+Cover'}
              alt={game.name}
              fit="cover"
              w={220}
              radius="md"
            />
            <Stack gap="sm" style={{ flex: 1 }}>
              <Title order={1}>{game.name}</Title>
              <Text c="dimmed">
                {game.release_date ? `Releases ${formatDate(game.release_date)}` : 'Release date TBA'}
                {companies.length > 0 && ` · by ${companies.map((c) => c.name).join(', ')}`}
              </Text>
              <Group gap="xs">
                {game.genres.map((g) => (
                  <Badge key={g.id} variant="light" tt="none">{g.name}</Badge>
                ))}
                {game.platforms.map((p) => (
                  <Badge key={p.id} variant="default" tt="none">{p.abbreviation || p.name}</Badge>
                ))}
              </Group>
              {game.summary && <Text>{game.summary}</Text>}
              <Links websites={game.websites ?? []} />
            </Stack>
          </Flex>

          {videos.length > 0 && (
            <Stack gap="xs">
              <Title order={3}>Trailers</Title>
              <Trailer key={videos[videoIndex].video_id} video={videos[videoIndex]} />
              {videos.length > 1 && (
                <Group gap="xs">
                  {videos.slice(0, 8).map((v, i) => (
                    <Button
                      key={v.video_id}
                      size="compact-sm"
                      variant={i === videoIndex ? 'filled' : 'default'}
                      onClick={() => setVideoIndex(i)}
                    >
                      {v.name || `Video ${i + 1}`}
                    </Button>
                  ))}
                </Group>
              )}
            </Stack>
          )}

          {screenshots.length > 0 && (
            <Stack gap="xs">
              <Title order={3}>Screenshots</Title>
              <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="xs">
                {screenshots.map((url) => (
                  <UnstyledButton key={url} onClick={() => setShown(url)} aria-label="View screenshot">
                    <AspectRatio ratio={16 / 9}>
                      <Image src={resize(url, 't_screenshot_med')} radius="sm" loading="lazy" alt="" />
                    </AspectRatio>
                  </UnstyledButton>
                ))}
              </SimpleGrid>
            </Stack>
          )}
        </Stack>
      </Paper>

      <Modal opened={shown !== null} onClose={() => setShown(null)} size="auto" centered withCloseButton={false} padding={0}>
        {shown && <Image src={resize(shown, 't_1080p')} alt="" className={classes.fullScreenshot} />}
      </Modal>
    </Container>
  );
};

export default GameDetailPage;
