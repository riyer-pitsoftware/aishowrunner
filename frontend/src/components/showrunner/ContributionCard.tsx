// ContributionCard — progressive disclosure for a single skill contribution.
// Collapsed: skill_name (author), stance badge, summary.
// Expanded: recommendations, risks, additional fields. (asr-0ei.6)
import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { stanceVariant, stanceLabel } from '@/components/showrunner/stance';
import type { Contribution } from '@/api/showrunner/types';

// ── Safe unknown-value renderer ──────────────────────────────────────────────

function renderValue(value: unknown, depth = 0): React.ReactNode {
  if (value === null || value === undefined) return null;

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-[var(--muted-foreground)]">—</span>;
    return (
      <ul className="space-y-0.5 pl-3">
        {value.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-xs text-[var(--foreground)]">
            <span className="mt-0.5 shrink-0 text-[var(--muted-foreground)]">&bull;</span>
            <span>{renderValue(item, depth + 1)}</span>
          </li>
        ))}
      </ul>
    );
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).filter(
      ([, v]) => v !== null && v !== undefined,
    );
    if (entries.length === 0) return null;
    // Avoid deeply nested objects growing unbounded
    if (depth >= 2) return <span className="text-xs text-[var(--muted-foreground)]">{JSON.stringify(value)}</span>;
    return (
      <dl className="space-y-0.5">
        {entries.map(([k, v]) => (
          <div key={k} className="flex gap-1.5 text-xs">
            <dt className="shrink-0 font-medium text-[var(--muted-foreground)] capitalize">
              {k.replace(/_/g, ' ')}:
            </dt>
            <dd className="text-[var(--foreground)]">{renderValue(v, depth + 1)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return <span className="text-xs text-[var(--foreground)]">{String(value)}</span>;
}

// ── ContributionCard ─────────────────────────────────────────────────────────

interface ContributionCardProps {
  contribution: Contribution;
}

export function ContributionCard({ contribution }: ContributionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const { skill_name, stance, summary, recommendations, risks, fields } = contribution;

  // Resolve authorship model from known field paths
  const resolvedModel =
    (typeof fields?.model === 'string' ? fields.model : null) ??
    (typeof fields?.resolved_model === 'string' ? fields.resolved_model : null);

  // Collect extra displayable fields (exclude known top-level pass-throughs)
  const SKIP_FIELDS = new Set(['model', 'resolved_model', 'proposals', 'branches']);
  const extraFields = fields
    ? Object.entries(fields).filter(([k]) => !SKIP_FIELDS.has(k))
    : [];

  const hasExpandable =
    recommendations != null || risks != null || extraFields.length > 0;

  return (
    <Card className="overflow-hidden">
      {/* ── Collapsed header row ── */}
      <div
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        onClick={() => hasExpandable && setExpanded((e) => !e)}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && hasExpandable) {
            e.preventDefault();
            setExpanded((v) => !v);
          }
        }}
        className={cn(
          'flex items-start gap-3 px-4 py-3',
          hasExpandable ? 'cursor-pointer hover:bg-[var(--accent)] transition-colors' : 'cursor-default',
        )}
      >
        <div className="flex-1 min-w-0">
          {/* Authorship line */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-semibold text-[var(--foreground)]">{skill_name}</span>
            {resolvedModel && (
              <span className="text-[10px] text-[var(--muted-foreground)] font-mono">
                via {resolvedModel}
              </span>
            )}
          </div>

          {/* Summary */}
          {summary && (
            <p className="text-xs text-[var(--muted-foreground)] line-clamp-3 leading-relaxed">
              {summary}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={stanceVariant(stance)}>{stanceLabel(stance)}</Badge>
          {hasExpandable && (
            <span className="text-[var(--muted-foreground)]">
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </span>
          )}
        </div>
      </div>

      {/* ── Expanded detail ── */}
      {expanded && (
        <CardContent className="border-t border-[var(--border)] px-4 py-3 space-y-4">
          {recommendations != null && (
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Recommendations
              </h4>
              {renderValue(recommendations)}
            </section>
          )}

          {risks != null && (
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Risks
              </h4>
              {renderValue(risks)}
            </section>
          )}

          {extraFields.length > 0 && (
            <section>
              <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Fields
              </h4>
              <dl className="space-y-1">
                {extraFields.map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-[10px] font-medium text-[var(--muted-foreground)] capitalize mb-0.5">
                      {k.replace(/_/g, ' ')}
                    </dt>
                    <dd>{renderValue(v)}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </CardContent>
      )}
    </Card>
  );
}
