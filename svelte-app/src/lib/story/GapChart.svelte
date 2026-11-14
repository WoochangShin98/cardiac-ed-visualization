<!--
  Scene 2 graphic: length-of-stay distributions.
  step 0: non-cardiac bars grow in · step 1: focus bars + medians · step 2: highlight 12h+ tail
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { COLORS, NON_CARDIAC, nz, fmt1, pct, type Cell, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	let w = $state(700);
	let h = $state(420);
	const m = { top: 70, right: 16, bottom: 46, left: 44 };

	const shares = (c: Cell | null) => {
		const v = c?.los.hist.map(nz) ?? [];
		const t = v.reduce((a, b) => a + b, 0) || 1;
		return v.map((x) => x / t);
	};

	const focus = $derived(storyCell(cube, filters.group));
	const base = $derived(storyCell(cube, NON_CARDIAC));
	const fS = $derived(shares(focus));
	const bS = $derived(shares(base));
	const bins = $derived(cube.meta.los_bins);
	const maxShare = $derived(Math.max(0.05, ...fS, ...bS) * 1.1);

	const heights = Tween.of(
		() => ({
			b: bS.map((s) => (step >= 0 ? s : 0)),
			f: fS.map((s) => (step >= 1 ? s : 0))
		}),
		{ duration: reduceMotion() ? 0 : 750, easing: cubicOut }
	);

	const iw = $derived(Math.max(100, w - m.left - m.right));
	const ih = $derived(Math.max(100, h - m.top - m.bottom));
	const bw = $derived(iw / Math.max(1, bins.length));
	const y = (s: number) => m.top + ih - (s / maxShare) * ih;
	const xHours = (v: number) => m.left + (Math.min(v, 26) / 26) * iw;

	const tail = (s: number[]) => s.slice(6).reduce((a, b) => a + b, 0);
	const gap = $derived(
		focus?.los.median != null && base?.los.median != null ? focus.los.median - base.los.median : null
	);
</script>

<div class="title">How long do patients stay in the ED?</div>
<div class="sub">Share of visits by length of stay · 2-hour bins
	<span class="key"><i style:background={COLORS.baseline}></i>Non-cardiac</span>
	<span class="key" style:opacity={step >= 1 ? 1 : 0.3}><i style:background={COLORS.focus}></i>{filters.group}</span>
</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Length of stay distributions">
		{#each [0, 0.25, 0.5, 0.75, 1] as t}
			{@const v = t * maxShare}
			<line x1={m.left} x2={w - m.right} y1={y(v)} y2={y(v)} stroke={COLORS.grid} />
			<text x={m.left - 8} y={y(v) + 4} class="tick" text-anchor="end">{Math.round(v * 100)}%</text>
		{/each}

		{#each bins as label, i}
			{@const x0 = m.left + i * bw}
			{@const dim = step >= 2 && i < 6}
			<g class="bin" style:opacity={dim ? 0.18 : 1}
				role="presentation"
				onmousemove={(e) => showTip(e, [`${label} hours`, `Non-cardiac: ${pct(bS[i] ?? 0)}`, `${filters.group}: ${pct(fS[i] ?? 0)}`])}
				onmouseleave={hideTip}>
				<rect x={x0 + bw * 0.1} y={y(heights.current.b[i] ?? 0)} width={bw * 0.38} height={Math.max(0, m.top + ih - y(heights.current.b[i] ?? 0))} fill={COLORS.baseline} rx="2" />
				<rect x={x0 + bw * 0.52} y={y(heights.current.f[i] ?? 0)} width={bw * 0.38} height={Math.max(0, m.top + ih - y(heights.current.f[i] ?? 0))} fill={COLORS.focus} rx="2" />
				{#if i % 2 === 0 || bins.length < 10}
					<text x={x0} y={m.top + ih + 18} class="tick" text-anchor="middle">{label === '24+' ? '24' : label.split('-')[0]}</text>
				{/if}
			</g>
		{/each}
		<text x={m.left + iw / 2} y={h - 6} class="axis" text-anchor="middle">Hours in the ED</text>

		<g class="fade" style:opacity={step === 1 ? 1 : 0}>
			{#if base?.los.median != null && focus?.los.median != null}
				<line x1={xHours(base.los.median)} x2={xHours(base.los.median)} y1={m.top - 30} y2={m.top + ih} stroke={COLORS.baseline} stroke-width="2" stroke-dasharray="5 4" />
				<line x1={xHours(focus.los.median)} x2={xHours(focus.los.median)} y1={m.top - 30} y2={m.top + ih} stroke={COLORS.focus} stroke-width="2" stroke-dasharray="5 4" />
				<text x={xHours(focus.los.median) + 8} y={m.top - 36} class="callout">
					median {fmt1(focus.los.median)} h vs {fmt1(base.los.median)} h
					{#if gap != null}({gap >= 0 ? '+' : ''}{fmt1(gap)} h){/if}
				</text>
			{/if}
		</g>
		<g class="fade" style:opacity={step >= 2 ? 1 : 0}>
			<text x={m.left + 6 * bw + 8} y={m.top - 36} class="callout">
				12 h or longer: {pct(tail(fS))} vs {pct(tail(bS))}
			</text>
		</g>
	</svg>
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.82rem; color: #64748b; margin-top: 2px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
	.key { display: inline-flex; align-items: center; gap: 5px; font-weight: 600; color: #334155; transition: opacity 0.5s; }
	.key i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.tick { font-size: 11px; fill: #64748b; }
	.axis { font-size: 12px; font-weight: 600; fill: #475569; }
	.callout { font-size: 14px; font-weight: 700; fill: #172033; }
	.bin, .fade { transition: opacity 0.6s ease; }
</style>
