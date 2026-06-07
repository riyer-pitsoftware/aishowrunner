// BranchProposals — derives branch/story proposals from contribution fields.
// No dedicated backend endpoint yet (Sprint 6+); reads proposals/branches arrays
// from contribution.fields defensively. (asr-0ei.2)
import { GitFork } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Contribution } from '@/api/showrunner/types';

// ── Types for extracted proposals ────────────────────────────────────────────

interface Proposal {
  hook?: string;
  consequences?: string;
  complexity?: string;
  [key: string]: unknown;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function asProposal(v: unknown): Proposal | null {
  if (typeof v === 'string') return { hook: v };
  if (isRecord(v)) return v as Proposal;
  return null;
}

/** Extract proposals/branches arrays from all contributions' fields. */
function extractProposals(contributions: Contribution[]): Proposal[] {
  const results: Proposal[] = [];

  for (const contrib of contributions) {
    if (!contrib.fields) continue;

    for (const key of ['proposals', 'branches']) {
      const raw = contrib.fields[key];
      if (!Array.isArray(raw)) continue;

      for (const item of raw) {
        const p = asProposal(item);
        if (p) results.push(p);
      }
    }
  }

  return results;
}

function complexityVariant(
  complexity: string | undefined,
): 'default' | 'warning' | 'destructive' | 'secondary' {
  if (!complexity) return 'secondary';
  const lower = complexity.toLowerCase();
  if (lower === 'high') return 'destructive';
  if (lower === 'medium') return 'warning';
  return 'default';
}

// ── ProposalCard ─────────────────────────────────────────────────────────────

function ProposalCard({ proposal, index }: { proposal: Proposal; index: number }) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] px-3 py-2.5 space-y-1.5">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-semibold text-[var(--muted-foreground)]">
          Branch {index + 1}
        </span>
        {proposal.complexity && (
          <Badge variant={complexityVariant(String(proposal.complexity))} >
            {String(proposal.complexity)}
          </Badge>
        )}
      </div>

      {proposal.hook && (
        <p className="text-xs text-[var(--foreground)] leading-relaxed">{String(proposal.hook)}</p>
      )}

      {proposal.consequences && (
        <p className="text-[11px] text-[var(--muted-foreground)] italic leading-relaxed">
          {String(proposal.consequences)}
        </p>
      )}
    </div>
  );
}

// ── BranchProposals ──────────────────────────────────────────────────────────

interface BranchProposalsProps {
  contributions: Contribution[];
}

export function BranchProposals({ contributions }: BranchProposalsProps) {
  const proposals = extractProposals(contributions);

  return (
    <Card className="mb-4">
      <CardHeader className="px-4 py-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <GitFork className="h-4 w-4 text-[var(--muted-foreground)]" />
          Branch Proposals
          {proposals.length > 0 && (
            <span className="ml-auto rounded-full bg-[var(--accent)] px-1.5 py-0.5 text-[10px] font-normal text-[var(--muted-foreground)]">
              {proposals.length}
            </span>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="px-4 pb-4 pt-0">
        {proposals.length === 0 ? (
          <p className="text-xs text-[var(--muted-foreground)] italic">
            Branch proposals appear after the Story Room runs.
          </p>
        ) : (
          <div className="space-y-2">
            {proposals.map((proposal, i) => (
              <ProposalCard key={i} proposal={proposal} index={i} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
