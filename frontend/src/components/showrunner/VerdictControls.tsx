// VerdictControls — submission form for Greenlight Council gate verdicts.
// Renders verdict buttons appropriate to the current gate plus optional
// actor, rationale, and (for the episode gate) estimate_usd fields.
// A 409 budget_exceeded error from the backend is surfaced as a destructive callout.
import { useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { usePostGreenlight } from '@/api/showrunner/hooks';
import type { GateName } from '@/api/showrunner/types';

interface VerdictControlsProps {
  episodeId: string;
  gate: GateName;
}

// Loopback/decline options differ per gate.
type VerdictOption = {
  verdict: string;
  label: string;
  variant: 'default' | 'outline' | 'secondary' | 'destructive';
};

function verdictOptions(gate: GateName): VerdictOption[] {
  const kill: VerdictOption = { verdict: 'kill', label: 'Kill', variant: 'destructive' };
  const defer: VerdictOption = { verdict: 'defer', label: 'Defer', variant: 'outline' };

  switch (gate) {
    case 'branch':
      return [
        { verdict: 'approved', label: 'Approve', variant: 'default' },
        { verdict: 'reconsider', label: 'Reconsider', variant: 'secondary' },
        kill,
        defer,
      ];
    case 'episode':
      return [
        { verdict: 'approved', label: 'Approve', variant: 'default' },
        { verdict: 'revise', label: 'Revise', variant: 'secondary' },
        kill,
        defer,
      ];
    case 'final':
      return [
        { verdict: 'approved', label: 'Approve', variant: 'default' },
        { verdict: 'reduce', label: 'Reduce', variant: 'secondary' },
        kill,
        defer,
      ];
  }
}

// Extract a readable message from an unknown error shape.
function extractErrorMessage(err: unknown): string {
  if (!err) return 'Unknown error.';
  if (typeof err === 'string') return err;
  // Axios-style response shape
  const e = err as Record<string, unknown>;
  const detail = (e['response'] as Record<string, unknown> | undefined)?.['data'];
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    const d = detail as Record<string, unknown>;
    if (typeof d['detail'] === 'string') return d['detail'];
  }
  if (typeof e['message'] === 'string') return e['message'];
  return JSON.stringify(err);
}

function isBudgetExceeded(err: unknown): boolean {
  return extractErrorMessage(err).toLowerCase().includes('budget_exceeded');
}

function gateLabel(gate: GateName): string {
  switch (gate) {
    case 'branch':
      return 'Branch Gate';
    case 'episode':
      return 'Episode Gate';
    case 'final':
      return 'Final Gate';
  }
}

export function VerdictControls({ episodeId, gate }: VerdictControlsProps) {
  const { mutate, isPending, isSuccess, isError, error, data } = usePostGreenlight(episodeId);

  const [actor, setActor] = useState('');
  const [rationale, setRationale] = useState('');
  const [estimateUsd, setEstimateUsd] = useState('');

  function submit(verdict: string) {
    mutate({
      gate,
      body: {
        verdict,
        actor: actor.trim() || undefined,
        rationale: rationale.trim() || undefined,
        estimate_usd:
          gate === 'episode' && estimateUsd !== ''
            ? parseFloat(estimateUsd)
            : undefined,
      },
    });
  }

  const options = verdictOptions(gate);
  const budgetError = isError && isBudgetExceeded(error);

  return (
    <section className="space-y-4">
      {/* Gate heading */}
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="text-xs font-mono">
          {gateLabel(gate)}
        </Badge>
      </div>

      {/* Optional fields */}
      <div className="space-y-2">
        <Input
          placeholder="Actor (optional — who is casting this vote?)"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
          disabled={isPending}
        />
        <Textarea
          placeholder="Rationale (optional)"
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          disabled={isPending}
          className="min-h-[60px]"
        />

        {gate === 'episode' && (
          <div className="space-y-1">
            <label className="text-xs text-[var(--muted-foreground)]">
              Estimated budget (USD) — required for budget reservation on approval
            </label>
            <Input
              type="number"
              min={0}
              step={0.01}
              placeholder="e.g. 12.50"
              value={estimateUsd}
              onChange={(e) => setEstimateUsd(e.target.value)}
              disabled={isPending}
            />
          </div>
        )}
      </div>

      {/* Verdict buttons */}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <Button
            key={opt.verdict}
            variant={opt.variant}
            size="sm"
            disabled={isPending}
            onClick={() => submit(opt.verdict)}
            className={cn(opt.verdict === 'approved' && 'bg-green-600 text-white hover:opacity-90')}
          >
            {isPending && <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />}
            {opt.label}
          </Button>
        ))}
      </div>

      {/* Budget exceeded error */}
      {budgetError && (
        <div className="flex items-start gap-2 rounded-md border border-[var(--destructive)] bg-red-50 px-3 py-2">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--destructive)]" />
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-[var(--destructive)]">Budget cap exceeded</p>
            <p className="text-xs text-[var(--destructive)]">
              This episode&apos;s estimated cost exceeds its budget limit. Reduce the estimate or
              request a budget increase before approving.
            </p>
          </div>
        </div>
      )}

      {/* Generic error (non-budget) */}
      {isError && !budgetError && (
        <div className="flex items-start gap-2 rounded-md border border-[var(--destructive)] bg-red-50 px-3 py-2">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--destructive)]" />
          <p className="text-xs text-[var(--destructive)]">{extractErrorMessage(error)}</p>
        </div>
      )}

      {/* Success */}
      {isSuccess && data && (
        <div className="flex items-start gap-2 rounded-md border border-green-300 bg-green-50 px-3 py-2">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-700" />
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-green-800">
              Verdict recorded: <span className="capitalize">{data.verdict}</span>
            </p>
            <p className="text-xs text-green-700">
              New episode status:{' '}
              <span className="font-mono">{data.status}</span>
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
