// Showrunner React Query hooks (Sprint 5). Same conventions as api/hooks/useConfig.ts.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  Budget,
  Canon,
  Contribution,
  CostRollup,
  Disagreement,
  Episode,
  Estimate,
  EstimateRequest,
  GateName,
  GreenlightRequest,
  GreenlightResult,
  Invocation,
  RoomAccepted,
  Series,
  SeriesCreate,
} from './types';

const LIVE = 4000; // poll interval while a room job runs

// ── Series + canon ───────────────────────────────────────────────────────────
export function useSeriesList() {
  return useQuery({ queryKey: ['sr', 'series'], queryFn: () => api.get<Series[]>('/series') });
}

export function useSeries(seriesId?: string) {
  return useQuery({
    queryKey: ['sr', 'series', seriesId],
    queryFn: () => api.get<Series>(`/series/${seriesId}`),
    enabled: !!seriesId,
  });
}

export function useCreateSeries() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SeriesCreate) => api.post<Series>('/series', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sr', 'series'] }),
  });
}

export function useCanon(seriesId?: string) {
  return useQuery({
    queryKey: ['sr', 'canon', seriesId],
    queryFn: () => api.get<Canon>(`/series/${seriesId}/canon`),
    enabled: !!seriesId,
  });
}

// ── Episode + rooms ──────────────────────────────────────────────────────────
export function useEpisode(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'episode', episodeId],
    queryFn: () => api.get<Episode>(`/episodes/${episodeId}`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useContributions(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'contributions', episodeId],
    queryFn: () => api.get<Contribution[]>(`/episodes/${episodeId}/contributions`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useDisagreements(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'disagreements', episodeId],
    queryFn: () => api.get<Disagreement[]>(`/episodes/${episodeId}/disagreements`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useConveneStoryRoom(seriesId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title?: string; premise?: string; task?: string }) =>
      api.post<RoomAccepted>(`/series/${seriesId}/story-room`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sr'] }),
  });
}

export function useConveneProductionDesk(episodeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { task?: string }) =>
      api.post<RoomAccepted>(`/episodes/${episodeId}/production-desk`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sr', 'contributions', episodeId] }),
  });
}

// ── Greenlight gates ─────────────────────────────────────────────────────────
export function usePostGreenlight(episodeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ gate, body }: { gate: GateName; body: GreenlightRequest }) =>
      api.post<GreenlightResult>(`/episodes/${episodeId}/greenlights/${gate}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sr'] }),
  });
}

// ── Cost + budget ────────────────────────────────────────────────────────────
export function useEpisodeBudget(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'budget', 'episode', episodeId],
    queryFn: () => api.get<Budget>(`/episodes/${episodeId}/budget`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useSeriesBudget(seriesId?: string) {
  return useQuery({
    queryKey: ['sr', 'budget', 'series', seriesId],
    queryFn: () => api.get<Budget>(`/series/${seriesId}/budget`),
    enabled: !!seriesId,
  });
}

export function useEpisodeCost(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'cost', episodeId],
    queryFn: () => api.get<CostRollup>(`/episodes/${episodeId}/cost`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useInvocations(episodeId?: string, live = false) {
  return useQuery({
    queryKey: ['sr', 'invocations', episodeId],
    queryFn: () => api.get<Invocation[]>(`/episodes/${episodeId}/invocations`),
    enabled: !!episodeId,
    refetchInterval: live ? LIVE : false,
  });
}

export function useEstimate(episodeId: string) {
  return useMutation({
    mutationFn: (body: EstimateRequest) =>
      api.post<Estimate>(`/episodes/${episodeId}/estimate`, body),
  });
}
