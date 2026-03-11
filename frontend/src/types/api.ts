export type Theme = {
  main: string;
  sub: string;
  border: string;
  speech: string;
  nameplate_1: string;
  nameplate_2: string;
  image_main: string;
  image_sub: string;
};

export type MetricEntry = {
  slug: string;
  name_zh?: string | null;
  name_ja?: string | null;
  name_en?: string | null;
  chara_img?: string | null;
  height_cm?: number | null;
  bust_cm?: number | null;
  waist_cm?: number | null;
  hip_cm?: number | null;
  waist_to_hip?: number | null;
  waist_to_bust?: number | null;
  bust_to_hip?: number | null;
  value?: number | string | null;
  rank?: number;
};

export type CharacterImage = {
  path?: string | null;
  title?: string | null;
  ready: boolean;
};

export type CharacterCounts = {
  support_cards: number;
  character_cards: number;
  relations: number;
  main_comics: number;
};

export type ProfileFact = {
  key: string;
  label: string;
  value: string | number;
};

export type ProfileSection = {
  title: string;
  items: ProfileFact[];
};

export type SupportCard = {
  id: number | string;
  name?: string | null;
  title?: string | null;
  rarity?: number | null;
  published_at?: string | null;
  published_at_ts: number;
  command?: number | null;
  command_label: string;
  event_bonus: boolean;
};

export type CharacterDress = {
  id: number | string;
  title?: string | null;
  aliases?: string | null;
  published_at?: string | null;
  published_at_ts: number;
  limited: boolean;
  event_bonus: boolean;
  talents: Record<string, number | null | undefined>;
  aptitudes: Record<string, string | null | undefined>;
};

export type Relation = {
  slug: string;
  name_ja?: string | null;
  name_en?: string | null;
  theme: {
    main: string;
    sub: string;
    speech: string;
  };
};

export type CharacterSummary = {
  slug: string;
  name_zh?: string | null;
  name_ja?: string | null;
  name_en?: string | null;
  image: CharacterImage;
  theme: Theme;
  tagline: string;
  counts: CharacterCounts;
  metrics?: MetricEntry | null;
};

export type CharacterDetail = CharacterSummary & {
  description: string;
  profile_sections: ProfileSection[];
  support_cards: SupportCard[];
  character_cards: CharacterDress[];
  relations: Relation[];
  main_comics: Array<Record<string, unknown>>;
};

export type SiteStats = {
  total_characters: number;
  with_images: number;
  with_metrics: number;
  support_card_total: number;
  character_card_total: number;
  relation_total: number;
};

export type RankingMeta = {
  key: string;
  label: string;
  description: string;
  direction: "asc" | "desc";
  unit?: string;
};

export type RankingItem = {
  rank: number;
  slug: string;
  name_zh?: string | null;
  name_ja?: string | null;
  name_en?: string | null;
  value: number | string;
  chara_img?: string | null;
};

export type OverviewResponse = {
  ok: true;
  overview: {
    featured: CharacterSummary[];
    latest_outfits: CharacterSummary[];
    ranking_previews: Record<string, RankingItem[]>;
  };
  stats: SiteStats;
  updated_at_utc?: string | null;
};

export type CharactersResponse = {
  ok: true;
  items: CharacterSummary[];
  total: number;
  limit: number;
  offset: number;
  query: string;
};

export type CharacterResponse = {
  ok: true;
  item: CharacterDetail;
};

export type RankingsResponse = {
  ok: true;
  meta: RankingMeta[];
  rankings: Record<string, RankingItem[]>;
};

export type CompareResponse = {
  ok: true;
  items: CharacterDetail[];
};

export type Job = {
  id: string;
  action: string;
  command: string[];
  status: string;
  created_at_utc: string;
  started_at_utc?: string | null;
  finished_at_utc?: string | null;
  return_code?: number | null;
  error?: string | null;
  logs: string[];
};

export type JobsResponse = {
  ok: true;
  jobs: Job[];
};

export type JobResponse = {
  ok: true;
  job: Job;
};

export type AdminOverviewResponse = {
  ok: true;
  stats: SiteStats;
  updated_at_utc?: string | null;
  actions: string[];
  jobs: Job[];
};
