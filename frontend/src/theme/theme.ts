import { createTheme, type MantineColorsTuple } from '@mantine/core';

// Sober, game-adjacent look: graphite neutrals, cover art as the colour, one
// restrained accent. Values mirror the CSS variables in styles/main.css.

// Accent: a calm cobalt (Mantine needs 10 shades, light to dark).
const brand: MantineColorsTuple = [
  '#eef1ff', '#dbe1ff', '#b4c1ff', '#8a9eff', '#6a82fb',
  '#5670f2', '#4a64eb', '#3b53d1', '#3249bb', '#253da5',
];

// Graphite neutrals for dark mode (dark[7] = page, dark[6] = surfaces).
const dark: MantineColorsTuple = [
  '#e7e9ee', '#c3c7cf', '#9097a3', '#6b7280', '#3a404b',
  '#2a2f39', '#1c2029', '#14171d', '#0f1115', '#0a0c0f',
];

export const appTheme = createTheme({
  primaryColor: 'brand',
  primaryShade: { light: 6, dark: 5 },
  colors: { brand, dark },
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  headings: { fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', fontWeight: '650' },
  defaultRadius: 'md',
  components: {
    Container: { defaultProps: { size: 'xl', px: 'md' } },
    Paper: { defaultProps: { radius: 'md' } },
    Badge: { defaultProps: { radius: 'sm' } },
  },
});

export default appTheme;
