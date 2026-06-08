// ShotTimeline — production desk contributions + live shot strip (asr-0ei.3,
// TRD §6.5). Shots + artifacts are Sprint 6 media-production deliverables; this
// component renders an ordered, live-polled strip of shot cards with per-shot
// thumbnails, status chips, and regenerate controls.
import { Film, RefreshCw, Loader2, ImageOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
  useContributions,
  useShots,
  useArtifacts,
  useRegenerateShot,
} from '@/api/showrunner/hooks';
import { stanceVariant, stanceLabel } from '@/components/showrunner/stance';
import type { Contribution, ProductionArtifact, Shot } from '@/api/showrunner/types';

// ── Shot status chip ──────────────────────────────────────────────────────────

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';

function shotStatusVariant(status: string): BadgeVariant {
  switch (status) {
    case 'ready':
      return 'success';
    case 'generating':
      return 'warning';
    case 'stale':
      return 'warning';
    case 'approved':
      return 'default';
    case 'failed':
    case 'error':
      return 'destructive';
    case 'pending':
    default:
      return 'secondary';
  }
}

// ── Shot thumbnail ────────────────────────────────────────────────────────────

function ShotThumbnail({ artifact }: { artifact: ProductionArtifact | undefined }) {
  const isVideo =
    artifact?.kind === 'video' || (artifact?.mime_type?.startsWith('video/') ?? false);
  const isImage =
    artifact?.kind === 'image' || (artifact?.mime_type?.startsWith('image/') ?? false);

  return (
    <div
      className="relative w-full overflow-hidden rounded border border-[var(--border)] bg-black"
      style={{ aspectRatio: '9 / 16' }}
    >
      {artifact?.url && isVideo ? (
        <video src={artifact.url} controls className="h-full w-full object-cover" />
      ) : artifact?.url && isImage ? (
        <img
          src={artifact.url}
          alt="Shot preview"
          className="h-full w-full object-cover"
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-[var(--muted-foreground)]">
          <ImageOff className="h-5 w-5" />
        </div>
      )}
    </div>
  );
}

// ── Shot card ─────────────────────────────────────────────────────────────────

function ShotCard({
  shot,
  artifact,
  onRegenerate,
  regenerating,
}: {
  shot: Shot;
  artifact: ProductionArtifact | undefined;
  onRegenerate: (shotId: string) => void;
  regenerating: boolean;
}) {
  const generating = shot.status === 'generating';

  return (
    <div className="flex w-[120px] shrink-0 flex-col gap-1.5 rounded-md border border-[var(--border)] bg-[var(--muted)] p-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-[var(--muted-foreground)] tabular-nums">
          #{shot.index + 1}
        </span>
        <Badge
          variant={shotStatusVariant(shot.status)}
          className={cn('text-[9px] px-1.5 py-0', generating && 'animate-pulse')}
        >
          {shot.status}
        </Badge>
      </div>

      <ShotThumbnail artifact={artifact} />

      {shot.description && (
        <p
          className="text-[10px] leading-tight text-[var(--foreground)] line-clamp-2"
          title={shot.description}
        >
          {shot.description}
        </p>
      )}

      <Button
        size="sm"
        variant="outline"
        disabled={regenerating || generating}
        onClick={() => onRegenerate(shot.id)}
        className="mt-auto h-6 w-full gap-1 px-1 text-[10px]"
      >
        {regenerating || generating ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <>
            <RefreshCw className="h-3 w-3" />
            Regenerate
          </>
        )}
      </Button>
    </div>
  );
}

// ── Timeline strip ────────────────────────────────────────────────────────────

function TimelineStrip({ episodeId }: { episodeId: string }) {
  const { data: shots } = useShots(episodeId, true);
  const { data: artifacts } = useArtifacts(episodeId, true);
  const regenerate = useRegenerateShot(episodeId);

  const artifactById = new Map<string, ProductionArtifact>(
    (artifacts ?? []).map((a) => [a.id, a]),
  );

  const ordered = [...(shots ?? [])].sort((a, b) => a.index - b.index);

  if (ordered.length === 0) {
    return (
      <div className="rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2">
        <div className="flex flex-col items-center gap-1.5 py-3 text-center">
          <Film className="h-5 w-5 text-[var(--muted-foreground)]" />
          <p className="text-xs text-[var(--muted-foreground)]">
            No shots planned yet — produce to generate.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {ordered.map((shot) => (
          <ShotCard
            key={shot.id}
            shot={shot}
            artifact={shot.artifact_id ? artifactById.get(shot.artifact_id) : undefined}
            onRegenerate={(shotId) => regenerate.mutate(shotId)}
            regenerating={regenerate.isPending && regenerate.variables === shot.id}
          />
        ))}
      </div>
    </div>
  );
}

// ── Contribution card ─────────────────────────────────────────────────────────

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
        {/* Live shot strip */}
        <TimelineStrip episodeId={episodeId} />

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
