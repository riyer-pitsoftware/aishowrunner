// Persistent 9:16 vertical preview stage (asr-0ei.5, PRD §6 / TRD §6.6).
// Always-visible right rail across all three rooms. Shows the assembling vertical
// cut; before any media exists it shows a status placeholder. Real shot assets
// land here in Sprint 6 (media production).
import { Film, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Episode } from '@/api/showrunner/types';

interface Stage916Props {
  episode?: Episode;
  posterUrl?: string | null;
  videoUrl?: string | null;
  className?: string;
}

const PRODUCING_STATES = new Set(['producing', 'production_desk']);

export function Stage916({ episode, posterUrl, videoUrl, className }: Stage916Props) {
  const status = episode?.status ?? 'draft';
  const producing = PRODUCING_STATES.has(status);

  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      <div
        className="relative w-full max-w-[260px] overflow-hidden rounded-xl border border-[var(--border)] bg-black shadow-lg"
        style={{ aspectRatio: '9 / 16' }}
      >
        {videoUrl ? (
          <video
            src={videoUrl}
            poster={posterUrl ?? undefined}
            controls
            className="h-full w-full object-cover"
          />
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
