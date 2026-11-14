<!--
  Scene 1 - "Do cardiac patients stay longer, even at the same acuity?"
  (Answers FP1 comment 1: compare within acuity + disposition, not only overall means.)
  Rows = acuity, two box plots per row: focus group vs non-cardiac.
-->
<script lang="ts">
	import { getCell, COLORS, NON_CARDIAC, ALL, fmt1, fmtInt, type Cube } from '#lib/cube.ts';
	import { filters, toggleFilter, setFilter } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	let width = $state(800);
	const rowsDef = [ALL, '1', '2', '3', '4', '5'];
	const margin = { top: 28, right: 90, bottom: 40, left: 120 };
	const rowH = 54;
	const boxH = 14;

	const rows = $derived(
		rowsDef.map((acuity) => ({
			acuity,
			focus: getCell(cube, filters, { acuity }),
			base: getCell(cube, filters, { acuity, group: NON_CARDIAC })
		}))
	);

	const maxX = $derived(
		Math.min(
			48,
			Math.ceil(
				Math.max(8, ...rows.flatMap((r) => [r.focus?.los.p90 ?? 0, r.base?.los.p90 ?? 0])) / 2
			) * 2
		)
	);
	const innerW = $derived(Math.max(200, width - margin.left - margin.right));
	const height = $derived(margin.top + rows.length * rowH + margin.bottom);
	const x = (v: number) => margin.left + (Math.min(v, maxX) / maxX) * innerW;
	const ticks = $derived(Array.from({ length: maxX / 2 + 1 }, (_, i) => i * 2).filter((t) => maxX <= 24 || t % 4 === 0));

	// Dynamic interpretation text - updates with every filter change.
	const summary = $derived.by(() => {
		const levels = rows.filter((r) => r.acuity !== ALL && r.focus?.los.median != null && r.base?.los.median != null);
		const longer = levels.filter((r) => r.focus!.los.median! > r.base!.los.median!);
		const all = rows[0];
		const diff = all.focus?.los.median != null && all.base?.los.median != null ? all.focus.los.median - all.base.los.median : null;
		return { longer: longer.length, compared: levels.length, diff };
	});

	function tipLines(label: string, c: NonNullable<(typeof rows)[0]['focus']>) {
		return [
			label,
			`Median ${fmt1(c.los.median)} h (IQR ${fmt1(c.los.q1)}–${fmt1(c.los.q3)} h)`,
			`10th–90th pct: ${fmt1(c.los.p10)}–${fmt1(c.los.p90)} h`,
			`n = ${fmtInt(c.los.n)} encounters`
		];
	}
</script>

<div class="controls">
	<span class="ctl-label">Show stays ending in:</span>
	{#each [ALL, 'Admitted', 'Home'] as d}
		<button class="seg" class:active={filters.dispo === d} onclick={() => setFilter('dispo', d)}>
			{d === ALL ? 'Any disposition' : d}
		</button>
	{/each}
</div>

<div class="chart" bind:clientWidth={width}>
	<svg {width} {height} role="img" aria-label="ED length of stay by triage acuity">
		{#each ticks as t}
			<line x1={x(t)} x2={x(t)} y1={margin.top - 6} y2={height - margin.bottom} stroke={COLORS.grid} />
			<text x={x(t)} y={height - margin.bottom + 18} class="tick" text-anchor="middle">{t}{t === maxX ? '+' : ''}</text>
		{/each}
		<text x={margin.left + innerW / 2} y={height - 6} class="axis" text-anchor="middle">ED length of stay (hours)</text>

		{#each rows as r, i}
			{@const y0 = margin.top + i * rowH}
			{@const selected = filters.acuity === r.acuity && r.acuity !== ALL}
			{#if selected}
				<rect x="0" y={y0 - 4} width={width} height={rowH - 4} fill="#eef4ff" rx="6" />
			{/if}
			{#if i === 1}
				<line x1="8" x2={width - 8} y1={y0 - 6} y2={y0 - 6} stroke="#cfd6e3" stroke-dasharray="3 3" />
			{/if}
			<g
				class="row-label"
				role="button"
				tabindex="0"
				onclick={() => r.acuity !== ALL && toggleFilter('acuity', r.acuity)}
				onkeydown={(e) => e.key === 'Enter' && r.acuity !== ALL && toggleFilter('acuity', r.acuity)}
			>
				<text x="12" y={y0 + rowH / 2 - 4} class="lbl" class:sel={selected}>
					{r.acuity === ALL ? 'All acuities' : `Acuity ${r.acuity}`}
				</text>
				<text x="12" y={y0 + rowH / 2 + 11} class="sub">
					{r.acuity === '1' ? 'most urgent' : r.acuity === '5' ? 'least urgent' : ''}
				</text>
			</g>

			{#each [{ c: r.focus, color: COLORS.focus, dy: 0, name: filters.group }, { c: r.base, color: COLORS.baseline, dy: boxH + 6, name: NON_CARDIAC }] as b}
				{@const cy = y0 + 8 + b.dy + boxH / 2}
				{#if b.c && b.c.los.median != null}
					<g
						role="presentation"
						onmousemove={(e) => showTip(e, tipLines(`${b.name} · ${r.acuity === ALL ? 'all acuities' : 'acuity ' + r.acuity}`, b.c!))}
						onmouseleave={hideTip}
					>
						<line x1={x(b.c.los.p10!)} x2={x(b.c.los.p90!)} y1={cy} y2={cy} stroke={b.color} stroke-width="1.5" />
						<rect x={x(b.c.los.q1!)} y={cy - boxH / 2} width={Math.max(1, x(b.c.los.q3!) - x(b.c.los.q1!))} height={boxH} fill={b.color} fill-opacity="0.22" stroke={b.color} rx="2" />
						<line x1={x(b.c.los.median)} x2={x(b.c.los.median)} y1={cy - boxH / 2} y2={cy + boxH / 2} stroke={b.color} stroke-width="3" />
					</g>
					<text x={width - margin.right + 8} y={cy + 4} class="val" fill={b.color}>{fmt1(b.c.los.median)} h</text>
				{:else}
					<text x={margin.left + 4} y={cy + 4} class="sub">too few encounters to show</text>
				{/if}
			{/each}
		{/each}
	</svg>
</div>

<p class="takeaway">
	{#if summary.diff != null}
		Overall, <b style:color={COLORS.focus}>{filters.group}</b> encounters have a median stay
		<b>{summary.diff >= 0 ? `${fmt1(summary.diff)} h longer` : `${fmt1(-summary.diff)} h shorter`}</b>
		than non-cardiac encounters.
	{/if}
	Comparing patients at the <i>same</i> triage acuity, the {filters.group} median is longer in
	<b>{summary.longer} of {summary.compared}</b> acuity levels — so the gap is
	{summary.longer >= Math.max(1, summary.compared - 1) ? 'not explained by acuity alone' : 'partly explained by acuity'}.
</p>

<style>
	.chart { width: 100%; }
	svg { display: block; overflow: visible; }
	.tick { font-size: 11px; fill: #64748b; }
	.axis { font-size: 12px; fill: #475569; font-weight: 600; }
	.lbl { font-size: 13px; font-weight: 700; fill: #172033; }
	.lbl.sel { fill: #2563eb; }
	.sub { font-size: 11px; fill: #94a3b8; }
	.val { font-size: 12px; font-weight: 700; }
	.row-label { cursor: pointer; }
	.row-label:hover .lbl { text-decoration: underline; }
</style>
