// ProductionDeskPanel — the Production Desk's main panel within EpisodeRoom.
// Renders BudgetBar, Convene button, ShotTimeline, and CostPanel.
// asr-0ei.3 + asr-0ei.7, TRD §6.5–§6.6.
import { AlertCircle, Clapperboard, Film, Loader2, Scissors } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useConveneProductionDesk,
  useProduce,
  useFinalize,
} from '@/api/showrunner/hooks';
import { BudgetBar } from '@/components/showrunner/BudgetBar';
import { ShotTimeline } from '@/components/showrunner/ShotTimeline';
import { CostPanel } from '@/components/showrunner/CostPanel';

// ── Empty state (no episode) ──────────────────────────────────────────────────

function NoEpisodeState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
      <Clapperboard className="h-12 w-12 text-[var(--muted-foreground)]" />
      <div className="space-y-1">
        <h2 className="text-base font-semibold text-[var(--foreground)]">Production Desk</h2>
        <p className="max-w-xs text-sm text-[var(--muted-foreground)]">
          No episode in production yet.
        </p>
      </div>
    </div>
  );
}

// ── Convene button section ────────────────────────────────────────────────────

function ConveneSection({ episodeId }: { episodeId: string }) {
  const convene = useConveneProductionDesk(episodeId);
  const produce = useProduce(episodeId);
  const finalize = useFinalize(episodeId);

  function handleConvene() {
    convene.mutate({});
  }

  const errored = [convene, produce, finalize].find((m) => m.isError);
  const erroredVerb =
    convene.isError ? 'convene' : produce.isError ? 'produce' : 'finalize';

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={handleConvene}
          disabled={convene.isPending}
          size='sm'
          className='flex items-center gap-1.5'
        >
          {convene.isPending ? (
            <>
              <Loader2 className='h-3 w-3 animate-spin' />
              Convening…
            </>
          ) : (
            <>
              <Clapperboard className='h-3 w-3' />
              Convene Production Desk
            </>
          )}
        </Button>

        <Button
          onClick={() => produce.mutate()}
          disabled={produce.isPending}
          size='sm'
          variant='secondary'
          className='flex items-center gap-1.5'
        >
          {produce.isPending ? (
            <>
              <Loader2 className='h-3 w-3 animate-spin' />
              Producing…
            </>
          ) : (
            <>
              <Film className='h-3 w-3' />
              Produce
            </>
          )}
        </Button>

        <Button
          onClick={() => finalize.mutate()}
          disabled={finalize.isPending}
          size='sm'
          variant='outline'
          className='flex items-center gap-1.5'
        >
          {finalize.isPending ? (
            <>
              <Loader2 className='h-3 w-3 animate-spin' />
              Finalizing…
            </>
          ) : (
            <>
              <Scissors className='h-3 w-3' />
              Finalize
            </>
          )}
        </Button>
      </div>

      {errored && (
        <div className='flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400'>
          <AlertCircle className='h-4 w-4 shrink-0' />
          <span>
            {errored.error instanceof Error
              ? errored.error.message
              : `Failed to ${erroredVerb} — please retry.`}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export interface ProductionDeskPanelProps {
  episodeId?: string;
  active: boolean;
}

export function ProductionDeskPanel({ episodeId, active: _active }: ProductionDeskPanelProps) {
  if (!episodeId) {
    return <NoEpisodeState />;
  }

  // `active` is received and stored in _active to signal intent for live-
  // polling callers. Child components (BudgetBar, ShotTimeline, CostPanel)
  // each call their own hooks with live=true and manage their own polling;
  // no additional gating is needed here beyond what the children do.

  return (
    <div className='flex flex-col gap-5 p-4'>
      {/* Budget meter at the top of the panel */}
      <BudgetBar episodeId={episodeId} />

      {/* Convene action */}
      <ConveneSection episodeId={episodeId} />

      {/* Shot timeline + production desk contributions */}
      <ShotTimeline episodeId={episodeId} />

      {/* Cost rollup + invocations + pre-flight estimate */}
      <CostPanel episodeId={episodeId} />
    </div>
  );
}
