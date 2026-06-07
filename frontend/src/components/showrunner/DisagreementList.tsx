// DisagreementList — renders every recorded disagreement for an episode.
// Each skill's individual stance is shown VERBATIM (UAT-TEAM-004/005):
// stances are never merged or averaged — dissent is preserved in full.
import { AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useDisagreements } from '@/api/showrunner/hooks';
import { stanceVariant, stanceLabel } from '@/components/showrunner/stance';

interface DisagreementListProps {
  episodeId: string;
}

export function DisagreementList({ episodeId }: DisagreementListProps) {
  const { data: disagreements, isLoading, isError } = useDisagreements(episodeId, true);

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-[var(--muted-foreground)]" />
        <h3 className="text-sm font-semibold text-[var(--foreground)]">Recorded Disagreements</h3>
      </div>

      <p className="text-xs text-[var(--muted-foreground)]">
        Each skill&apos;s stance is shown verbatim — dissent is preserved, never synthesized away.
      </p>

      {isLoading && (
        <p className="text-xs text-[var(--muted-foreground)]">Loading disagreements…</p>
      )}

      {isError && (
        <p className="text-xs text-[var(--destructive)]">Failed to load disagreements.</p>
      )}

      {!isLoading && !isError && (!disagreements || disagreements.length === 0) && (
        <p className="text-xs text-[var(--muted-foreground)]">No recorded disagreements.</p>
      )}

      {disagreements && disagreements.map((d) => (
        <Card key={d.id} className="overflow-hidden">
          <CardHeader className="pb-2 pt-4 px-4">
            <div className="flex items-start justify-between gap-3">
              <CardTitle className="text-sm font-semibold capitalize">
                {d.axis.replace(/_/g, ' ')}
              </CardTitle>
              <Badge variant={d.resolved ? 'success' : 'warning'}>
                {d.resolved ? 'Resolved' : 'Unresolved'}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="px-4 pb-4 space-y-3">
            {/* Per-skill stances — verbatim, one badge per skill */}
            {Object.keys(d.stances).length > 0 && (
              <div>
                <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                  Skill Stances
                </p>
                <ul className="flex flex-wrap gap-2">
                  {Object.entries(d.stances).map(([skillName, stance]) => (
                    <li key={skillName} className="flex items-center gap-1.5">
                      <span className="text-xs text-[var(--foreground)]">{skillName}</span>
                      <Badge variant={stanceVariant(stance)}>{stanceLabel(stance)}</Badge>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Detail text */}
            {d.detail && (
              <div>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                  Detail
                </p>
                <p className="text-xs text-[var(--foreground)] leading-relaxed">{d.detail}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
