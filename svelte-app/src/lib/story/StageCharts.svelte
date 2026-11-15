<!--
  Graphics for the new journey stages, driven by the scroll step:
  - kind="arrival":  step 0 = how patients arrive (transport), step 1 = vital signs at triage
  - kind="acuity":   triage acuity distribution (step 1 highlights acuity 1-2)
  - kind="dx":       number of recorded diagnoses (step 0 = all visits, step 1 = split by disposition)
-->
<script lang="ts">
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, nz, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell } from './story.ts';
	import StackBars from './StackBars.svelte';
	import VitalsPanel from '#lib/components/VitalsPanel.svelte';

	let { cube, step, kind }: { cube: Cube; step: number; kind: 'arrival' | 'acuity' | 'dx' } = $props();

	const name = (g: string) => (g === CARDIAC_ALL ? 'Cardiac' : g);
	const groups = $derived([
		{ g: filters.group, label: name(filters.group), color: COLORS.focus },
		{ g: NON_CARDIAC, label: 'Non-cardiac', color: COLORS.baseline }
	]);

	// --- arrival: ambulance / walk-in / other -------------------------------
	const transportRows = $derived(
		groups.map(({ g, label, color }) => {
			const c = storyCell(cube, g);
			const t = c?.transport.map(nz) ?? [0, 0, 0, 0, 0];
			// levels: AMBULANCE, WALK IN, HELICOPTER, OTHER, UNKNOWN
			return { label, color, n: c?.n ?? null, parts: [t[0] + t[2], t[1], t[3] + t[4]] };
		})
	);

	// --- triage acuity ----------------------------------------------------------
	const acuityRows = $derived(
		groups.map(({ g, label, color }) => ({
			label, color,
			n: storyCell(cube, g)?.n ?? null,
			parts: ['1', '2', '3', '4', '5'].map((a) => storyCell(cube, g, { acuity: a })?.n ?? 0)
		}))
	);

	// --- diagnosis count ---------------------------------------------------------
	const dxParts = (c: ReturnType<typeof storyCell>) => {
		const d = c?.dx.map(nz) ?? [0, 0, 0, 0, 0, 0, 0];
		// labels: 0, 1, 2, 3, 4, 5-7, 8+  ->  1 | 2 | 3 | 4+
		return [d[0] + d[1], d[2], d[3], d[4] + d[5] + d[6]];
	};
	const dxRows = $derived(
		step === 0
			? groups.map(({ g, label, color }) => {
					const c = storyCell(cube, g);
					return { label, color, n: c?.n ?? null, parts: dxParts(c) };
				})
			: ['Admitted', 'Home'].flatMap((dispo) =>
					groups.map(({ g, label, color }) => {
						const c = storyCell(cube, g, { dispo });
						return { label: `${label} · ${dispo === 'Home' ? 'sent home' : 'admitted'}`, color, n: c?.n ?? null, parts: dxParts(c) };
					})
				)
	);
</script>

{#if kind === 'arrival'}
	{#if step === 0}
		<div class="title">How do patients arrive at the ED?</div>
		<div class="sub">Share of visits by arrival mode</div>
		<StackBars rows={transportRows} partLabels={['Ambulance / helicopter', 'Walk-in', 'Other / unknown']}
			partColors={['#b91c1c', '#94a3b8', '#e2e8f0']} highlight={[0]} darkText={[2]} />
	{:else}
		<div class="title">Vital signs at triage</div>
		<div class="sub">Median (dot) and middle 50% (bar); green band = typical adult range. Hover for exact values.</div>
		<VitalsPanel {cube} />
	{/if}
{:else if kind === 'acuity'}
	<div class="title">How urgent is each visit at triage?</div>
	<div class="sub">Share of visits by triage acuity · 1 = most urgent</div>
	<StackBars rows={acuityRows} partLabels={['Acuity 1', 'Acuity 2', 'Acuity 3', 'Acuity 4', 'Acuity 5']}
		partColors={['#7f1d1d', '#dc2626', '#f59e0b', '#fcd34d', '#fef3c7']}
		highlight={step >= 1 ? [0, 1] : null} darkText={[2, 3, 4]} />
{:else}
	<div class="title">How many diagnoses are recorded per visit?</div>
	<div class="sub">{step === 0 ? 'Share of visits by number of distinct diagnoses' : 'Split by disposition: admitted vs. sent home'}</div>
	<StackBars rows={dxRows} partLabels={['0–1 diagnosis', '2', '3', '4 or more']}
		partColors={['#e0e7ff', '#a5b4fc', '#6366f1', '#3730a3']} highlight={[2, 3]} darkText={[0, 1]} />
{/if}

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.82rem; color: #64748b; margin-top: 2px; }
</style>
