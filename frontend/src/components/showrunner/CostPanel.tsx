// CostPanel — episode cost rollup, invocation table, and pre-flight estimate form
// (asr-0ei.7, TRD §6.6). Uses live polling for cost + invocations.
import { useState } from 'react';
import { Loader2, AlertTriangle, DollarSign, Zap, Image, Mic, Video } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { useEpisodeCost, useInvocations, useEstimate } from '@/api/showrunner/hooks';
import type { EstimateRequest, Estimate } from '@/api/showrunner/types';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtUsd(v: number | null | undefined): string {
  if (v == null) return '—';
  if (v === 0) return '$0.0000';
  if (v < 0.0001) return `$${v.toFixed(6)}`;
  return `$${v.toFixed(4)}`;
}

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';

function confidenceVariant(confidence: string | null | undefined): BadgeVariant {
  switch (confidence) {
    case 'exact':
    case 'measured':
      return 'success';
    case 'estimated':
      return 'warning';
    default:
      return 'secondary';
  }
}

function outcomeVariant(outcome: Estimate['outcome']): BadgeVariant {
  switch (outcome) {
    case 'allow':
      return 'success';
    case 'warn':
      return 'warning';
    case 'block':
      return 'destructive';
  }
}

function statusVariant(status: string | null | undefined): BadgeVariant {
  switch (status) {
    case 'ok':
    case 'done':
    case 'success':
      return 'success';
    case 'error':
    case 'failed':
      return 'destructive';
    case 'running':
    case 'pending':
      return 'warning';
    default:
      return 'secondary';
  }
}

// ── Cost rollup summary ───────────────────────────────────────────────────────

function StatPill({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="flex-1 min-w-28 rounded-md border border-[var(--border)] bg-[var(--muted)] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)] font-medium">
        {label}
      </p>
      <p className="text-sm font-bold mt-0.5 tabular-nums">{value}</p>
      {sub && <p className="text-[10px] text-[var(--muted-foreground)] mt-0.5">{sub}</p>}
    </div>
  );
}

// ── Invocation table ─────────────────────────────────────────────────────────

function InvocationTable({ episodeId }: { episodeId: string }) {
  const { data, isLoading, isError } = useInvocations(episodeId, true);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)] py-2">
        <Loader2 className="h-3 w-3 animate-spin" />
        Loading invocations…
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--destructive)] py-2">
        <AlertTriangle className="h-3 w-3" />
        Failed to load invocations.
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <p className="text-sm text-[var(--muted-foreground)] py-2">
        No skill invocations recorded yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-separate border-spacing-0">
        <thead>
          <tr className="text-[10px] text-[var(--muted-foreground)] uppercase tracking-wide">
            <th className="text-left pb-2 font-medium pr-3">Skill</th>
            <th className="text-left pb-2 font-medium pr-3">Model</th>
            <th className="text-right pb-2 font-medium pr-3">In</th>
            <th className="text-right pb-2 font-medium pr-3">Out</th>
            <th className="text-right pb-2 font-medium pr-3">Cost</th>
            <th className="text-center pb-2 font-medium pr-3">Confidence</th>
            <th className="text-center pb-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((inv) => (
            <tr
              key={inv.id}
              className="hover:bg-[var(--accent)] transition-colors"
            >
              <td className="py-1.5 pr-3 font-medium max-w-[120px] truncate" title={inv.skill_name}>
                {inv.skill_name}
              </td>
              <td className="py-1.5 pr-3 text-[var(--muted-foreground)] max-w-[100px] truncate" title={inv.model ?? ''}>
                {inv.model ?? '—'}
              </td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-[var(--muted-foreground)]">
                {inv.input_tokens != null ? inv.input_tokens.toLocaleString() : '—'}
              </td>
              <td className="py-1.5 pr-3 text-right tabular-nums text-[var(--muted-foreground)]">
                {inv.output_tokens != null ? inv.output_tokens.toLocaleString() : '—'}
              </td>
              <td className="py-1.5 pr-3 text-right tabular-nums">
                {fmtUsd(inv.cost_usd)}
              </td>
              <td className="py-1.5 pr-3 text-center">
                <Badge variant={confidenceVariant(inv.cost_confidence)}>
                  {inv.cost_confidence ?? '—'}
                </Badge>
              </td>
              <td className="py-1.5 text-center">
                <Badge variant={statusVariant(inv.status)}>
                  {inv.status ?? '—'}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Pre-flight estimate form ──────────────────────────────────────────────────

function EstimateForm({ episodeId }: { episodeId: string }) {
  const estimateMut = useEstimate(episodeId);

  const [form, setForm] = useState<EstimateRequest>({
    num_skill_calls: undefined,
    num_images: undefined,
    num_video_seconds: undefined,
    num_tts_chars: undefined,
  });

  function setField(key: keyof EstimateRequest, raw: string) {
    const parsed = raw === '' ? undefined : Number(raw);
    setForm((prev) => ({ ...prev, [key]: parsed }));
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    estimateMut.mutate(form);
  }

  const result = estimateMut.data;

  return (
    <div className="space-y-3">
      <p className="text-xs text-[var(--muted-foreground)]">
        Pre-flight estimate — enter expected workload to check budget before running.
      </p>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2">
        <label className="flex flex-col gap-1">
          <span className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] uppercase tracking-wide font-medium">
            <Zap className="h-3 w-3" />
            Skill calls
          </span>
          <Input
            type="number"
            min={0}
            placeholder="e.g. 10"
            className="h-8 text-xs"
            value={form.num_skill_calls ?? ''}
            onChange={(e) => setField('num_skill_calls', e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] uppercase tracking-wide font-medium">
            <Image className="h-3 w-3" />
            Images
          </span>
          <Input
            type="number"
            min={0}
            placeholder="e.g. 5"
            className="h-8 text-xs"
            value={form.num_images ?? ''}
            onChange={(e) => setField('num_images', e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] uppercase tracking-wide font-medium">
            <Video className="h-3 w-3" />
            Video seconds
          </span>
          <Input
            type="number"
            min={0}
            placeholder="e.g. 30"
            className="h-8 text-xs"
            value={form.num_video_seconds ?? ''}
            onChange={(e) => setField('num_video_seconds', e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] uppercase tracking-wide font-medium">
            <Mic className="h-3 w-3" />
            TTS chars
          </span>
          <Input
            type="number"
            min={0}
            placeholder="e.g. 1000"
            className="h-8 text-xs"
            value={form.num_tts_chars ?? ''}
            onChange={(e) => setField('num_tts_chars', e.target.value)}
          />
        </label>
        <div className="col-span-2 flex items-center gap-3">
          <Button
            type="submit"
            size="sm"
            disabled={estimateMut.isPending}
            className="flex items-center gap-1.5"
          >
            {estimateMut.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
            Estimate
          </Button>
          {estimateMut.isError && (
            <span className="text-xs text-[var(--destructive)]">Estimate failed.</span>
          )}
        </div>
      </form>

      {result && (
        <div className="rounded-md border border-[var(--border)] bg-[var(--muted)] p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">Outcome</span>
            <Badge variant={outcomeVariant(result.outcome)} className="uppercase">
              {result.outcome}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <p className="text-[var(--muted-foreground)]">This run</p>
              <p className="font-bold tabular-nums">{fmtUsd(result.estimate_usd)}</p>
            </div>
            <div>
              <p className="text-[var(--muted-foreground)]">Projected total</p>
              <p className="font-bold tabular-nums">{fmtUsd(result.projected_usd)}</p>
            </div>
            <div>
              <p className="text-[var(--muted-foreground)]">Limit</p>
              <p className="font-bold tabular-nums">
                {result.limit_usd <= 0 ? 'Unlimited' : fmtUsd(result.limit_usd)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────

export function CostPanel({ episodeId }: { episodeId: string }) {
  const { data: cost, isLoading, isError } = useEpisodeCost(episodeId, true);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <DollarSign className="h-4 w-4" />
          Cost
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Cost rollup */}
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading cost data…
          </div>
        )}
        {isError && (
          <div className="flex items-center gap-2 text-sm text-[var(--destructive)]">
            <AlertTriangle className="h-4 w-4" />
            Cost data unavailable.
          </div>
        )}
        {cost && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <StatPill
                label="Skill cost"
                value={fmtUsd(cost.skill_cost_usd)}
                sub={`${cost.skill_calls} call${cost.skill_calls !== 1 ? 's' : ''}`}
              />
              <StatPill
                label="Media cost"
                value={fmtUsd(cost.media_cost_usd)}
                sub={`${cost.media_jobs} job${cost.media_jobs !== 1 ? 's' : ''}`}
              />
              <StatPill label="Total" value={fmtUsd(cost.total_usd)} />
            </div>
            <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <span>Confidence</span>
              <Badge variant={confidenceVariant(cost.confidence)}>{cost.confidence}</Badge>
            </div>
          </div>
        )}

        {/* Invocation table */}
        <div>
          <p className={cn(
            'text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide mb-2',
          )}>
            Invocations
          </p>
          <InvocationTable episodeId={episodeId} />
        </div>

        {/* Pre-flight estimate */}
        <div>
          <p className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide mb-2">
            Pre-flight estimate
          </p>
          <EstimateForm episodeId={episodeId} />
        </div>
      </CardContent>
    </Card>
  );
}
