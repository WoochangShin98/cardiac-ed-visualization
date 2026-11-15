<!--
  Scene 4 graphic: mean-pain bars MORPH into full 0-10 distributions.
  step 0: FP1-style mean bars · step 1: 100% stacked distributions · step 2: highlight severe pain (7-10)
  Every bar is built from 11 slices so the same marks can move between the two layouts.
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut } from 'svelte/easing';
	import { COLORS, PAIN_COLORS, NON_CARDIAC, nz, fmt1, fmtInt, pct, type Cell, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	let w = $state(700);
	let h = $state(420);
	const m = { top: 16, right: 16, bottom: 40, left: 70 };
	const levels = ['1', '2', '3', '4', '5'];
	const K = 11;

	const dist = (c: Cell | null) => {
		const v = c?.pain.dist.map(nz) ?? new Array(K).fill(0);
		const t = v.reduce((a, b) => a + b, 0) || 1;
		return v.map((x) => x / t);
	};

	const bars = $derived(
		levels.flatMap((a, ai) =>
			[
				{ g: filters.group, col: COLORS.focus, gi: 0 },
				{ g: NON_CARDIAC, col: COLORS.baseline, gi: 1 }
			].map((s) => {
				const c = storyCell(cube, s.g, { acuity: a });
				return { ...s, ai, a, c, mean: c?.pain.mean ?? 0, shares: dist(c), ok: !!c && c.pain.n > 0 };
			})
		)
	);

	const iw = $derived(Math.max(100, w - m.left - m.right));
	const ih = $derived(Math.max(100, h - m.top - m.bottom));

	const layout = $derived.by(() => {
		const out: { x: number; y: number; w: number; h: number }[] = [];
		const colW = iw / levels.length;
		const bw = Math.min(46, colW * 0.32);
		const rowH = ih / levels.length;
		const bh = Math.min(34, rowH * 0.36);
		for (const b of bars) {
			if (step === 0) {
				const H = (b.mean / 10) * ih;
				const x0 = m.left + b.ai * colW + colW / 2 - bw - 2 + b.gi * (bw + 4);
				for (let k = 0; k < K; k++)
					out.push({ x: (x0 - m.left) / iw, y: 1 - ((k + 1) * H) / K / ih, w: bw / iw, h: H / K / ih });
			} else {
				const y0 = m.top + b.ai * rowH + rowH / 2 - bh - 2 + b.gi * (bh + 4);
				let acc = 0;
				for (let k = 0; k < K; k++) {
					out.push({ x: acc, y: (y0 - m.top) / ih, w: Math.max(0, b.shares[k] - 0.6 / iw), h: bh / ih });
					acc += b.shares[k];
				}
			}
		}
		return out;
	});

	const geo = Tween.of(() => layout, { duration: reduceMotion() ? 0 : 900, easing: cubicInOut });

	const fillFor = (barIdx: number, k: number) => {
		const b = bars[barIdx];
		if (step === 0) return b.col;
		if (step >= 2 && k < 7) return '#e7eaf0';
		return PAIN_COLORS[k];
	};
	const severe = (s: number[]) => s.slice(7).reduce((a, b) => a + b, 0);
	const all = $derived({
		f: dist(storyCell(cube, filters.group)),
		b: dist(storyCell(cube, NON_CARDIAC))
	});
</script>

<div class="title">{step === 0 ? 'Average reported pain by triage acuity' : 'Full distribution of reported pain (0–10)'}</div>
<div class="sub">
	{#if step === 0}
		<span class="key"><i style:background={COLORS.focus}></i>{filters.group}</span>
		<span class="key"><i style:background={COLORS.baseline}></i>Non-cardiac</span>
	{:else}
		<span>Top bar = {filters.group} · bottom bar = non-cardiac</span>
		<span class="ramp">{#each PAIN_COLORS as c, i}<span style:background={step >= 2 && i < 7 ? '#e7eaf0' : c}>{i === 0 || i === 10 ? i : ''}</span>{/each}</span>
	{/if}
</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Pain by acuity">
		<g class="fade" style:opacity={step === 0 ? 1 : 0}>
			{#each [0, 2, 4, 6, 8, 10] as t}
				<line x1={m.left} x2={w - m.right} y1={m.top + ih - (t / 10) * ih} y2={m.top + ih - (t / 10) * ih} stroke={COLORS.grid} />
				<text x={m.left - 8} y={m.top + ih - (t / 10) * ih + 4} class="tick" text-anchor="end">{t}</text>
			{/each}
			{#each levels as a, i}
				<text x={m.left + (i + 0.5) * (iw / levels.length)} y={m.top + ih + 20} class="lbl" text-anchor="middle">Acuity {a}</text>
			{/each}
		</g>
		<g class="fade" style:opacity={step >= 1 ? 1 : 0}>
			{#each levels as a, i}
				<text x="4" y={m.top + (i + 0.5) * (ih / levels.length) + 4} class="lbl">Acuity {a}</text>
			{/each}
			{#each [0, 0.25, 0.5, 0.75, 1] as t}
				<text x={m.left + t * iw} y={m.top + ih + 20} class="tick" text-anchor="middle">{t * 100}%</text>
			{/each}
		</g>

		{#each bars as b, bi}
			{#if b.ok}
				{#each { length: K } as _, k}
					{@const r = geo.current[bi * K + k]}
					{#if r}
						<rect x={m.left + r.x * iw} y={m.top + r.y * ih} width={Math.max(0, r.w * iw)} height={Math.max(0, r.h * ih)} style:fill={fillFor(bi, k)} class="seg"
							role="presentation"
							onmousemove={(e) => showTip(e, step === 0
								? [`${b.g} · acuity ${b.a}`, `Mean pain ${fmt1(b.mean)} / 10`, `n = ${fmtInt(b.c?.pain.n)}`]
								: [`${b.g} · acuity ${b.a}`, `Pain ${k}: ${pct(b.shares[k])} of visits`, `n = ${fmtInt(b.c?.pain.n)}`])}
							onmouseleave={hideTip} />
					{/if}
				{/each}
			{/if}
		{/each}
	</svg>
</div>
<div class="foot" style:opacity={step >= 2 ? 1 : 0}>
	Severe pain (7–10): <b style:color={COLORS.focus}>{pct(severe(all.f))}</b> of {filters.group} vs
	<b style:color={COLORS.baseline}>{pct(severe(all.b))}</b> of non-cardiac visits
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.8rem; color: #64748b; margin-top: 6px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; min-height: 20px; }
	.key { display: inline-flex; align-items: center; gap: 5px; font-weight: 600; color: #334155; }
	.key i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
	.ramp { display: inline-flex; border-radius: 4px; overflow: hidden; }
	.ramp span { width: 16px; height: 14px; font-size: 9px; line-height: 14px; text-align: center; color: #fff; text-shadow: 0 0 2px #000a; transition: background 0.6s; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.seg { transition: fill 0.6s ease; }
	.fade, .foot { transition: opacity 0.5s ease; }
	.tick { font-size: 11px; fill: #64748b; }
	.lbl { font-size: 12.5px; font-weight: 700; fill: #172033; }
	.foot { font-size: 0.95rem; margin-top: 6px; }
</style>
