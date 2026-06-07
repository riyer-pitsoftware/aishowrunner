// StoryRoomPanel — the Story Room's main panel within EpisodeRoom.
// No episodeId: shows Convene button → calls useConveneStoryRoom → navigates.
// Has episodeId: two-column layout (CanonRail | contribution feed).
// Contribution feed: useContributions filtered to room === 'story_room'. (asr-0ei.2 + asr-0ei.6)
import { AlertCircle, Drama, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useConveneStoryRoom, useContributions } from '@/api/showrunner/hooks';
import { useNavigation } from '@/stores/navigation';
import { CanonRail } from '@/components/showrunner/CanonRail';
import { ContributionCard } from '@/components/showrunner/ContributionCard';
import { BranchProposals } from '@/components/showrunner/BranchProposals';
import type { RoomAccepted } from '@/api/showrunner/types';

// ── ConveneView (no episodeId yet) ───────────────────────────────────────────

interface ConveneViewProps {
  seriesId: string;
}

function ConveneView({ seriesId }: ConveneViewProps) {
  const { navigate } = useNavigation();
  const convene = useConveneStoryRoom(seriesId);

  function handleConvene() {
    convene.mutate(
      {},
      {
        onSuccess: (result: RoomAccepted) => {
          navigate(`/room?series=${seriesId}&episode=${result.episode_id}`);
        },
      },
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
      <Drama className="h-12 w-12 text-[var(--muted-foreground)]" />

      <div className="space-y-1">
        <h2 className="text-base font-semibold text-[var(--foreground)]">Story Room</h2>
        <p className="max-w-xs text-sm text-[var(--muted-foreground)]">
          Convene the room to gather canon analysis, branch proposals, and story beats from your
          skill ensemble.
        </p>
      </div>

      {convene.isError && (
        <div className="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>
            {convene.error instanceof Error
              ? convene.error.message
              : 'Failed to convene — please retry.'}
          </span>
        </div>
      )}

      <Button onClick={handleConvene} disabled={convene.isPending} size="lg">
        {convene.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Convening…
          </>
        ) : (
          'Convene Story Room'
        )}
      </Button>
    </div>
  );
}

// ── FeedView (episodeId present) ─────────────────────────────────────────────

interface FeedViewProps {
  seriesId: string;
  episodeId: string;
  active: boolean;
}

function FeedView({ seriesId, episodeId, active }: FeedViewProps) {
  const { data: contributions, isLoading, isError } = useContributions(episodeId, active);

  const storyRoomContribs = (contributions ?? []).filter((c) => c.room === 'story_room');

  return (
    <div className="flex h-full min-h-0 gap-4">
      {/* Left rail — canon state */}
      <aside className="w-48 shrink-0 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--card)] p-2">
        <CanonRail seriesId={seriesId} />
      </aside>

      {/* Right — main feed */}
      <div className="flex min-w-0 flex-1 flex-col gap-3 overflow-y-auto">
        {/* Branch proposals above the feed */}
        <BranchProposals contributions={storyRoomContribs} />

        {/* Contribution feed */}
        {isLoading && (
          <div className="flex items-center gap-2 py-6 text-sm text-[var(--muted-foreground)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading contributions…
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            Could not load contributions. Check your connection and retry.
          </div>
        )}

        {!isLoading && !isError && storyRoomContribs.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <Drama className="h-8 w-8 text-[var(--muted-foreground)]" />
            <p className="text-sm text-[var(--muted-foreground)]">
              No contributions yet — convene the room.
            </p>
          </div>
        )}

        {storyRoomContribs.map((contrib) => (
          <ContributionCard key={contrib.id} contribution={contrib} />
        ))}
      </div>
    </div>
  );
}

// ── StoryRoomPanel ────────────────────────────────────────────────────────────

interface StoryRoomPanelProps {
  seriesId: string;
  episodeId?: string;
  active: boolean;
}

export function StoryRoomPanel({ seriesId, episodeId, active }: StoryRoomPanelProps) {
  if (!episodeId) {
    return <ConveneView seriesId={seriesId} />;
  }

  return <FeedView seriesId={seriesId} episodeId={episodeId} active={active} />;
}
