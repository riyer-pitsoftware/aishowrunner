// ShotTimeline — production desk contributions + forward-compatible shot strip
// (asr-0ei.3, TRD §6.5). Shot/asset data is a Sprint 6 deliverable; this
// component renders an empty timeline strip now and is wired for live data later.
import { Film } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { useContributions } from '@/api/showrunner/hooks';
import { stanceVariant, stanceLabel } from '@/components/showrunner/stance';

// ── Shot state chip types ─────────────────────────────────────────────────────
// TODO (Sprint 6): Replace empty `shots` array with real data from the media-
// production endpoint (e.g. GET /episodes/{id}/shots) once that route exists.
// ShotState and ShotChip are already wired — just populate the array.

type ShotState = 'planned' | 'generating' | 'ready' | 'stale';

interface Shot {
  id: string;
  label: string;
  state: ShotState;
}

function shotStateVariant(
  state: ShotState,
): 'secondary' | 'warning' | 'success' | 'outline' {
  switch (state) {
    case 'planned':
      return 'secondary';
    case 'generating':
      return 'warning';
    case 'ready':
      return 'success';
    case 'stale':
      return 'outline';
  }
}

function ShotChip({ shot }: { shot: Shot }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-1 min-w-[64px] px-2 py-1.5 rounded-md border border-[var(--border)] bg-[var(--muted)] text-center',
      )}
    >
      <Badge variant={shotStateVariant(shot.state)} className="text-[9px] px-1.5 py-0">
        {shot.state}
      </Badge>
      <span className="text-[10px] text-[var(--muted-foreground)] truncate max-w-[56px]" title={shot.label}>
        {shot.label}
      </span>
    </div>
  );
}

// ── Timeline strip ────────────────────────────────────────────────────────────

function TimelineStrip({ shots }: { shots: Shot[] }) {
  return (
    <div className="rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2">
      {shots.length === 0 ? (
        <div className="flex flex-col items-center gap-1.5 py-3 text-center">
          <Film className="h-5 w-5 text-[var(--muted-foreground)]" />
          <p className="text-xs text-[var(--muted-foreground)]">
            Shots and assets appear here once production runs.
          </p>
          <p className="text-[10px] text-[var(--muted-foreground)]/60">
            Sprint 6 · media production
          </p>
        </div>
      ) : (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {shots.map((shot) => (
            <ShotChip key={shot.id} shot={shot} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Contribution card ─────────────────────────────────────────────────────────

import type { Contribution } from '@/api/showrunner/types';

function ContributionCard({ contrib }: { contrib: Contribution }) {
  return (
    <div className="rounded-md border border-[var(--border)] bg-[var(--muted)] px-3 py-2 flex items-start gap-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-medium text-[var(--foreground)] truncate">
            {contrib.skill_name}
          </span>
          <Badge variant={stanceVariant(contrib.stance)}>
            {stanceLabel(contrib.stance)}
          </Badge>
        </div>
        {contrib.summary && (
          <p className="mt-1 text-[11px] text-[var(--muted-foreground)] line-clamp-2">
            {contrib.summary}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────

export function ShotTimeline({ episodeId }: { episodeId: string }) {
  const { data: contributions } = useContributions(episodeId, true);

  // TODO (Sprint 6): fetch shots from media endpoint and pass real data here.
  const shots: Shot[] = [];

  const deskContribs = (contributions ?? []).filter(
    (c) => c.room === 'production_desk',
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Film className="h-4 w-4" />
          Shot Timeline
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Forward-compatible shot strip */}
        <TimelineStrip shots={shots} />

        {/* Production desk contributions */}
        {deskContribs.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-wide font-medium text-[var(--muted-foreground)]">
              Production Desk · {deskContribs.length} contribution{deskContribs.length !== 1 ? 's' : ''}
            </p>
            {deskContribs.map((c) => (
              <ContributionCard key={c.id} contrib={c} />
            ))}
          </div>
        )}

        {deskContribs.length === 0 && (
          <p className="text-xs text-[var(--muted-foreground)]">
            No production desk contributions yet.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
