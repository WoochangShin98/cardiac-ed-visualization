<!--
  Vital signs at triage: focus group vs non-cardiac (median + IQR).
  Small multiples - one panel per vital sign. Reacts to all filters.
-->
<script lang="ts">
	import { getCell, COLORS, NON_CARDIAC, fmt1, fmtInt, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	const META: Record<string, { label: string; unit: string; normal: [number, number]; domain: [number, number] }> = {
		heartrate: { label: 'Heart rate', unit: 'bpm', normal: [60, 100], domain: [40, 140] },
		sbp: { label: 'Systolic BP', unit: 'mmHg', normal: [90, 120], domain: [80, 200] },
		dbp: { label: 'Diastolic BP', unit: 'mmHg', normal: [60, 80], domain: [40, 120] },
		o2sat: { label: 'O₂ saturation', unit: '%', normal: [95, 100], domain: [85, 100] },
		resprate: { label: 'Respiratory rate', unit: '/min', normal: [12, 20], domain: [8, 30] },
		temperature: { label: 'Temperature', unit: '°F', normal: [97, 99], domain: [95, 102] }
	};

	const focus = $derived(getCell(cube, filters));
	const base = $derived(getCell(cube, filters, { group: NON_CARDIAC }));
	const W = 220;
	const sx = (v: number, [a, b]: [number, number]) => 10 + ((Math.max(a, Math.min(b, v)) - a) / (b - a)) * (W - 20);
</script>

<div class="grid">
	{#each cube.meta.vitals as v}
		{@const m = META[v]}
		<div class="panel">
			<div class="title">{m.label} <small>{m.unit}</small></div>
			<svg width={W} height="62">
				<rect x={sx(m.normal[0], m.domain)} width={sx(m.normal[1], m.domain) - sx(m.normal[0], m.domain)} y="4" height="40" fill="#ecfdf5" />
				<text x={sx(m.normal[0], m.domain) + 3} y="13" class="norm">typical</text>
				{#each [{ c: focus, color: COLORS.focus, y: 20, name: filters.group }, { c: base, color: COLORS.baseline, y: 34, name: NON_CARDIAC }] as b}
					{@const s = b.c?.vitals[v]}
					{#if s && s.median != null}
						<g role="presentation" onmousemove={(e) => showTip(e, [`${b.name} · ${m.label}`, `Median ${fmt1(s.median)} ${m.unit}`, `IQR ${fmt1(s.q1)}–${fmt1(s.q3)}`, `n = ${fmtInt(s.n)}`])} onmouseleave={hideTip}>
							<line x1={sx(s.q1!, m.domain)} x2={sx(s.q3!, m.domain)} y1={b.y} y2={b.y} stroke={b.color} stroke-width="6" stroke-opacity="0.3" stroke-linecap="round" />
							<circle cx={sx(s.median, m.domain)} cy={b.y} r="5" fill={b.color} />
						</g>
					{/if}
				{/each}
				<text x="10" y="58" class="tick">{m.domain[0]}</text>
				<text x={W - 10} y="58" class="tick" text-anchor="end">{m.domain[1]}</text>
			</svg>
		</div>
	{/each}
</div>

<style>
	.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
	.panel { border: 1px solid #e8edf4; border-radius: 10px; padding: 8px 8px 2px; background: #fff; }
	.title { font-size: 13px; font-weight: 700; color: #172033; }
	.title small { font-weight: 500; color: #94a3b8; }
	.norm { font-size: 9px; fill: #059669; }
	.tick { font-size: 10px; fill: #94a3b8; }
</style>
