/** Serialize rows to RFC-4180 CSV. */
export function toCsv(
  headers: string[],
  rows: (string | number | null | undefined)[][],
): string {
  const escape = (val: string | number | null | undefined) => {
    const s = val == null ? "" : String(val);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [headers.map(escape).join(",")];
  for (const row of rows) lines.push(row.map(escape).join(","));
  return lines.join("\r\n");
}

export function csvFilename(prefix: string): string {
  const date = new Date().toISOString().slice(0, 10);
  return `${prefix}-${date}.csv`;
}
