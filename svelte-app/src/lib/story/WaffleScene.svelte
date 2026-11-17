<!--
  "Out of 100 patients": 100 person icons per group, filled in by admission rate.
  Click a condition chip to change the focus group (same shared filter as the rest of the page).
-->
<script lang="ts">
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, ALL, nz, type Cube, type Cell } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';

	let { cube }: { cube: Cube } = $props();

	const conditions = $derived(cube.meta.dim_values.group.filter((g) => ![ALL, NON_CARDIAC].includes(g)));
	const share = (c: Cell | null) => {
		const d = c?.dispo.map(nz) ?? [];
		const t = d.reduce((a, b) => a + b, 0);
		return t ? [d[0] / t, d[1] / t] : [0, 0];
	};
	const label = (g: string) => (g === CARDIAC_ALL ? 'All cardiac' : g);
	const groups = $derived([
		{ g: filters.group, name: label(filters.group), color: COLORS.focus, s: share(storyCell(cube, filters.group)) },
		{ g: NON_CARDIAC, name: 'Non-cardiac', color: COLORS.baseline, s: share(storyCell(cube, NON_CARDIAC)) }
	]);
	// whole icons (sum to 100)
	const counts = (s: number[]) => {
		const a = Math.round(s[0] * 100);
		const h = Math.min(100 - a, Math.round(s[1] * 100));
		return { a, h, o: 100 - a - h };
	};

	// fill animation: icons appear one by one when the scene enters the viewport
	let shown = $state(0);
	let el: HTMLElement;
	let raf = 0;
	function run() {
		cancelAnimationFrame(raf);
		if (reduceMotion()) { shown = 100; return; }
		shown = 0;
		const t0 = performance.now();
		const step = (now: number) => {
			shown = Math.min(100, Math.floor((now - t0) / 14));
			if (shown < 100) raf = requestAnimationFrame(step);
		};
		raf = requestAnimationFrame(step);
	}
	$effect(() => {
		let started = false;
		const obs = new IntersectionObserver((es) => {
			for (const e of es) if (e.isIntersecting && !started) { started = true; run(); }
		}, { threshold: 0.4 });
		obs.observe(el);
		return () => { obs.disconnect(); cancelAnimationFrame(raf); };
	});

	const COLS = 10;
	const fillFor = (i: number, c: { a: number; h: number }, color: string) =>
		i >= shown ? '#e2e8f0' : i < c.a ? color : i < c.a + c.h ? '#cbd5e1' : '#f1f5f9';
</script>

<section class="waffle" bind:this={el} aria-label="Out of 100 patients">
	<div class="head">
		<span class="kicker">Out of 100 patients</span>
		<h3>How many are admitted to the hospital?</h3>
		<p class="sub">Each figure = 1 in 100 visits. <b>Colored</b> = admitted, <b class="g">gray</b> = sent home, outline = other. Pick a condition:</p>
		<div class="chips">
			{#each conditions as g}
				<button class:on={filters.group === g} onclick={() => { filters.group = g; run(); }}>{label(g)}</button>
			{/each}
		</div>
	</div>

	<div class="pair">
		{#each groups as gr}
			{@const c = counts(gr.s)}
			<div class="panel">
				<div class="big" style:color={gr.color}>{c.a}<span> / 100</span></div>
				<div class="name">{gr.name} · admitted</div>
				<svg viewBox="0 0 {COLS * 26} {10 * 34}" role="img" aria-label={`${gr.name}: ${c.a} of 100 admitted, ${c.h} sent home`}>
					{#each Array(100) as _, i}
						{@const x = (i % COLS) * 26 + 13}
						{@const y = Math.floor(i / COLS) * 34}
						{@const f = fillFor(i, c, gr.color)}
						<g transform={`translate(${x} ${y})`} class="pp">
							<circle cx="0" cy="8" r="6" fill={f} stroke={f === '#f1f5f9' ? '#cbd5e1' : 'none'} />
							<path d="M-8 30 Q-8 16 0 16 Q8 16 8 30 Z" fill={f} stroke={f === '#f1f5f9' ? '#cbd5e1' : 'none'} />
						</g>
					{/each}
				</svg>
			</div>
		{/each}
	</div>
</section>

<style>
	.waffle { max-width: 1100px; margin: 0 auto; padding: 8vh 28px 4vh; }
	.kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #b45309; }
	h3 { margin: 4px 0 6px; font-size: clamp(1.4rem, 2.6vw, 2rem); letter-spacing: -0.02em; }
	.sub { margin: 0 0 10px; color: #475569; }
	.sub .g { color: #94a3b8; }
	.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
	.chips button { font: inherit; font-size: 0.85rem; font-weight: 700; border: 1px solid #cbd5e1; background: #fff; color: #334155; border-radius: 999px; padding: 5px 12px; cursor: pointer; transition: all 0.3s; }
	.chips button.on { background: #2563eb; border-color: #2563eb; color: #fff; }
	.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
	.panel { background: #fff; border: 1px solid #e6ebf3; border-radius: 18px; padding: 18px 22px; box-shadow: 0 12px 30px rgba(23, 43, 77, 0.07); }
	.big { font-size: 2.6rem; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums; }
	.big span { font-size: 1rem; color: #94a3b8; font-weight: 700; }
	.name { font-weight: 700; color: #334155; margin: 4px 0 12px; }
	svg { width: 100%; height: auto; display: block; }
	.pp circle, .pp path { transition: fill 0.35s ease; }
	@media (max-width: 760px) { .pair { grid-template-columns: 1fr; } }
</style>
