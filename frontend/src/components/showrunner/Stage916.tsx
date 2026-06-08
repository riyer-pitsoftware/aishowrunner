// Persistent 9:16 vertical preview stage (asr-0ei.5, PRD §6 / TRD §6.6).
// Always-visible right rail across all three rooms. Shows the assembling vertical
// cut; once a final `episode` artifact lands (Sprint 6 media production) it shows
// the rendered video, or — when ffmpeg is absent — a "Final cut ready" manifest
// state. Before any media exists it shows a status placeholder.
import { CheckCircle2, Film, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useArtifacts } from '@/api/showrunner/hooks';
import type { Episode, ProductionArtifact } from '@/api/showrunner/types';

interface Stage916Props {
  episode?: Episode;
  posterUrl?: string | null;
  videoUrl?: string | null;
  className?: string;
}

const PRODUCING_STATES = new Set(['producing', 'production_desk']);

// Latest (highest version) final episode artifact, if any.
function pickFinalArtifact(
  artifacts: ProductionArtifact[] | undefined,
): ProductionArtifact | undefined {
  return (artifacts ?? [])
    .filter((a) => a.kind === 'episode')
    .reduce<ProductionArtifact | undefined>((latest, a) => {
      if (!latest || a.version > latest.version) return a;
      return latest;
    }, undefined);
}

function shotCountOf(artifact: ProductionArtifact): number | null {
  const raw = artifact.payload?.shot_count ?? artifact.payload?.shots;
  if (typeof raw === 'number') return raw;
  if (Array.isArray(raw)) return raw.length;
  return null;
}

export function Stage916({ episode, posterUrl, videoUrl, className }: Stage916Props) {
  const status = episode?.status ?? 'draft';
  const producing = PRODUCING_STATES.has(status);

  const { data: artifacts } = useArtifacts(episode?.id, true);
  const final = pickFinalArtifact(artifacts);

  const finalIsVideo =
    final != null &&
    final.url != null &&
    (final.mime_type?.startsWith('video/') ?? false);
  const finalIsManifest = final != null && !finalIsVideo;

  // Explicit videoUrl prop wins, then a rendered final cut.
  const effectiveVideoUrl = videoUrl ?? (finalIsVideo ? final?.url : null);
  const shotCount = finalIsManifest && final ? shotCountOf(final) : null;

  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      <div
        className="relative w-full max-w-[260px] overflow-hidden rounded-xl border border-[var(--border)] bg-black shadow-lg"
        style={{ aspectRatio: '9 / 16' }}
      >
        {effectiveVideoUrl ? (
          <video
            src={effectiveVideoUrl}
            poster={posterUrl ?? undefined}
            controls
            className="h-full w-full object-cover"
          />
        ) : finalIsManifest ? (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 px-4 text-center text-zinc-300">
            <CheckCircle2 className="h-7 w-7 text-green-400" />
            <span className="text-xs font-medium">Final cut ready</span>
            {shotCount != null && (
              <span className="text-[11px] text-zinc-400">
                {shotCount} shot{shotCount !== 1 ? 's' : ''}
              </span>
            )}
            {final?.url && (
              <a
                href={final.url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-[var(--primary)] underline underline-offset-2"
              >
                Open manifest
              </a>
            )}
          </div>
        ) : posterUrl ? (
          <img src={posterUrl} alt="Episode preview" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-zinc-500">
            {producing ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Film className="h-6 w-6" />
            )}
            <span className="px-4 text-center text-xs">
              {producing ? 'Assembling 9:16 cut…' : 'No preview yet'}
            </span>
          </div>
        )}
        <div className="pointer-events-none absolute right-1.5 top-1.5 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white/80">
          9:16
        </div>
      </div>
      <div className="text-center">
        <div className="text-xs font-medium text-[var(--foreground)]">
          {episode?.title ?? 'Untitled episode'}
        </div>
        <div className="text-[11px] text-[var(--muted-foreground)]">
          {episode?.number != null ? `Ep ${episode.number} · ` : ''}
          {status.replace(/_/g, ' ')}
        </div>
      </div>
    </div>
  );
}
