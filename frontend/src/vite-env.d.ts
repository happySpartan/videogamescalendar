/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GAME_API_URL?: string;
  /** 'static' reads the JSON export under <base>/data instead of the API. */
  readonly VITE_DATA_MODE?: string;
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
