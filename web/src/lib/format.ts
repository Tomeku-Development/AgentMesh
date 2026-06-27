/**
 * Compact number formatting helpers for the stats bar.
 */

const compact = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2,
});

const standard = new Intl.NumberFormat("en-US");

/** 24392 -> "24,392" */
export function formatNumber(value: number): string {
  return standard.format(value);
}

/** 2450000 -> "2.45M" */
export function formatCompact(value: number): string {
  return compact.format(value);
}

/** 2450000 -> "2.45M CSPR" */
export function formatCspr(value: number): string {
  return `${compact.format(value)} CSPR`;
}
