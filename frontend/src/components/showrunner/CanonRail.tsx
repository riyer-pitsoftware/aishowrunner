// CanonRail — compact left rail displaying series canon state.
// Sections: Characters, Facts, Threads (open / resolved). (asr-0ei.2)
import { BookOpen, User, FileText, GitBranch } from 'lucide-react';
import { useCanon } from '@/api/showrunner/hooks';

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Pull a human-readable label from an opaque record using known field heuristics. */
function recordLabel(record: Record<string, unknown>): string {
  // Try common label fields in priority order
  for (const key of ['name', 'title', 'text', 'label', 'id']) {
    const v = record[key];
    if (typeof v === 'string' && v.trim()) return v.trim();
    if (typeof v === 'number') return String(v);
  }
  // Last resort: first string value found
  for (const v of Object.values(record)) {
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return '(unnamed)';
}

// ── Section components ───────────────────────────────────────────────────────

function SectionHeader({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-1.5">
      <Icon className="h-3.5 w-3.5 text-[var(--muted-foreground)] shrink-0" />
      <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
        {label}
      </span>
    </div>
  );
}

function EntryList({ items }: { items: Array<Record<string, unknown>> }) {
  if (items.length === 0) {
    return <p className="text-[10px] text-[var(--muted-foreground)] italic pl-1">None yet</p>;
  }
  return (
    <ul className="space-y-0.5">
      {items.map((item, i) => (
        <li
          key={i}
          className="truncate rounded px-1.5 py-0.5 text-xs text-[var(--foreground)] hover:bg-[var(--accent)] transition-colors"
          title={recordLabel(item)}
        >
          {recordLabel(item)}
        </li>
      ))}
    </ul>
  );
}

// ── CanonRail ─────────────────────────────────────────────────────────────────

interface CanonRailProps {
  seriesId: string;
}

export function CanonRail({ seriesId }: CanonRailProps) {
  const { data: canon, isLoading, isError } = useCanon(seriesId);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-3 text-xs text-[var(--muted-foreground)]">
        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
        Loading canon…
      </div>
    );
  }

  if (isError || !canon) {
    return (
      <p className="p-3 text-xs text-[var(--muted-foreground)]">
        Could not load canon. Retry later.
      </p>
    );
  }

  const openThreads = canon.threads.open ?? [];
  const resolvedThreads = canon.threads.resolved ?? [];

  return (
    <div className="space-y-4 p-1">
      {/* Header with applied count */}
      <div className="flex items-center gap-2">
        <BookOpen className="h-4 w-4 text-[var(--muted-foreground)]" />
        <span className="text-sm font-semibold text-[var(--foreground)]">Canon</span>
        {canon.applied > 0 && (
          <span className="ml-auto rounded-full bg-[var(--accent)] px-1.5 py-0.5 text-[10px] text-[var(--muted-foreground)]">
            {canon.applied} applied
          </span>
        )}
      </div>

      {/* Characters */}
      <section>
        <SectionHeader icon={User} label="Characters" />
        <EntryList items={canon.characters} />
      </section>

      {/* Facts */}
      <section>
        <SectionHeader icon={FileText} label="Facts" />
        <EntryList items={canon.facts} />
      </section>

      {/* Threads */}
      <section>
        <SectionHeader icon={GitBranch} label="Threads" />
        {openThreads.length === 0 && resolvedThreads.length === 0 ? (
          <p className="text-[10px] text-[var(--muted-foreground)] italic pl-1">None yet</p>
        ) : (
          <div className="space-y-2">
            {openThreads.length > 0 && (
              <div>
                <p className="mb-0.5 pl-1 text-[10px] text-[var(--muted-foreground)]">Open</p>
                <EntryList items={openThreads} />
              </div>
            )}
            {resolvedThreads.length > 0 && (
              <div>
                <p className="mb-0.5 pl-1 text-[10px] text-[var(--muted-foreground)] line-through">
                  Resolved
                </p>
                <ul className="space-y-0.5 opacity-50">
                  {resolvedThreads.map((item, i) => (
                    <li
                      key={i}
                      className="truncate rounded px-1.5 py-0.5 text-xs text-[var(--muted-foreground)] line-through"
                      title={recordLabel(item)}
                    >
                      {recordLabel(item)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
