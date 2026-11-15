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
	let hgt = $state(320);
	const longest = $derived(Math.max(...rows.map((r) => r.label.length), 8));
	// bars grow with the available box height so the card never looks empty
	const barH = $derived(Math.max(34, Math.min(92, ((hgt - 30) / Math.max(1, rows.length)) * 0.55)));
	const gap = $derived(Math.min(56, barH * 0.65));
	const block = $derived(rows.length * barH + (rows.length - 1) * gap);
	const top = $derived(Math.max(46, (hgt - block) / 2 - 10));

	const shares = $derived(
		rows.map((r) => {
			const t = r.parts.reduce((a, b) => a + b, 0) || 1;
			return r.parts.map((p) => p / t);
		})
	);
	const tw = Tween.of(() => shares, { duration: reduceMotion() ? 0 : 800, easing: cubicOut });
	// label column grows with the longest row label (capped at 40% of the width)
	const m = $derived({ left: Math.min(w * 0.4, Math.max(150, longest * 9.6 + 28)), right: 16 });
	const iw = $derived(Math.max(100, w - m.left - m.right));
	// labels for segments too thin to hold their own number
	function callouts(ri: number) {
		const sh = shares[ri] ?? [];
		const out: { pi: number; cx: number; tx: number; lift: number; text: string }[] = [];
		let acc = 0;
		let lastX = -Infinity;
		let lift = 0;
		sh.forEach((v, pi) => {
			const cx = m.left + (acc + v / 2) * iw;
			acc += v;
			if (v > 0.07 || v <= 0) return;
			const text = v < 0.01 ? '<1%' : pct(v);
			lift = cx - lastX < 44 ? lift + 16 : 0;
			lastX = cx;
			out.push({ pi, cx, tx: Math.min(cx, w - 22), lift, text });
		});
		return out;
	}
	const fs = $derived(Math.max(13, Math.min(16, barH * 0.26)));
</script>

<div class="legend">
	{#each partLabels as l, i}
		<span class:dim={highlight && !highlight.includes(i)}><i style:background={partColors[i]}></i>{l}</span>
	{/each}
</div>
<div class="wrap" bind:clientWidth={w} bind:clientHeight={hgt}>
	<svg width={w} height={hgt} role="img" aria-label="Stacked bar comparison">
		{#each rows as r, ri}
			{@const y = top + ri * (barH + gap)}
			<rect x="0" y={y + 6} width="5" height={barH - 12} rx="2" fill={r.color} />
			<text x="14" y={y + barH / 2 - 2} class="lbl" style:font-size="{fs + 1}px">{r.label}</text>
			<text x="14" y={y + barH / 2 + fs} class="n">n ≈ {fmtInt(r.n)}</text>
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
					<text x={m.left + (x0 + s / 2) * iw} y={y + barH / 2 + fs * 0.36} text-anchor="middle"
						style:font-size="{fs}px" class="val" class:dark={darkText.includes(pi)} style:opacity={dim ? 0.25 : 1}>{pct(s)}</text>
				{/if}
			{/each}
			<!-- small segments: label above the bar with a short leader line (staggered so they never overlap) -->
			{#each callouts(ri) as c}
				<g style:opacity={highlight && !highlight.includes(c.pi) ? 0.35 : 1} class="call">
					<line x1={c.cx} x2={c.cx} y1={y - 2} y2={y - 8 - c.lift} stroke="#94a3b8" stroke-width="1" />
					<text x={c.tx} y={y - 12 - c.lift} text-anchor="middle" style:font-size="{Math.max(12, fs - 2)}px" class="callval">{c.text}</text>
				</g>
			{/each}
		{/each}
	</svg>
</div>

<style>
	.legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.8rem; color: #334155; margin: 6px 0 12px; }
	.legend span { display: inline-flex; align-items: center; gap: 5px; transition: opacity 0.5s; }
	.legend span.dim { opacity: 0.35; }
	.legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
	.wrap { width: 100%; flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.lbl { font-size: 14px; font-weight: 700; fill: #172033; }
	.n { font-size: 11px; fill: #64748b; }
	.val { font-size: 12.5px; font-weight: 700; fill: #fff; pointer-events: none; transition: opacity 0.5s; }
	.val.dark { fill: #172033; }
	.seg { transition: opacity 0.5s; }
	.callval { font-weight: 700; fill: #334155; }
	.call { transition: opacity 0.5s; }
</style>
