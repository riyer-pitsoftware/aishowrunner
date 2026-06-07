// Showrunner API types (Sprint 5). Mirror backend schemas:
// api/schemas/series.py, api/schemas/cost.py, api/routes/rooms.py.

export type Stance = 'support' | 'concern' | 'block' | 'unknown';

export interface Series {
  id: string;
  title: string;
  premise?: string | null;
  era?: string | null;
  creative_rules?: Record<string, unknown> | null;
  status: string;
  created_at?: string | null;
}

export interface SeriesCreate {
  title: string;
  premise?: string;
  era?: string;
  creative_rules?: Record<string, unknown>;
}

export interface Canon {
  series_id: string;
  facts: Array<Record<string, unknown>>;
  characters: Array<Record<string, unknown>>;
  relationships: Array<Record<string, unknown>>;
  threads: { open?: Array<Record<string, unknown>>; resolved?: Array<Record<string, unknown>> };
  applied: number;
}

// EpisodeService.describe()
export interface Episode {
  id: string;
  series_id: string;
  number: number | null;
  title: string | null;
  status: string;
  active_room: string | null;
  next_required_gate: string | null;
}

// GET /episodes/{id}/contributions
export interface Contribution {
  id: string;
  room: string;
  skill_name: string;
  stance: Stance;
  summary: string | null;
  recommendations: unknown;
  risks: unknown;
  fields: Record<string, unknown> | null;
  decision_id: string | null;
}

// GET /episodes/{id}/disagreements
export interface Disagreement {
  id: string;
  axis: string;
  stances: Record<string, string>;
  detail: string | null;
  resolved: boolean;
  decision_id: string | null;
}

// GET /{series|episodes}/{id}/budget
export interface Budget {
  scope: 'series' | 'episode';
  scope_id: string;
  limit_usd: number;
  soft_pct: number;
  hard_behavior: string;
  spent_usd: number;
  reserved_usd: number;
  available_usd: number;
}

// GET /episodes/{id}/cost
export interface CostRollup {
  episode_id: string;
  skill_cost_usd: number;
  skill_calls: number;
  media_cost_usd: number;
  media_jobs: number;
  total_usd: number;
  confidence: string;
}

// POST /episodes/{id}/estimate
export interface EstimateRequest {
  num_skill_calls?: number;
  num_images?: number;
  num_video_seconds?: number;
  num_tts_chars?: number;
  skill_model?: string;
}

export interface Estimate {
  estimate_usd: number;
  outcome: 'allow' | 'warn' | 'block';
  projected_usd: number;
  limit_usd: number;
}

// GET /episodes/{id}/invocations
export interface Invocation {
  id: string;
  skill_name: string;
  model: string | null;
  provider: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  cost_confidence: string | null;
  status: string | null;
  room: string | null;
  gate: string | null;
}

export type GateName = 'branch' | 'episode' | 'final';
export type Verdict = 'approved' | 'defer' | 'reduce' | 'kill';

export interface GreenlightRequest {
  verdict: string;
  actor?: string;
  rationale?: string;
  decision_id?: string;
  chosen_option_id?: string;
  estimate_usd?: number;
}

export interface GreenlightResult {
  gate_id: string;
  gate: GateName;
  verdict: string;
  status: string;
}

export interface RoomAccepted {
  episode_id: string;
  status?: string;
  accepted: boolean;
}

// The three visible rooms (PRD §6).
export type RoomKey = 'story_room' | 'production_desk' | 'greenlight';
