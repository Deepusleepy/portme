// Faithful port of the subset of Python's difflib + Click's _format_possibilities
// used by the notes CLI's "did you mean" suggestion (rulebook R-005, R-006).
//
// get_close_matches(word, possibilities, n=3, cutoff=0.6) with CPython defaults.
// SequenceMatcher.ratio() is ported exactly (junk-free; autojunk is irrelevant
// for inputs far below the 200-element threshold). quick_ratio/real_quick_ratio
// are pure upper bounds on ratio, so gating on `ratio >= cutoff` alone yields an
// identical match set to CPython's triple-gated filter.

// Sum of matched-block sizes between a and b (== CPython get_matching_blocks
// total; block merging never changes the total, so we skip it).
function matchCount(a: string, b: string): number {
  // b2j: element -> ascending indices in b
  const b2j = new Map<string, number[]>();
  for (let i = 0; i < b.length; i++) {
    const arr = b2j.get(b[i]);
    if (arr) arr.push(i);
    else b2j.set(b[i], [i]);
  }

  // find_longest_match over a[alo:ahi], b[blo:bhi]
  function findLongest(alo: number, ahi: number, blo: number, bhi: number): [number, number, number] {
    let besti = alo, bestj = blo, bestsize = 0;
    let j2len = new Map<number, number>();
    for (let i = alo; i < ahi; i++) {
      const newj2len = new Map<number, number>();
      const idxs = b2j.get(a[i]);
      if (idxs) {
        for (const j of idxs) {
          if (j < blo) continue;
          if (j >= bhi) break;
          const k = (j2len.get(j - 1) ?? 0) + 1;
          newj2len.set(j, k);
          if (k > bestsize) {
            besti = i - k + 1;
            bestj = j - k + 1;
            bestsize = k;
          }
        }
      }
      j2len = newj2len;
    }
    // Extend the match (no junk, so only the non-junk extension loops apply).
    while (besti > alo && bestj > blo && a[besti - 1] === b[bestj - 1]) {
      besti--; bestj--; bestsize++;
    }
    while (besti + bestsize < ahi && bestj + bestsize < bhi &&
           a[besti + bestsize] === b[bestj + bestsize]) {
      bestsize++;
    }
    return [besti, bestj, bestsize];
  }

  let total = 0;
  const queue: [number, number, number, number][] = [[0, a.length, 0, b.length]];
  while (queue.length) {
    const [alo, ahi, blo, bhi] = queue.pop()!;
    const [i, j, k] = findLongest(alo, ahi, blo, bhi);
    if (k) {
      total += k;
      if (alo < i && blo < j) queue.push([alo, i, blo, j]);
      if (i + k < ahi && j + k < bhi) queue.push([i + k, ahi, j + k, bhi]);
    }
  }
  return total;
}

// SequenceMatcher.ratio() with set_seq1(a=possibility), set_seq2(b=word).
function ratio(a: string, b: string): number {
  const length = a.length + b.length;
  if (!length) return 1.0;
  return (2.0 * matchCount(a, b)) / length;
}

export function getCloseMatches(
  word: string,
  possibilities: string[],
  n = 3,
  cutoff = 0.6,
): string[] {
  if (n <= 0) throw new Error(`n must be > 0: ${n}`);
  if (cutoff < 0.0 || cutoff > 1.0) throw new Error(`cutoff must be in [0.0, 1.0]: ${cutoff}`);
  const scored: [number, string][] = [];
  for (const x of possibilities) {
    const r = ratio(x, word); // set_seq1(x), set_seq2(word)
    if (r >= cutoff) scored.push([r, x]);
  }
  // heapq.nlargest(n, scored): the n largest (score, x) tuples, descending.
  scored.sort((p, q) => (q[0] - p[0]) || cmpStr(q[1], p[1]));
  return scored.slice(0, n).map(([, x]) => x);
}

// Python string ordering by Unicode code point.
function cmpStr(x: string, y: string): number {
  const lx = x.length, ly = y.length, m = Math.min(lx, ly);
  for (let i = 0; i < m; i++) {
    const dx = x.codePointAt(i)!, dy = y.codePointAt(i)!;
    if (dx !== dy) return dx - dy;
  }
  return lx - ly;
}

// Python repr() for a str, matching CPython's quote selection and escaping.
export function pyRepr(s: string): string {
  const hasSingle = s.includes("'");
  const hasDouble = s.includes('"');
  const quote = hasSingle && !hasDouble ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    const cp = ch.codePointAt(0)!;
    if (ch === '\\') out += '\\\\';
    else if (ch === quote) out += '\\' + ch;
    else if (ch === '\n') out += '\\n';
    else if (ch === '\r') out += '\\r';
    else if (ch === '\t') out += '\\t';
    else if (cp < 0x20 || cp === 0x7f) out += '\\x' + cp.toString(16).padStart(2, '0');
    else out += ch;
  }
  return out + quote;
}

// Mirror of click.exceptions._format_possibilities.
export function formatPossibilities(possibilities: string[]): string {
  const sorted = [...possibilities].sort(cmpStr);
  const s = sorted.map(pyRepr).join(', ');
  if (possibilities.length === 1) return `Did you mean ${s}?`;
  return `(Did you mean one of: ${s}?)`;
}
