// GreenlightPanel — Greenlight Council view (Sprint 5, bead asr-0ei.4).
// Renders episode status + current gate, VerdictControls, council roster
// (contributions filtered to room === 'greenlight'), and DisagreementList.
import { Gavel } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useEpisode, useContributions } from '@/api/showrunner/hooks';
import { stanceVariant, stanceLabel } from '@/components/showrunner/stance';
import { VerdictControls } from '@/components/showrunner/VerdictControls';
import { DisagreementList } from '@/components/showrunner/DisagreementList';
import type { GateName } from '@/api/showrunner/types';

// ── Gate derivation ──────────────────────────────────────────────────────────

const GATE_NAMES: readonly GateName[] = ['branch', 'episode', 'final'];

function toGateName(raw: string | null | undefined): GateName | null {
  if (!raw) return null;
  // next_required_gate may arrive as e.g. 'branch_greenlight' or 'branch' —
  // normalise by extracting the prefix before any '_greenlight' suffix.
  const normalised = raw.replace(/_greenlight$/, '');
  return (GATE_NAMES as readonly string[]).includes(normalised)
    ? (normalised as GateName)
    : null;
}

function gateBadgeLabel(gate: GateName): string {
  switch (gate) {
    case 'branch':
      return 'Branch Gate';
    case 'episode':
      return 'Episode Gate';
    case 'final':
      return 'Final Gate';
  }
}

// ── Council member row ───────────────────────────────────────────────────────

interface CouncilMemberProps {
  skillName: string;
  stance: string;
  summary: string | null;
}

function CouncilMember({ skillName, stance, summary }: CouncilMemberProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="flex items-start gap-3 px-4 py-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-[var(--foreground)]">{skillName}</p>
          {summary && (
            <p className="mt-0.5 text-xs text-[var(--muted-foreground)] line-clamp-2 leading-relaxed">
              {summary}
            </p>
          )}
        </div>
        <Badge variant={stanceVariant(stance)} className="shrink-0">
          {stanceLabel(stance)}
        </Badge>
      </CardContent>
    </Card>
  );
}

// ── GreenlightPanel ──────────────────────────────────────────────────────────

interface GreenlightPanelProps {
  episodeId?: string;
  active: boolean;
}

export function GreenlightPanel({ episodeId, active }: GreenlightPanelProps) {
  // No episode selected
  if (!episodeId) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
        <Gavel className="h-10 w-10 text-[var(--muted-foreground)]" />
        <p className="text-sm text-[var(--muted-foreground)]">No episode awaiting greenlight.</p>
      </div>
    );
  }

  return <GreenlightPanelBody episodeId={episodeId} active={active} />;
}

// Split into a child so the hooks only run when episodeId is defined.
function GreenlightPanelBody({ episodeId, active }: { episodeId: string; active: boolean }) {
  const {
    data: episode,
    isLoading: epLoading,
    isError: epError,
  } = useEpisode(episodeId, active);

  const {
    data: contributions,
    isLoading: contribLoading,
  } = useContributions(episodeId, active);

  const derivedGate = toGateName(episode?.next_required_gate);

  // Council roster = contributions from the greenlight room
  const roster = contributions?.filter((c) => c.room === 'greenlight') ?? [];

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <section className="space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Gavel className="h-4 w-4 text-[var(--muted-foreground)]" />
          <h2 className="text-sm font-semibold text-[var(--foreground)]">Greenlight Council</h2>

          {epLoading && (
            <span className="text-xs text-[var(--muted-foreground)]">Loading…</span>
          )}

          {epError && (
            <span className="text-xs text-[var(--destructive)]">Failed to load episode.</span>
          )}

          {episode && (
            <>
              <Badge variant="outline" className="font-mono text-xs">
                {episode.status}
              </Badge>
              {derivedGate ? (
                <Badge variant="secondary" className="text-xs">
                  {gateBadgeLabel(derivedGate)}
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">
                  No gate pending
                </Badge>
              )}
            </>
          )}
        </div>

        {episode?.title && (
          <p className="text-xs text-[var(--muted-foreground)]">{episode.title}</p>
        )}
      </section>

      {/* ── Verdict controls — only when a gate is pending ── */}
      {derivedGate && (
        <section>
          <VerdictControls episodeId={episodeId} gate={derivedGate} />
        </section>
      )}

      {/* ── Council roster ── */}
      <section className="space-y-2">
        <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
          Council Roster
        </h3>

        {contribLoading && (
          <p className="text-xs text-[var(--muted-foreground)]">Loading contributions…</p>
        )}

        {!contribLoading && roster.length === 0 && (
          <p className="text-xs text-[var(--muted-foreground)]">
            No greenlight contributions recorded yet.
          </p>
        )}

        <div className="space-y-2">
          {roster.map((c) => (
            <CouncilMember
              key={c.id}
              skillName={c.skill_name}
              stance={c.stance}
              summary={c.summary}
            />
          ))}
        </div>
      </section>

      {/* ── Disagreements ── */}
      <DisagreementList episodeId={episodeId} />
    </div>
  );
}
