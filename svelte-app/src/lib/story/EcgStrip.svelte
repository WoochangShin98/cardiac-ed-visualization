<!--
  Two monitor strips that beat at each group's median triage heart rate (aggregated value).
  The waveform is a stylised PQRST shape; only the beat rate comes from the data.
-->
<script lang="ts">
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';

	let { cube }: { cube: Cube } = $props();

	const W = 520, H = 64, MID = 38, PX_PER_SEC = 110;
	const strips = $derived([
		{ name: filters.group === CARDIAC_ALL ? 'Cardiac' : filters.group, color: COLORS.focus, bpm: storyCell(cube, filters.group)?.vitals.heartrate?.median ?? null },
		{ name: 'Non-cardiac', color: COLORS.baseline, bpm: storyCell(cube, NON_CARDIAC)?.vitals.heartrate?.median ?? null }
	]);

	// one beat of width P (px), as polyline points
	const beat = (x: number, P: number) => {
		const f = (u: number, dy: number) => `${(x + u * P).toFixed(1)},${(MID - dy).toFixed(1)}`;
		return [f(0, 0), f(0.1, 0), f(0.14, 4), f(0.18, 0), f(0.26, 0), f(0.29, -4), f(0.32, 26), f(0.35, -10), f(0.38, 0), f(0.52, 0), f(0.6, 7), f(0.68, 0), f(1, 0)].join(' ');
	};
	const path = (bpm: number | null) => {
		if (!bpm) return '';
		const P = (60 / bpm) * PX_PER_SEC;
		const pts: string[] = [];
		for (let x = -P * 2; x < W * 2 + P; x += P) pts.push(beat(x, P));
		return pts.join(' ');
	};

	let elapsed = $state(0); // seconds
	// shift by a whole number of beats so the loop is seamless
	const off = (bpm: number | null) => (bpm ? (elapsed * PX_PER_SEC) % ((60 / bpm) * PX_PER_SEC) : 0);
	$effect(() => {
		if (reduceMotion()) return;
		let raf = 0, t0 = performance.now();
		const tick = (now: number) => {
			elapsed = (now - t0) / 1000;
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(raf);
	});
</script>

<div class="ecg">
	{#each strips as s}
		<div class="row">
			<div class="lbl"><span style:color={s.color}>{s.name}</span><b>{s.bpm ?? '–'}<small> bpm</small></b></div>
			<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img" aria-label={`${s.name}: median heart rate ${s.bpm} beats per minute`}>
				<rect width={W} height={H} rx="8" fill="#0f172a" />
				{#each [16, 32, 48] as gy}<line x1="0" x2={W} y1={gy} y2={gy} stroke="#1e293b" />{/each}
				<g transform={`translate(${-off(s.bpm)} 0)`}>
					<polyline points={path(s.bpm)} fill="none" stroke={s.color === COLORS.focus ? '#60a5fa' : '#fb923c'} stroke-width="2.2" stroke-linejoin="round" />
				</g>
				<!-- fade-in cursor like a monitor sweep -->
				<rect x={W - 30} y="0" width="30" height={H} fill="url(#ecgfade)" />
				<defs><linearGradient id="ecgfade" x1="0" x2="1"><stop offset="0" stop-color="#0f172a" stop-opacity="0" /><stop offset="1" stop-color="#0f172a" /></linearGradient></defs>
			</svg>
		</div>
	{/each}
	<p class="note">Beat rate = each group's median heart rate at triage. Waveform shape is illustrative.</p>
</div>

<style>
	.ecg { display: flex; flex-direction: column; gap: 6px; margin: 6px 0 10px; flex: 0 0 auto; }
	.row { display: grid; grid-template-columns: 150px 1fr; gap: 12px; align-items: center; }
	.lbl { display: flex; flex-direction: column; font-weight: 700; font-size: 0.85rem; }
	.lbl b { font-size: 1.5rem; color: #172033; font-variant-numeric: tabular-nums; }
	.lbl small { font-size: 0.75rem; color: #64748b; }
	svg { width: 100%; height: 42px; display: block; }
	.note { margin: 0; font-size: 0.75rem; color: #64748b; }
</style>
