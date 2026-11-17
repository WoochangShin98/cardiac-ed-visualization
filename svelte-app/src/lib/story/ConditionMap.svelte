<!--
  Condition map: one view that holds five attributes at once.
    x = median ED stay, y = admission rate, bubble area = number of visits,
    color = heart condition, shape = gender (circle = women, diamond = men).
  step 0: one bubble per condition (all patients)
  step 1: each bubble splits into a woman + man pair joined by a line (unified gender view)
  step 2: quadrants against the non-cardiac baseline
  Click a bubble to make that condition the focus group for the whole page.
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut } from 'svelte/easing';
	import { ALL, NON_CARDIAC, CARDIAC_ALL, nz, fmt1, fmtInt, pct, getCell, DEFAULT_FILTERS, type Cube, type Cell } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';
	import { reduceMotion, COND_COLORS } from './story.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	const conds = $derived(cube.meta.dim_values.group.filter((g) => ![ALL, NON_CARDIAC, CARDIAC_ALL].includes(g)));

	// this view always shows both genders, so it ignores the gender switch on purpose
	const cell = (g: string, gender: string) => getCell(cube, { ...DEFAULT_FILTERS, group: g, gender });
	const adm = (c: Cell | null) => {
		const d = c?.dispo.map(nz) ?? [];
		const t = d.reduce((a, b) => a + b, 0);
		return t ? d[0] / t : null;
	};
	const pt = (c: Cell | null) => ({ x: c?.los.median ?? null, y: adm(c), n: c?.n ?? 0 });

	const rows = $derived(
		conds.map((g) => ({ g, all: pt(cell(g, ALL)), f: pt(cell(g, 'Female')), m: pt(cell(g, 'Male')) }))
	);
	const base = $derived(pt(cell(NON_CARDIAC, ALL)));
	const card = $derived(pt(cell(CARDIAC_ALL, ALL)));

	let w = $state(700);
	let h = $state(460);
	const m = { top: 24, right: 24, bottom: 50, left: 64 };
	const iw = $derived(Math.max(100, w - m.left - m.right));
	const ih = $derived(Math.max(100, h - m.top - m.bottom));
	const X = [3, 8]; // hours
	const sx = (v: number) => m.left + ((Math.max(X[0], Math.min(X[1], v)) - X[0]) / (X[1] - X[0])) * iw;
	const sy = (v: number) => m.top + (1 - v) * ih;
	const maxN = $derived(Math.max(...rows.map((r) => r.all.n), 1));
	const rad = (n: number, k = 1) => Math.max(7, Math.sqrt(n / maxN) * 38 * k);

	// tweened layout in data units: for each condition [womanX, womanY, manX, manY, size factor]
	const target = $derived(
		rows.map((r) => {
			const a = r.all;
			const split = step >= 1;
			const f = split && r.f.x != null && r.f.y != null ? r.f : a;
			const mm = split && r.m.x != null && r.m.y != null ? r.m : a;
			return [f.x ?? 0, f.y ?? 0, mm.x ?? 0, mm.y ?? 0, split ? 1.15 : 1];
		})
	);
	const tw = Tween.of(() => target, { duration: reduceMotion() ? 0 : 900, easing: cubicInOut });
	const short = (g: string) => g.replace(' / ischemia', '').replace(' / symptoms', '').replace('Other cardiovascular', 'Other CV');
	const diamond = (x: number, y: number, r: number) => `M${x},${y - r} L${x + r},${y} L${x},${y + r} L${x - r},${y} Z`;
</script>

<div class="title">Every heart condition on one map</div>
<div class="sub">
	<span>x = median stay · y = admitted · size = visits</span>
	{#if step >= 1}<span class="key"><svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="#475569" /></svg>Women</span>
		<span class="key"><svg width="12" height="12"><path d={diamond(6, 6, 5.5)} fill="#475569" /></svg>Men</span>{/if}
	<span class="hint">Click a bubble to follow that condition</span>
</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Heart conditions by median stay and admission rate, split by gender">
		<!-- quadrants against the non-cardiac baseline -->
		{#if base.x != null && base.y != null}
			<g class="fade" style:opacity={step >= 2 ? 1 : 0}>
				<!-- amber: longer stay but fewer admitted (the "long work-up, then home" corner) -->
				<rect x={sx(base.x)} y={sy(base.y)} width={m.left + iw - sx(base.x)} height={m.top + ih - sy(base.y)} fill="#fef3c7" opacity="0.7" />
				<!-- blue: shorter stay and more admitted (quick decision to admit) -->
				<rect x={m.left} y={m.top} width={sx(base.x) - m.left} height={sy(base.y) - m.top} fill="#e0f2fe" opacity="0.7" />
				<text x={m.left + iw - 8} y={m.top + 18} text-anchor="end" class="quad">Longer stay · more admitted</text>
				<text x={m.left + iw - 8} y={m.top + ih - 10} text-anchor="end" class="quad">Longer stay · fewer admitted</text>
				<text x={m.left + 8} y={m.top + 18} class="quad">Shorter stay · more admitted</text>
			</g>
		{/if}
		{#each [0, 0.25, 0.5, 0.75, 1] as t}
			<line x1={m.left} x2={m.left + iw} y1={sy(t)} y2={sy(t)} stroke="#eef2f7" />
			<text x={m.left - 8} y={sy(t) + 4} text-anchor="end" class="tick">{t * 100}%</text>
		{/each}
		{#each [3, 4, 5, 6, 7, 8] as t}
			<text x={sx(t)} y={m.top + ih + 18} text-anchor="middle" class="tick">{t} h</text>
		{/each}
		<text x={m.left + iw / 2} y={h - 6} text-anchor="middle" class="axis">Median time in the ED →</text>
		<text transform={`translate(14 ${m.top + ih / 2}) rotate(-90)`} text-anchor="middle" class="axis">Admitted to hospital →</text>

		<!-- reference points -->
		{#each [{ p: base, c: '#e87945', l: 'Non-cardiac' }, { p: card, c: '#2563eb', l: 'All cardiac' }] as ref}
			{#if ref.p.x != null && ref.p.y != null}
				<g role="presentation" onmousemove={(e) => showTip(e, [ref.l, `Median stay ${fmt1(ref.p.x)} h`, `Admitted ${pct(ref.p.y ?? 0)}`, `n ≈ ${fmtInt(ref.p.n)}`])} onmouseleave={hideTip}>
					<line x1={sx(ref.p.x)} x2={sx(ref.p.x)} y1={m.top} y2={m.top + ih} stroke={ref.c} stroke-dasharray="4 4" opacity="0.5" />
					<circle cx={sx(ref.p.x)} cy={sy(ref.p.y)} r="7" fill="#fff" stroke={ref.c} stroke-width="3" />
					<text x={sx(ref.p.x) + 10} y={sy(ref.p.y) - 9} class="ref" style:fill={ref.c}>{ref.l}</text>
				</g>
			{/if}
		{/each}

		{#each rows as r, i}
			{@const v = tw.current[i]}
			{@const col = COND_COLORS[r.g] ?? '#64748b'}
			{#if v && r.all.x != null}
				{@const fx = sx(v[0])} {@const fy = sy(v[1])} {@const mx = sx(v[2])} {@const my = sy(v[3])}
				<g class="cond" class:sel={filters.group === r.g} role="button" tabindex="0"
					aria-label={`${r.g}: follow this condition`}
					onclick={() => (filters.group = filters.group === r.g ? CARDIAC_ALL : r.g)}
					onkeydown={(e) => e.key === 'Enter' && (filters.group = filters.group === r.g ? CARDIAC_ALL : r.g)}
					onmousemove={(e) => showTip(e, step >= 1
						? [r.g, `Women: ${fmt1(r.f.x)} h · ${pct(r.f.y ?? 0)} admitted`, `Men: ${fmt1(r.m.x)} h · ${pct(r.m.y ?? 0)} admitted`,
							r.f.y != null && r.m.y != null ? `Gap (men − women): ${fmt1((r.m.y - r.f.y) * 100)} pts admitted` : '']
						: [r.g, `Median stay ${fmt1(r.all.x)} h`, `Admitted ${pct(r.all.y ?? 0)}`, `n ≈ ${fmtInt(r.all.n)}`])}
					onmouseleave={hideTip}>
					<line x1={fx} y1={fy} x2={mx} y2={my} stroke={col} stroke-width="3" opacity={step >= 1 ? 0.6 : 0} />
					<circle cx={fx} cy={fy} r={rad(step >= 1 ? r.f.n : r.all.n, v[4])} fill={col} fill-opacity="0.78" stroke="#fff" stroke-width="2" />
					{#if step >= 1}
						<path d={diamond(mx, my, rad(r.m.n, v[4]) * 1.15)} fill={col} fill-opacity="0.78" stroke="#fff" stroke-width="2" />
					{/if}
					<text x={Math.max(fx, mx) + rad(r.all.n, v[4]) + 6} y={(fy + my) / 2 + 4} class="lbl" style:fill={col}>{short(r.g)}</text>
				</g>
			{/if}
		{/each}
	</svg>
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.8rem; color: #64748b; margin-top: 4px; display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }
	.key { display: inline-flex; align-items: center; gap: 4px; font-weight: 700; color: #334155; }
	.hint { color: #2563eb; font-weight: 600; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; overflow: visible; }
	.tick { font-size: 11px; fill: #64748b; }
	.axis { font-size: 12px; font-weight: 700; fill: #334155; }
	.quad { font-size: 12px; font-weight: 700; fill: #92400e; opacity: 0.8; }
	.ref { font-size: 12px; font-weight: 800; }
	.lbl { font-size: 13px; font-weight: 800; paint-order: stroke; stroke: #fff; stroke-width: 4px; pointer-events: none; }
	.cond { cursor: pointer; outline: none; }
	.cond:hover circle, .cond:hover path, .cond.sel circle, .cond.sel path { fill-opacity: 1; stroke: #172033; }
	.fade { transition: opacity 0.6s; }
	line { transition: opacity 0.6s; }
</style>
