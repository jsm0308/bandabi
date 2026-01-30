// apps/dev_ui/src/lib/csv.ts
// pandas CSV(따옴표/콤마 포함)도 안전하게 파싱하는 최소 CSV 파서

export type Row = Record<string, string>;

export function parseCsv(text: string): Row[] {
  const lines = splitLines(text);
  if (lines.length === 0) return [];
  const header = parseLine(lines[0]);
  const rows: Row[] = [];

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const fields = parseLine(lines[i]);
    const row: Row = {};
    for (let c = 0; c < header.length; c++) row[header[c]] = fields[c] ?? "";
    rows.push(row);
  }
  return rows;
}

function splitLines(text: string): string[] {
  // BOM 제거
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
}

function parseLine(line: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];

    if (inQuotes) {
      if (ch === '"') {
        const next = line[i + 1];
        if (next === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cur += ch;
      }
    } else {
      if (ch === '"') inQuotes = true;
      else if (ch === ",") {
        out.push(cur);
        cur = "";
      } else {
        cur += ch;
      }
    }
  }
  out.push(cur);
  return out;
}
