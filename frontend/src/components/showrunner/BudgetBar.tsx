// BudgetBar — horizontal stacked meter for episode budget (asr-0ei.7, TRD §6.6).
// Shows spent_usd (solid) + reserved_usd (hatched/lighter) against limit_usd with
// a soft-cap marker. Handles unlimited (limit_usd <= 0) gracefully.
import { AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEpisodeBudget } from '@/api/showrunner/hooks';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtUsd(v: number): string {
  if (v === 0) return '$0.0000';
  if (v < 0.0001) return `$${v.toFixed(6)}`;
  return `$${v.toFixed(4)}`;
}

type MeterColor = 'normal' | 'warning' | 'destructive';

function meterColor(
  spent: number,
  reserved: number,
  limit: number,
  softPct: number,
): MeterColor {
  if (spent + reserved >= limit) return 'destructive';
  if (spent + reserved >= limit * (softPct / 100)) return 'warning';
  return 'normal';
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function NumericRow({
  spent,
  reserved,
  available,
  limit,
}: {
  spent: number;
  reserved: number;
  available: number;
  limit: number;
}) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-[var(--muted-foreground)]">
      <span>
        <span className="font-medium text-[var(--foreground)]">Spent</span>{' '}
        {fmtUsd(spent)}
      </span>
      <span>
        <span className="font-medium text-[var(--foreground)]">Reserved</span>{' '}
        {fmtUsd(reserved)}
      </span>
      <span>
        <span className="font-medium text-[var(--foreground)]">Available</span>{' '}
        {fmtUsd(available)}
      </span>
      <span>
        <span className="font-medium text-[var(--foreground)]">Limit</span>{' '}
        {fmtUsd(limit)}
      </span>
    </div>
  );
}

// ── Meter ─────────────────────────────────────────────────────────────────────

interface MeterProps {
  spent: number;
  reserved: number;
  limit: number;
  softPct: number;
  color: MeterColor;
}

function Meter({ spent, reserved, limit, softPct, color }: MeterProps) {
  const spentPct = Math.min((spent / limit) * 100, 100);
  const reservedPct = Math.min((reserved / limit) * 100, 100 - spentPct);
  const softMarkerPct = Math.min(softPct, 100);

  const spentBg =
    color === 'destructive'
      ? 'bg-[var(--destructive)]'
      : color === 'warning'
        ? 'bg-amber-500'
        : 'bg-[var(--primary)]';

  const reservedBg =
    color === 'destructive'
      ? 'bg-red-300'
      : color === 'warning'
        ? 'bg-amber-300'
        : 'bg-[var(--primary)]/40';

  return (
    <div className="relative">
      {/* Track */}
      <div className="h-4 rounded-full overflow-hidden border border-[var(--border)] bg-[var(--muted)] flex">
        {/* Spent segment */}
        <div
          className={cn('h-full transition-all', spentBg)}
          style={{ width: `${spentPct}%` }}
        />
        {/* Reserved segment — hatched via repeating-linear-gradient overlay */}
        <div
          className={cn('h-full transition-all relative overflow-hidden', reservedBg)}
          style={{ width: `${reservedPct}%` }}
        >
          {/* Hatching overlay */}
          <div
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage:
                'repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(0,0,0,0.4) 3px, rgba(0,0,0,0.4) 4px)',
            }}
          />
        </div>
      </div>

      {/* Soft-cap marker */}
      <div
        className="absolute top-0 bottom-0 w-px bg-yellow-500 opacity-80"
        style={{ left: `${softMarkerPct}%` }}
        title={`Soft cap at ${softPct}%`}
      />
      <div
        className="absolute -top-3 text-[9px] text-yellow-600 font-medium"
        style={{ left: `${softMarkerPct}%`, transform: 'translateX(-50%)' }}
      >
        {softPct}%
      </div>
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────

export function BudgetBar({ episodeId }: { episodeId: string }) {
  const { data, isLoading, isError } = useEpisodeBudget(episodeId, true);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)] py-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading budget…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--destructive)] py-2">
        <AlertTriangle className="h-4 w-4" />
        Budget unavailable.
      </div>
    );
  }

  const { limit_usd, soft_pct, spent_usd, reserved_usd, available_usd } = data;

  // Unlimited budget
  if (limit_usd <= 0) {
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
            Budget
          </span>
          <span className="text-xs text-[var(--muted-foreground)]">Unlimited</span>
        </div>
        <NumericRow
          spent={spent_usd}
          reserved={reserved_usd}
          available={available_usd}
          limit={0}
        />
      </div>
    );
  }

  const color = meterColor(spent_usd, reserved_usd, limit_usd, soft_pct);

  return (
    <div className="space-y-1 pt-3">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
          Budget
        </span>
        {color === 'destructive' && (
          <span className="flex items-center gap-1 text-xs text-[var(--destructive)] font-medium">
            <AlertTriangle className="h-3 w-3" />
            Limit reached
          </span>
        )}
        {color === 'warning' && (
          <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
            <AlertTriangle className="h-3 w-3" />
            Near soft cap
          </span>
        )}
      </div>
      <Meter
        spent={spent_usd}
        reserved={reserved_usd}
        limit={limit_usd}
        softPct={soft_pct}
        color={color}
      />
      <NumericRow
        spent={spent_usd}
        reserved={reserved_usd}
        available={available_usd}
        limit={limit_usd}
      />
    </div>
  );
}
