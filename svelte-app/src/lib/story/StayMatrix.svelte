<!--
  Stay matrix: heart condition (rows) x triage acuity (columns) x gender (two triangles per cell).
  step 0: color = median ED stay (women = upper-left triangle, men = lower-right)
  step 1: color = gender gap (women minus men), diverging scale
  Hidden cells (fewer than min_cell_size visits) are hatched, never shown as zero.
-->
<script lang="ts">
	import { ALL, NON_CARDIAC, CARDIAC_ALL, fmt1, fmtInt, getCell, DEFAULT_FILTERS, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';
	import { COND_COLORS } from './story.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	const ACU = ['1', '2', '3', '4'];
	const groups = $derived([
		NON_CARDIAC,
		CARDIAC_ALL,
		...cube.meta.dim_values.group.filter((g) => ![ALL, NON_CARDIAC, CARDIAC_ALL].includes(g))
	]);
	const med = (g: string, a: string, gender: string) =>
		getCell(cube, { ...DEFAULT_FILTERS, group: g, acuity: a, gender })?.los.median ?? null;
	const nOf = (g: string, a: string, gender: string) =>
		getCell(cube, { ...DEFAULT_FILTERS, group: g, acuity: a, gender })?.n ?? null;

	const grid = $derived(
		groups.map((g) => ({
			g,
			cells: ACU.map((a) => ({ a, f: med(g, a, 'Female'), m: med(g, a, 'Male'), nf: nOf(g, a, 'Female'), nm: nOf(g, a, 'Male') }))
		}))
	);

	// color scales
	const LO = 2, HI = 8;
	const seq = ['#fff7ec', '#fdd49e', '#fc8d59', '#d7301f', '#7f0000'];
	function lerp(a: string, b: string, t: number) {
		const p = (s: string) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
		const [x, y] = [p(a), p(b)];
		return `rgb(${x.map((v, i) => Math.round(v + (y[i] - v) * t)).join(',')})`;
	}
	const stayColor = (v: number | null) => {
		if (v == null) return null;
		const t = Math.max(0, Math.min(1, (v - LO) / (HI - LO))) * (seq.length - 1);
		const i = Math.min(seq.length - 2, Math.floor(t));
		return lerp(seq[i], seq[i + 1], t - i);
	};
	const gapColor = (d: number | null) => {
		if (d == null) return null;
		const t = Math.max(-1, Math.min(1, d / 1.2));
		return t >= 0 ? lerp('#f8fafc', '#9333ea', t) : lerp('#f8fafc', '#0d9488', -t);
	};

	let w = $state(700);
	let h = $state(440);
	const m = { top: 34, right: 16, bottom: 56, left: 168 };
	const cw = $derived((w - m.left - m.right) / ACU.length);
	const rh = $derived(Math.min(80, (h - m.top - m.bottom) / groups.length));
	const label = (g: string) => (g === CARDIAC_ALL ? 'All cardiac' : g);

	const womenLonger = $derived(
		grid.filter((r) => r.g !== NON_CARDIAC && r.g !== CARDIAC_ALL)
			.flatMap((r) => r.cells).filter((c) => c.f != null && c.m != null)
	);
	const kW = $derived(womenLonger.filter((c) => c.f! > c.m!).length);
</script>

<div class="title">{step === 0 ? 'Median ED stay: condition × acuity × gender' : 'Gender gap in ED stay (women − men)'}</div>
<div class="sub">
	Each cell: <b>upper-left = women</b>, <b>lower-right = men</b>. Hatched = too few visits to show.
	<span class="legend">
		{#if step === 0}
			{LO} h <span class="bar" style:background={`linear-gradient(90deg, ${seq.join(',')})`}></span> {HI}+ h
		{:else}
			men longer <span class="bar" style:background="linear-gradient(90deg,#0d9488,#f8fafc,#9333ea)"></span> women longer
		{/if}
	</span>
</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Heatmap of median ED stay by condition, acuity and gender">
		<defs>
			<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<rect width="6" height="6" fill="#f1f5f9" /><line x1="0" y1="0" x2="0" y2="6" stroke="#cbd5e1" stroke-width="2" />
			</pattern>
		</defs>
		{#each ACU as a, j}
			<text x={m.left + (j + 0.5) * cw} y={m.top - 12} text-anchor="middle" class="col">Acuity {a}{a === '1' ? ' (most urgent)' : ''}</text>
		{/each}
		{#each grid as r, i}
			{@const y = m.top + i * rh}
			<text x={m.left - 12} y={y + rh / 2 + 4} text-anchor="end" class="row"
				class:sel={filters.group === r.g} style:fill={COND_COLORS[r.g] ?? (r.g === NON_CARDIAC ? '#e87945' : '#2563eb')}>{label(r.g)}</text>
			{#if i === 2}<line x1={m.left - 150} x2={m.left + cw * ACU.length} y1={y} y2={y} stroke="#94a3b8" stroke-dasharray="3 3" />{/if}
			{#each r.cells as c, j}
				{@const x = m.left + j * cw + 2}
				{@const cwi = cw - 4} {@const rhi = rh - 4}
				{@const fc = step === 0 ? stayColor(c.f) : gapColor(c.f != null && c.m != null ? c.f - c.m : null)}
				{@const mc = step === 0 ? stayColor(c.m) : gapColor(c.f != null && c.m != null ? c.f - c.m : null)}
				<g role="presentation"
					onmousemove={(e) => showTip(e, [`${label(r.g)} · acuity ${c.a}`,
						`Women: ${c.f != null ? fmt1(c.f) + ' h' : 'hidden'}${c.nf ? ` (n ≈ ${fmtInt(c.nf)})` : ''}`,
						`Men: ${c.m != null ? fmt1(c.m) + ' h' : 'hidden'}${c.nm ? ` (n ≈ ${fmtInt(c.nm)})` : ''}`,
						c.f != null && c.m != null ? `Women − men: ${c.f - c.m >= 0 ? '+' : ''}${fmt1(c.f - c.m)} h` : ''])}
					onmouseleave={hideTip}>
					<path d={`M${x},${y + 2} L${x + cwi},${y + 2} L${x},${y + 2 + rhi} Z`} fill={fc ?? 'url(#hatch)'} class="tri" />
					<path d={`M${x + cwi},${y + 2} L${x + cwi},${y + 2 + rhi} L${x},${y + 2 + rhi} Z`} fill={mc ?? 'url(#hatch)'} class="tri" />
					<rect x={x} y={y + 2} width={cwi} height={rhi} fill="none" stroke="#fff" stroke-width="2" rx="3" />
					{#if step === 1 && c.f != null && c.m != null}
						<text x={x + cwi / 2} y={y + 2 + rhi / 2 + 4} text-anchor="middle" class="gap">{c.f - c.m >= 0 ? '+' : ''}{fmt1(c.f - c.m)}</text>
					{:else if step === 0 && cwi > 110}
						<text x={x + 8} y={y + 18} class="v">{c.f != null ? fmt1(c.f) : ''}</text>
						<text x={x + cwi - 8} y={y + rhi - 4} text-anchor="end" class="v">{c.m != null ? fmt1(c.m) : ''}</text>
					{/if}
				</g>
			{/each}
		{/each}
		<text x={m.left} y={h - 14} class="foot">
			{step === 0 ? 'Darker = longer stay. Hover a cell for both values and the gap.' : `Women stay longer than men in ${kW} of ${womenLonger.length} condition × acuity cells.`}
		</text>
	</svg>
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.8rem; color: #64748b; margin-top: 4px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
	.legend { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; color: #334155; }
	.bar { display: inline-block; width: 120px; height: 10px; border-radius: 5px; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.col { font-size: 12px; font-weight: 800; fill: #334155; }
	.row { font-size: 13px; font-weight: 800; }
	.row.sel { text-decoration: underline; }
	.tri { transition: fill 0.7s ease; }
	.v { font-size: 11px; font-weight: 700; fill: #1e293b; paint-order: stroke; stroke: #ffffffaa; stroke-width: 3px; pointer-events: none; }
	.gap { font-size: 12px; font-weight: 800; fill: #1e293b; pointer-events: none; }
	.foot { font-size: 12.5px; font-weight: 700; fill: #334155; }
</style>
