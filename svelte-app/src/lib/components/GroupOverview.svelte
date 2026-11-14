<!--
  Scene 3 - "Not all cardiac patients are alike." (Q2, FP1 comment 3)
  One row per patient group, four aligned mini-charts.
  Clicking a row makes it the focus group for EVERY chart on the page.
-->
<script lang="ts">
	import { getCell, COLORS, NON_CARDIAC, CARDIAC_ALL, ALL, fmt1, fmtInt, nz, pct, type Cube } from '#lib/cube.ts';
	import { filters, toggleFilter } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	const groups = $derived(cube.meta.dim_values.group.filter((g) => g !== ALL));

	const rows = $derived(
		groups.map((g) => {
			const c = getCell(cube, filters, { group: g });
			const cAnyDispo = getCell(cube, filters, { group: g, dispo: ALL });
			const d = cAnyDispo?.dispo.map(nz) ?? [];
			const dTotal = d.reduce((a, b) => a + b, 0);
			const ambulance = c ? nz(c.transport[0]) / Math.max(1, c.n) : null;
			return {
				g,
				c,
				admitted: dTotal ? d[0] / dTotal : null,
				ambulance
			};
		})
	);

	const maxN = $derived(Math.max(1, ...rows.map((r) => r.c?.n ?? 0)));
	const maxLos = $derived(Math.max(8, ...rows.map((r) => r.c?.los.q3 ?? 0)) * 1.05);

	const colorFor = (g: string) =>
		g === NON_CARDIAC ? COLORS.baseline : g === filters.group ? COLORS.focus : '#64748b';

	const W = 150; // width of each mini-chart
</script>

<div class="table" role="table" aria-label="Patient groups compared">
	<div class="head" role="row">
		<span>Patient group <small>(click a row)</small></span>
		<span>Encounters</span>
		<span>Length of stay<br /><small>median + IQR, hours</small></span>
		<span>Admitted</span>
		<span>Arrived by ambulance</span>
		<span>Median pain</span>
	</div>

	{#each rows as r}
		{@const sel = r.g === filters.group}
		{@const col = colorFor(r.g)}
		<div
			class="row"
			class:sel
			class:base={r.g === NON_CARDIAC}
			class:sub={r.g !== NON_CARDIAC && r.g !== CARDIAC_ALL}
			role="row"
			tabindex="0"
			onclick={() => r.g !== NON_CARDIAC && toggleFilter('group', r.g)}
			onkeydown={(e) => e.key === 'Enter' && r.g !== NON_CARDIAC && toggleFilter('group', r.g)}
		>
			<span class="name" style:color={col}>
				{r.g === NON_CARDIAC ? 'Non-cardiac (baseline)' : r.g}
			</span>

			{#if r.c}
				<span>
					<svg width={W} height="18">
						<rect width={(r.c.n / maxN) * W} height="12" y="3" fill={col} fill-opacity="0.75" rx="2" />
					</svg>
					<small>{fmtInt(r.c.n)}</small>
				</span>
				<span
					role="presentation"
					onmousemove={(e) => showTip(e, [r.g, `Median ${fmt1(r.c!.los.median)} h`, `IQR ${fmt1(r.c!.los.q1)}–${fmt1(r.c!.los.q3)} h`, `n = ${fmtInt(r.c!.los.n)}`])}
					onmouseleave={hideTip}
				>
					<svg width={W} height="18">
						<line x1="0" x2={W} y1="9" y2="9" stroke="#eef1f6" />
						<line x1={(nz(r.c.los.q1) / maxLos) * W} x2={(nz(r.c.los.q3) / maxLos) * W} y1="9" y2="9" stroke={col} stroke-width="5" stroke-opacity="0.35" stroke-linecap="round" />
						<circle cx={(nz(r.c.los.median) / maxLos) * W} cy="9" r="5" fill={col} />
					</svg>
					<small>{fmt1(r.c.los.median)} h</small>
				</span>
				<span>
					<svg width={W * 0.6} height="18">
						<rect width={W * 0.6} height="12" y="3" fill="#eef1f6" rx="2" />
						<rect width={(r.admitted ?? 0) * W * 0.6} height="12" y="3" fill={col} fill-opacity="0.75" rx="2" />
					</svg>
					<small>{r.admitted == null ? '—' : pct(r.admitted)}</small>
				</span>
				<span>
					<svg width={W * 0.6} height="18">
						<rect width={W * 0.6} height="12" y="3" fill="#eef1f6" rx="2" />
						<rect width={(r.ambulance ?? 0) * W * 0.6} height="12" y="3" fill={col} fill-opacity="0.75" rx="2" />
					</svg>
					<small>{r.ambulance == null ? '—' : pct(r.ambulance)}</small>
				</span>
				<span><b>{fmt1(r.c.pain.median)}</b><small> / 10</small></span>
			{:else}
				<span class="na" style="grid-column: span 5">too few encounters for the current filters</span>
			{/if}
		</div>
	{/each}
</div>

<p class="takeaway">
	Categories come from ED diagnosis titles; when a visit matches several, it is assigned to the most specific
	one (MI &gt; heart failure &gt; arrhythmia &gt; other &gt; chest pain). "Admitted" ignores the disposition filter.
</p>

<style>
	.table { display: grid; font-size: 13px; overflow-x: auto; }
	.head, .row {
		display: grid;
		grid-template-columns: minmax(170px, 1.3fr) 1.3fr 1.3fr 1fr 1fr 0.7fr;
		align-items: center;
		gap: 10px;
		padding: 8px 10px;
		min-width: 860px;
	}
	.head { font-weight: 700; color: #475569; font-size: 12px; border-bottom: 1px solid #e2e8f0; }
	.head small { font-weight: 500; color: #94a3b8; }
	.row { border-bottom: 1px solid #f1f5f9; cursor: pointer; border-radius: 8px; }
	.row:hover { background: #f8fafc; }
	.row.sel { background: #eef4ff; outline: 1.5px solid #bfd3fb; }
	.row.base { cursor: default; background: #fff7f2; }
	.row.sub .name { padding-left: 14px; }
	.name { font-weight: 700; }
	.row span { display: flex; align-items: center; gap: 6px; }
	small { color: #64748b; }
	.na { color: #94a3b8; font-style: italic; }
</style>
