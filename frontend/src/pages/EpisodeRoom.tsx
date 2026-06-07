// Episode Room — the three visible rooms (PRD §6, TRD §6.6). One room is "active"
// (expanded), the others stay "compact" (a clickable summary strip). A persistent
// 9:16 stage rides along the right rail across all rooms. asr-0ei.1 + .5.
import { useEffect, useMemo, useState } from 'react';
import { ChevronRight, Clapperboard, Drama, Gavel } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigation } from '@/stores/navigation';
import { useEpisode } from '@/api/showrunner/hooks';
import { Stage916 } from '@/components/showrunner/Stage916';
import { StoryRoomPanel } from '@/components/showrunner/StoryRoomPanel';
import { ProductionDeskPanel } from '@/components/showrunner/ProductionDeskPanel';
import { GreenlightPanel } from '@/components/showrunner/GreenlightPanel';
import type { RoomKey } from '@/api/showrunner/types';

const ROOMS: Array<{ key: RoomKey; label: string; blurb: string; icon: React.ElementType }> = [
  { key: 'story_room', label: 'Story Room', blurb: 'Canon, branches, beats', icon: Drama },
  {
    key: 'production_desk',
    label: 'Production Desk',
    blurb: 'Shots, assets, budget',
    icon: Clapperboard,
  },
  { key: 'greenlight', label: 'Greenlight Council', blurb: 'Approvals & dissent', icon: Gavel },
];

// Map episode lifecycle state → the room that should be in focus.
function roomForStatus(status?: string | null): RoomKey {
  switch (status) {
    case 'production_desk':
    case 'producing':
      return 'production_desk';
    case 'branch_greenlight':
    case 'episode_greenlight':
    case 'final_greenlight':
    case 'canon_commit':
      return 'greenlight';
    default:
      return 'story_room';
  }
}

export function EpisodeRoom({
  seriesId: seriesIdProp,
  episodeId: episodeIdProp,
}: {
  seriesId?: string;
  episodeId?: string;
}) {
  const { currentPath } = useNavigation();
  // Path form: /room?series=<id>&episode=<id>
  const params = useMemo(() => {
    const q = currentPath.indexOf('?');
    return new URLSearchParams(q === -1 ? '' : currentPath.slice(q + 1));
  }, [currentPath]);
  const seriesId = seriesIdProp ?? params.get('series') ?? undefined;
  const episodeId = episodeIdProp ?? params.get('episode') ?? undefined;

  const { data: episode } = useEpisode(episodeId, true);
  const [active, setActive] = useState<RoomKey>('story_room');
  const [pinned, setPinned] = useState(false);

  // Follow the episode lifecycle until the user manually pins a room.
  useEffect(() => {
    if (!pinned) setActive(roomForStatus(episode?.status));
  }, [episode?.status, pinned]);

  const focus = (key: RoomKey) => {
    setPinned(true);
    setActive(key);
  };

  if (!seriesId) {
    return (
      <div className="p-8 text-sm text-[var(--muted-foreground)]">
        No series selected. Open a series to convene its rooms.
      </div>
    );
  }

  return (
    <div className="flex h-full gap-4 p-4">
      {/* Room column */}
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        {ROOMS.map((room) => {
          const isActive = room.key === active;
          const Icon = room.icon;
          return (
            <section
              key={room.key}
              className={cn(
                'rounded-lg border border-[var(--border)] bg-[var(--card)] transition-all',
                isActive ? 'flex-1 overflow-hidden' : 'shrink-0',
              )}
            >
              {/* Header strip — always clickable to focus */}
              <button
                onClick={() => focus(room.key)}
                className={cn(
                  'flex w-full items-center gap-3 px-4 py-3 text-left',
                  isActive
                    ? 'border-b border-[var(--border)]'
                    : 'hover:bg-[var(--accent)]',
                )}
              >
                <Icon className="h-5 w-5 text-[var(--muted-foreground)]" />
                <div className="min-w-0">
                  <div className="text-sm font-semibold">{room.label}</div>
                  <div className="truncate text-xs text-[var(--muted-foreground)]">
                    {room.blurb}
                  </div>
                </div>
                {!isActive && (
                  <ChevronRight className="ml-auto h-4 w-4 text-[var(--muted-foreground)]" />
                )}
              </button>

              {/* Active room body */}
              {isActive && (
                <div className="h-full overflow-y-auto p-4">
                  {room.key === 'story_room' && (
                    <StoryRoomPanel seriesId={seriesId} episodeId={episodeId} active />
                  )}
                  {room.key === 'production_desk' && (
                    <ProductionDeskPanel episodeId={episodeId} active />
                  )}
                  {room.key === 'greenlight' && (
                    <GreenlightPanel episodeId={episodeId} active />
                  )}
                </div>
              )}
            </section>
          );
        })}
      </div>

      {/* Persistent 9:16 stage rail */}
      <aside className="hidden w-[280px] shrink-0 flex-col gap-4 lg:flex">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
          <Stage916 episode={episode} />
        </div>
      </aside>
    </div>
  );
}
