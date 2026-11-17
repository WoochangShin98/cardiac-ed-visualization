<!--
  Scene 3 graphic: one comparison splits into five acuity rows.
  step 0: all visits · step 1: split by acuity · step 2: admitted only · step 3: discharged home only
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut } from 'svelte/easing';
	import { COLORS, NON_CARDIAC, ALL, fmt1, fmtInt, type Cell, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	let w = $state(700);
	let h = $state(420);
	const m = { top: 20, right: 70, bottom: 44, left: 96 };
	const levels = ['1', '2', '3', '4', '5'];
	const DISPO_BY_STEP = [ALL, ALL, 'Admitted', 'Home'];

	const dispo = $derived(DISPO_BY_STEP[Math.min(step, 3)] ?? ALL);
	const stats = (c: Cell | null) =>
		c && c.los.median != null
			? [c.los.p10 ?? 0, c.los.q1 ?? 0, c.los.median, c.los.q3 ?? 0, c.los.p90 ?? 0]
			: null;

	const maxX = $derived.by(() => {
		let mx = 8;
		for (const d of [ALL, 'Admitted', 'Home'])
			for (const a of [ALL, ...levels])
				for (const g of [filters.group, NON_CARDIAC]) mx = Math.max(mx, storyCell(cube, g, { acuity: a, dispo: d })?.los.p90 ?? 0);
		return Math.min(48, Math.ceil(mx / 4) * 4);
	});

	const iw = $derived(Math.max(100, w - m.left - m.right));
	const ih = $derived(Math.max(100, h - m.top - m.bottom));
	const rowH = $derived(ih / levels.length);
	const boxH = $derived(Math.max(14, Math.min(24, rowH * 0.2)));

	const cells = $derived(
		levels.map((a) => ({
			f: storyCell(cube, filters.group, { acuity: step === 0 ? ALL : a, dispo }),
			b: storyCell(cube, NON_CARDIAC, { acuity: step === 0 ? ALL : a, dispo })
		}))
	);

	// unified gender view in the tooltip: women and men side by side, no need to toggle
	const sexLine = (g: string, i: number) => {
		const o = { acuity: step === 0 ? ALL : levels[i], dispo };
		const f = storyCell(cube, g, { ...o, gender: 'Female' })?.los.median;
		const mm = storyCell(cube, g, { ...o, gender: 'Male' })?.los.median;
		if (f == null || mm == null) return 'Women / men: too few visits to compare';
		return `Women ${fmt1(f)} h · Men ${fmt1(mm)} h (gap ${f - mm >= 0 ? '+' : ''}${fmt1(f - mm)} h)`;
	};

	const geo = Tween.of(
		() =>
			cells.map((c, i) => {
				const f = stats(c.f);
				const b = stats(c.b);
				return {
					// y as a fraction of the plot height, so resizing never leaves rows stranded
					y: step === 0 ? 0.5 - 0.5 / levels.length : i / levels.length,
					op: (f || b) && !(step === 0 && i > 0) ? 1 : 0,
					fo: f ? 1 : 0,
					bo: b ? 1 : 0,
					f: f ?? [0, 0, 0, 0, 0],
					b: b ?? [0, 0, 0, 0, 0]
				};
			}),
		{ duration: reduceMotion() ? 0 : 800, easing: cubicInOut }
	);

	const x = (v: number) => m.left + (Math.min(v, maxX) / maxX) * iw;
	const ticks = $derived(Array.from({ length: maxX / 4 + 1 }, (_, i) => i * 4));
</script>

<div class="title">Length of stay by triage acuity</div>
<div class="sub">
	{#each [ALL, 'Admitted', 'Home'] as d, i}
		<span class="chip" class:on={dispo === d}>{i === 0 ? 'All visits' : d === 'Home' ? 'Discharged home' : 'Admitted'}</span>
	{/each}
	<span class="key"><i style:background={COLORS.focus}></i>{filters.group}</span>
	<span class="key"><i style:background={COLORS.baseline}></i>Non-cardiac</span>
</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Length of stay box plots by acuity">
		{#each ticks as t}
			<line x1={x(t)} x2={x(t)} y1={m.top} y2={m.top + ih} stroke={COLORS.grid} />
			<text x={x(t)} y={m.top + ih + 18} class="tick" text-anchor="middle">{t}{t === maxX ? '+' : ''}</text>
		{/each}
		<text x={m.left + iw / 2} y={h - 6} class="axis" text-anchor="middle">Hours in the ED · box = middle 50%, tick = median, line = 10th–90th pct</text>

		{#each geo.current as g0, i}
			{@const c = cells[i]}
			{@const g = { ...g0, y: m.top + g0.y * ih }}
			<g style:opacity={g.op}>
				<text x="4" y={g.y + rowH / 2 + 4} class="lbl">{step === 0 ? 'All visits' : `Acuity ${levels[i]}`}</text>
				{#if step > 0 && (i === 0 || i === 4)}
					<text x="4" y={g.y + rowH / 2 + 18} class="hint">{i === 0 ? 'most urgent' : 'least urgent'}</text>
				{/if}
				{#each [{ s: g.f, o: g.fo, col: COLORS.focus, dy: -boxH / 2 - 3, cell: c.f, name: filters.group }, { s: g.b, o: g.bo, col: COLORS.baseline, dy: boxH / 2 + 3, cell: c.b, name: NON_CARDIAC }] as b}
					{@const cy = g.y + rowH / 2 + b.dy}
					{#if b.o < 0.5}
						<text x={m.left + 6} y={cy + 4} class="hint">{b.name === NON_CARDIAC ? 'Non-cardiac' : 'Cardiac'}: too few visits to show</text>
					{/if}
					<g role="presentation" style:opacity={b.o}
						onmousemove={(e) => b.cell && showTip(e, [`${b.name} · ${step === 0 ? 'all acuities' : 'acuity ' + levels[i]}`, `Median ${fmt1(b.cell.los.median)} h (IQR ${fmt1(b.cell.los.q1)}–${fmt1(b.cell.los.q3)})`, `n = ${fmtInt(b.cell.los.n)}`, sexLine(b.name, i)])}
						onmouseleave={hideTip}>
						<line x1={x(b.s[0])} x2={x(b.s[4])} y1={cy} y2={cy} stroke={b.col} stroke-width="1.5" />
						<rect x={x(b.s[1])} y={cy - boxH / 2} width={Math.max(1, x(b.s[3]) - x(b.s[1]))} height={boxH} fill={b.col} fill-opacity="0.2" stroke={b.col} rx="3" />
						<line x1={x(b.s[2])} x2={x(b.s[2])} y1={cy - boxH / 2} y2={cy + boxH / 2} stroke={b.col} stroke-width="3.5" />
					</g>
					<text x={w - m.right + 8} y={cy + 4} class="val" fill={b.col} style:opacity={b.o}>{fmt1(b.s[2])} h</text>
				{/each}
			</g>
		{/each}
	</svg>
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.8rem; color: #64748b; margin-top: 6px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
	.chip { padding: 3px 10px; border-radius: 999px; border: 1px solid #cbd5e1; transition: all 0.4s; }
	.chip.on { background: #172b4d; color: #fff; border-color: #172b4d; }
	.key { display: inline-flex; align-items: center; gap: 5px; font-weight: 600; color: #334155; margin-left: 6px; }
	.key i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.tick { font-size: 11px; fill: #64748b; }
	.axis { font-size: 11.5px; font-weight: 600; fill: #475569; }
	.lbl { font-size: 13px; font-weight: 700; fill: #172033; }
	.hint { font-size: 10.5px; fill: #94a3b8; }
	.val { font-size: 12px; font-weight: 700; }
</style>
