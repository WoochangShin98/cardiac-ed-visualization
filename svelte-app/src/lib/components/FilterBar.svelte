<!--
  Sticky filter bar - shows (and edits) the shared state every chart reads.
-->
<script lang="ts">
	import { DIM_LABELS, ALL, NON_CARDIAC, COLORS, getCell, fmtInt, type Cube, type Dim } from '#lib/cube.ts';
	import { filters, setFilter, resetFilters } from '#lib/state.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	const dims = $derived(
		(['group', 'acuity', 'dispo', 'gender', 'age'] as Dim[]).filter((d) => d !== 'age' || cube.meta.age_available)
	);
	const options = (d: Dim) =>
		cube.meta.dim_values[d].filter((v) => !(d === 'group' && (v === ALL || v === NON_CARDIAC)));

	const n = $derived(getCell(cube, filters)?.n ?? null);
	const nBase = $derived(getCell(cube, filters, { group: NON_CARDIAC })?.n ?? null);
</script>

<div class="bar">
	{#each dims as d}
		<label class:active={d !== 'group' && filters[d] !== ALL}>
			<span>{d === 'group' ? 'Focus group' : DIM_LABELS[d]}</span>
			<select value={filters[d]} onchange={(e) => setFilter(d, e.currentTarget.value)}>
				{#each options(d) as v}
					<option value={v}>{d === 'acuity' && v !== ALL && v !== 'Unknown' ? `Acuity ${v}` : v}</option>
				{/each}
			</select>
		</label>
	{/each}
	<button class="reset" onclick={resetFilters}>Reset</button>
	<div class="count">
		<span style:color={COLORS.focus}>■</span> {fmtInt(n)} &nbsp;
		<span style:color={COLORS.baseline}>■</span> {fmtInt(nBase)} non-cardiac
		<small>encounters match</small>
	</div>
</div>

<style>
	.bar {
		position: sticky; top: 0; z-index: 10;
		display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px;
		padding: 10px 14px; margin: 0 -14px 18px;
		background: rgba(244, 246, 250, 0.94); backdrop-filter: blur(6px);
		border-bottom: 1px solid #e2e8f0;
	}
	label { display: flex; flex-direction: column; gap: 3px; font-size: 11px; font-weight: 700; color: #64748b; }
	label.active span { color: #2563eb; }
	select { font: inherit; font-size: 13px; font-weight: 500; color: #172033; padding: 5px 8px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; }
	label.active select { border-color: #2563eb; background: #eef4ff; }
	.reset { font: inherit; font-size: 12px; padding: 6px 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; }
	.reset:hover { background: #f1f5f9; }
	.count { margin-left: auto; font-size: 13px; font-weight: 700; color: #172033; }
	.count small { font-weight: 500; color: #64748b; }
</style>
