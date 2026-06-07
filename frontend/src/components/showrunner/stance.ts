// Shared stance → presentation mapping. Used by Story Room contribution cards and
// the Greenlight disagreement view so stance colors stay consistent (TRD §8.3).
import type { Stance } from '@/api/showrunner/types';

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';

export function stanceVariant(stance: string): BadgeVariant {
  switch (stance) {
    case 'support':
      return 'success';
    case 'concern':
      return 'warning';
    case 'block':
      return 'destructive';
    default:
      return 'secondary';
  }
}

export function stanceLabel(stance: string): string {
  return stance ? stance.charAt(0).toUpperCase() + stance.slice(1) : 'Unknown';
}

export const STANCE_ORDER: Stance[] = ['block', 'concern', 'support', 'unknown'];
