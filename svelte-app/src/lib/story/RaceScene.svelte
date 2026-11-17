<!--
  "Two patients, one clock": the focus-group patient and a non-cardiac patient arrive together.
  A clock runs; each patient leaves the ED when the clock reaches their group's median length of stay.
  Uses only aggregated medians from the cube.
-->
<script lang="ts">
	import { untrack } from 'svelte';
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, fmt1, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';

	let { cube }: { cube: Cube } = $props();

	const name = $derived(filters.group === CARDIAC_ALL ? 'Cardiac' : filters.group);
	const lanes = $derived([
		{ label: name, color: COLORS.focus, med: storyCell(cube, filters.group)?.los.median ?? null },
		{ label: 'Non-cardiac', color: COLORS.baseline, med: storyCell(cube, NON_CARDIAC)?.los.median ?? null }
	]);
	const maxH = $derived(Math.max(4, Math.ceil(Math.max(...lanes.map((l) => l.med ?? 0)) + 1)));

	// clock state (hours)
	let t = $state(0);
	let running = $state(false);
	let el: HTMLElement;
	let raf = 0;
	const DUR = 7000; // ms for the whole clock

	function play() {
		cancelAnimationFrame(raf);
		if (reduceMotion()) { t = maxH; return; }
		t = 0; running = true;
		const t0 = performance.now();
		const tick = (now: number) => {
			t = Math.min(maxH, ((now - t0) / DUR) * maxH);
			if (t < maxH) raf = requestAnimationFrame(tick);
			else running = false;
		};
		raf = requestAnimationFrame(tick);
	}

	$effect(() => {
		let started = false;
		const obs = new IntersectionObserver((es) => {
			for (const e of es) if (e.isIntersecting && !started) { started = true; play(); }
		}, { threshold: 0.5 });
		obs.observe(el);
		return () => { obs.disconnect(); cancelAnimationFrame(raf); };
	});

	// replay when the focus group or gender changes
	$effect(() => {
		filters.group; filters.gender;
		untrack(() => { if (t > 0) play(); });
	});

	// geometry (viewBox units)
	const X0 = 330, X1 = 900;
	const xAt = (h: number) => X0 + (Math.min(h, maxH) / maxH) * (X1 - X0);
	const hh = (h: number) => `${Math.floor(h)}:${String(Math.floor((h % 1) * 60)).padStart(2, '0')}`;
	const gap = $derived(lanes[0].med != null && lanes[1].med != null ? lanes[0].med - lanes[1].med : null);
</script>

{#snippet figure(kind: 'f' | 'm', color: string, phase: number)}
	<g class="fig" class:p2={phase === 2}>
		{#if kind === 'f'}
			<path d="M-13 13 Q-13 -1 0 0 Q13 -1 13 13 L14 36 Q0 40 -14 36 Z" fill="#4b3621" />
		{/if}
		<circle cx="0" cy="12" r="11" fill="#f1c7a3" />
		{#if kind === 'm'}
			<path d="M-11 9 Q-10 -1 0 -1 Q10 -1 11 9 Q5 4 0 5 Q-5 4 -11 9 Z" fill="#2b1d12" />
			<rect x="-12" y="25" width="24" height="34" rx="8" fill={color} />
		{:else}
			<path d="M-8 9 Q0 -1 8 9" fill="none" stroke="#4b3621" stroke-width="3" />
			<path d="M-9 25 L9 25 L16 60 L-16 60 Z" fill={color} />
		{/if}
		<line class="leg l" x1="-5" y1="58" x2="-5" y2="72" stroke="#1e293b" stroke-width="6" stroke-linecap="round" />
		<line class="leg r" x1="5" y1="58" x2="5" y2="72" stroke="#1e293b" stroke-width="6" stroke-linecap="round" />
	</g>
{/snippet}

<section class="race" bind:this={el} aria-label="Two patients, one clock">
	<div class="head">
		<span class="kicker">Two patients, one clock</span>
		<h3>Same arrival time. Who leaves first?</h3>
	</div>

	<svg viewBox="0 0 1000 300" role="img"
		aria-label={`Median stay: ${lanes[0].label} ${fmt1(lanes[0].med)} hours, non-cardiac ${fmt1(lanes[1].med)} hours`}>
		<rect x="0" y="0" width="1000" height="300" rx="18" fill="#eef2f8" />

		<!-- clock -->
		<g transform="translate(90 150)">
			<circle r="62" fill="#fff" stroke="#172b4d" stroke-width="4" />
			{#each Array(12) as _, i}
				<line x1="0" y1="-52" x2="0" y2="-44" stroke="#94a3b8" stroke-width="3" transform={`rotate(${i * 30})`} />
			{/each}
			<line x1="0" y1="0" x2="0" y2="-34" stroke="#172b4d" stroke-width="5" stroke-linecap="round" transform={`rotate(${(t / 12) * 360})`} />
			<line x1="0" y1="0" x2="0" y2="-48" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" transform={`rotate(${(t % 1) * 360})`} />
			<circle r="5" fill="#172b4d" />
			<text y="92" text-anchor="middle" class="clock">{hh(t)} h</text>
		</g>

		<!-- hour ticks -->
		{#each Array(maxH + 1) as _, h}
			<line x1={xAt(h)} x2={xAt(h)} y1="40" y2="262" stroke="#d6dde8" stroke-dasharray={h % 2 ? '3 5' : ''} />
			{#if h % 2 === 0}<text x={xAt(h)} y="284" text-anchor="middle" class="tick">{h} h</text>{/if}
		{/each}

		<!-- exit door -->
		<g transform="translate(920 60)">
			<rect width="56" height="190" rx="6" fill="#fff" stroke="#9fb0c7" stroke-width="3" />
			<rect x="8" y="10" width="40" height="22" rx="3" fill="#16a34a" />
			<text x="28" y="26" text-anchor="middle" class="exit">EXIT</text>
		</g>

		{#each lanes as l, i}
			{@const y = 95 + i * 105}
			{@const done = l.med != null && t >= l.med}
			{@const x = l.med == null ? X0 : done ? 948 : xAt(t)}
			<line x1={X0} x2={X1} y1={y + 42} y2={y + 42} stroke="#c4cedd" stroke-width="3" />
			<rect x={X0} y={y + 38} width={Math.max(0, Math.min(xAt(t), l.med != null ? xAt(l.med) : X0) - X0)} height="8" rx="4" fill={l.color} opacity="0.85" />
			{#if l.med != null}
				<line x1={xAt(l.med)} x2={xAt(l.med)} y1={y - 22} y2={y + 50} stroke={l.color} stroke-width="2" stroke-dasharray="4 3" opacity={done ? 1 : 0.25} />
			{/if}
			<text x={X0 - 14} y={y + 8} text-anchor="end" class="lane" style:fill={l.color}>{l.label}</text>
			<!-- person -->
			<g class="person" class:walk={running && !done} style:transform={`translate(${x}px, ${y - 30}px)`} style:opacity={done ? 0.35 : 1}>
				{#if filters.gender === 'Female'}
					{@render figure('f', l.color, 0)}
				{:else if filters.gender === 'Male'}
					{@render figure('m', l.color, 0)}
				{:else}
					<!-- "All": a woman and a man walk out together -->
					<g transform="translate(-13 4) scale(0.88)">{@render figure('f', l.color, 1)}</g>
					<g transform="translate(13 4) scale(0.88)">{@render figure('m', l.color, 2)}</g>
				{/if}
			</g>
			{#if done}
				<text x={Math.min(xAt(l.med!) + 8, 860)} y={y - 26} class="out" style:fill={l.color}>Leaves at {fmt1(l.med)} h</text>
			{/if}
		{/each}
	</svg>

	<div class="foot">
		{#if gap != null && t >= maxH - 0.01}
			<p class="verdict">The {name.toLowerCase()} patient stays <b style:color={COLORS.focus}>{fmt1(Math.abs(gap))} h {gap >= 0 ? 'longer' : 'shorter'}</b> (median stay).</p>
		{:else}
			<p class="verdict muted">The clock runs at the median stay for each group…</p>
		{/if}
		<button onclick={play}>↻ Replay</button>
	</div>
</section>

<style>
	.race { max-width: 1100px; margin: 0 auto; padding: 4vh 28px 2vh; }
	.head { margin-bottom: 14px; }
	.kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #b45309; }
	h3 { margin: 4px 0 0; font-size: clamp(1.4rem, 2.6vw, 2rem); letter-spacing: -0.02em; }
	svg { width: 100%; height: auto; display: block; border-radius: 18px; box-shadow: 0 12px 34px rgba(23, 43, 77, 0.08); }
	.clock { font-size: 20px; font-weight: 800; fill: #172b4d; font-variant-numeric: tabular-nums; }
	.tick { font-size: 13px; fill: #64748b; }
	.exit { font-size: 12px; font-weight: 800; fill: #fff; }
	.lane { font-size: 15px; font-weight: 800; }
	.out { font-size: 14px; font-weight: 800; }
	.person { transition: opacity 0.6s; }
	.person.walk .leg.l { animation: swl 0.4s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 0; }
	.person.walk .leg.r { animation: swr 0.4s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 0; }
	/* the second walker steps out of phase so the pair looks natural */
	.person.walk .p2 .leg { animation-delay: -0.2s; }
	@keyframes swl { 50% { transform: rotate(20deg); } }
	@keyframes swr { 50% { transform: rotate(-20deg); } }
	.foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; }
	.verdict { margin: 0; font-size: 1.15rem; }
	.verdict.muted { color: #64748b; font-style: italic; }
	button { font: inherit; font-size: 0.85rem; font-weight: 700; border: 1px solid #cbd5e1; background: #fff; border-radius: 999px; padding: 6px 14px; cursor: pointer; }
</style>
