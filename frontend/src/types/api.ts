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
  threesize_text?: string | null;
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

export type CharacterFilters = {
  birthday_month?: number | null;
  distance_tags: string[];
  style_tags: string[];
  support_command_tags: string[];
  theme_group: string;
  personality_tags: string[];
  limited: boolean;
  height_cm?: number | null;
  bust_cm?: number | null;
  waist_cm?: number | null;
  hip_cm?: number | null;
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

export type SupportCardGroup = {
  label: string;
  count: number;
  items: SupportCard[];
};

export type CharacterDress = {
  id: number | string;
  title?: string | null;
  aliases?: string | null;
  published_at?: string | null;
  published_at_ts: number;
  published_year?: string | null;
  limited: boolean;
  event_bonus: boolean;
  talents: Record<string, number | null | undefined>;
  aptitudes: Record<string, string | null | undefined>;
  aptitude_scores: Record<string, number | null | undefined>;
};

export type TimelineGroup = {
  label: string;
  items: CharacterDress[];
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

export type GraphNode = {
  slug: string;
  name: string;
  x: number;
  y: number;
  size: number;
  role: string;
  theme: Theme | Relation["theme"];
};

export type GraphEdge = {
  source: string;
  target: string;
  kind: string;
};

export type RelationGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
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
  personality_tags: string[];
  theme_group: string;
  persona_line: string;
  distance_profile: Record<string, string | null | undefined>;
  style_profile: Record<string, string | null | undefined>;
  filters: CharacterFilters;
};

export type CharacterDetail = CharacterSummary & {
  description: string;
  profile_sections: ProfileSection[];
  support_cards: SupportCard[];
  support_groups: {
    by_command: SupportCardGroup[];
    by_rarity: SupportCardGroup[];
  };
  character_cards: CharacterDress[];
  timeline_groups: TimelineGroup[];
  relations: Relation[];
  relation_graph: RelationGraph;
  similar_characters: CharacterSummary[];
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

export type NumericRange = {
  min: number | null;
  max: number | null;
};

export type FilterMeta = {
  theme_groups: string[];
  personality_tags: string[];
  distance_tags: string[];
  style_tags: string[];
  support_command_tags: string[];
  birthday_months: number[];
  numeric_ranges: Record<string, NumericRange>;
};

export type Manifest = {
  generated_at_utc?: string | null;
  raw_updated_at_utc?: string | null;
  counts: SiteStats;
  filter_meta: FilterMeta;
  ranking_keys: string[];
  derived_files: Record<string, string>;
  source_mode: string;
  stale: boolean;
};

export type RankingMeta = {
  key: string;
  label: string;
  description: string;
  direction: "asc" | "desc";
  unit?: string;
  category: string;
};

export type RankingItem = {
  rank: number;
  slug: string;
  name_zh?: string | null;
  name_ja?: string | null;
  name_en?: string | null;
  value: number | string;
  chara_img?: string | null;
  theme_group?: string;
  personality_tags?: string[];
};

export type QualityIssue = {
  slug: string;
  name: string;
  severity: number;
  issues: string[];
};

export type QualitySummary = {
  missing_name_zh_count: number;
  duplicate_name_zh_group_count: number;
  image_missing_count: number;
  image_invalid_count: number;
  description_missing_count: number;
  sparse_content_count: number;
  issue_character_count: number;
};

export type QualityReport = {
  generated_at_utc?: string | null;
  raw_updated_at_utc?: string | null;
  summary: QualitySummary;
  duplicate_name_zh_groups: Array<{ name_zh: string; slugs: string[] }>;
  issues: QualityIssue[];
  stale_prompt: {
    title: string;
    message: string;
    raw_updated_at_utc?: string | null;
    generated_at_utc?: string | null;
    recent_updates: Array<{
      slug: string;
      name_zh?: string | null;
      name_ja?: string | null;
      fetched_at_utc?: string | null;
    }>;
  } | null;
};

export type OverviewResponse = {
  ok: true;
  overview: {
    featured: CharacterSummary[];
    latest_outfits: CharacterSummary[];
    ranking_previews: Record<string, RankingItem[]>;
  };
  stats: SiteStats;
  filters: FilterMeta;
  manifest: Manifest;
  updated_at_utc?: string | null;
};

export type CharactersResponse = {
  ok: true;
  items: CharacterSummary[];
  total: number;
  limit: number;
  offset: number;
  query: string;
  applied_filters: Record<string, string>;
};

export type CharacterResponse = {
  ok: true;
  item: CharacterDetail;
};

export type RankingsResponse = {
  ok: true;
  meta: RankingMeta[];
  rankings: Record<string, RankingItem[]>;
  manifest: Manifest;
};

export type CompareResponse = {
  ok: true;
  items: CharacterDetail[];
};

export type GlobalRelationGraphResponse = {
  ok: true;
  graph: {
    nodes: Array<{
      slug: string;
      name: string;
      theme: Theme;
      theme_group: string;
    }>;
    edges: GraphEdge[];
  };
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
  retried_from_job_id?: string | null;
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
  manifest: Manifest;
  quality_summary: QualitySummary;
  diff_prompt: QualityReport["stale_prompt"];
  actions: string[];
  jobs: Job[];
  failed_jobs: Job[];
};

export type AdminQualityResponse = {
  ok: true;
  report: QualityReport;
  failed_jobs: Job[];
  manifest: Manifest;
};
