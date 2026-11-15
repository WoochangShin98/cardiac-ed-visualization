<!--
  Generic 100% stacked horizontal bars used by the Arrival, Triage and Disposition stages.
  rows: [{ label, color (group marker), parts: number[] (counts), n }]
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { fmtInt, pct } from '#lib/cube.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';
	import { reduceMotion } from './story.ts';

	type Row = { label: string; color: string; parts: number[]; n: number | null };
	let {
		rows,
		partLabels,
		partColors,
		highlight = null,
		darkText = []
	}: {
		rows: Row[];
		partLabels: string[];
		partColors: string[];
		highlight?: number[] | null;
		darkText?: number[];
	} = $props();

	let w = $state(600);
	const m = { left: 150, right: 16 };
	const barH = 34;
	const gap = 22;

	const shares = $derived(
		rows.map((r) => {
			const t = r.parts.reduce((a, b) => a + b, 0) || 1;
			return r.parts.map((p) => p / t);
		})
	);
	const tw = Tween.of(() => shares, { duration: reduceMotion() ? 0 : 800, easing: cubicOut });
	const iw = $derived(Math.max(100, w - m.left - m.right));
	const h = $derived(rows.length * (barH + gap) + 10);
</script>

<div class="legend">
	{#each partLabels as l, i}
		<span class:dim={highlight && !highlight.includes(i)}><i style:background={partColors[i]}></i>{l}</span>
	{/each}
</div>
<div class="wrap" bind:clientWidth={w}>
	<svg width={w} height={h} role="img" aria-label="Stacked bar comparison">
		{#each rows as r, ri}
			{@const y = ri * (barH + gap) + 4}
			<rect x="0" y={y + 6} width="5" height={barH - 12} rx="2" fill={r.color} />
			<text x="12" y={y + barH / 2 - 2} class="lbl">{r.label}</text>
			<text x="12" y={y + barH / 2 + 13} class="n">n ≈ {fmtInt(r.n)}</text>
			{#each tw.current[ri] ?? [] as s, pi}
				{@const x0 = (tw.current[ri] ?? []).slice(0, pi).reduce((a, b) => a + b, 0)}
				{@const dim = highlight && !highlight.includes(pi)}
				<rect
					x={m.left + x0 * iw} y={y} width={Math.max(0, s * iw - 1)} height={barH} rx="3"
					style:fill={partColors[pi]} style:opacity={dim ? 0.18 : 1} class="seg"
					role="presentation"
					onmousemove={(e) => showTip(e, [r.label, `${partLabels[pi]}: ${pct(shares[ri][pi])}`])}
					onmouseleave={hideTip}
				/>
				{#if s > 0.07}
					<text x={m.left + (x0 + s / 2) * iw} y={y + barH / 2 + 5} text-anchor="middle"
						class="val" class:dark={darkText.includes(pi)} style:opacity={dim ? 0.25 : 1}>{pct(s)}</text>
				{/if}
			{/each}
		{/each}
	</svg>
</div>

<style>
	.legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.8rem; color: #334155; margin: 6px 0 12px; }
	.legend span { display: inline-flex; align-items: center; gap: 5px; transition: opacity 0.5s; }
	.legend span.dim { opacity: 0.35; }
	.legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
	.wrap { width: 100%; }
	svg { display: block; }
	.lbl { font-size: 14px; font-weight: 700; fill: #172033; }
	.n { font-size: 11px; fill: #64748b; }
	.val { font-size: 12.5px; font-weight: 700; fill: #fff; pointer-events: none; transition: opacity 0.5s; }
	.val.dark { fill: #172033; }
	.seg { transition: opacity 0.5s; }
</style>
