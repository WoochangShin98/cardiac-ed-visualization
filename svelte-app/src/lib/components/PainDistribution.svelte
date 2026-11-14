<!--
  Scene 2 - "Averages hide the spread of reported pain."
  (Answers FP1 comment 2: show full 0-10 distribution + n, not only the mean.)
  Rows = acuity; each row has two 100% stacked bars (focus vs non-cardiac).
-->
<script lang="ts">
	import { getCell, COLORS, PAIN_COLORS, NON_CARDIAC, ALL, fmt1, fmtInt, nz, pct, type Cube, type Cell } from '#lib/cube.ts';
	import { filters, toggleFilter } from '#lib/state.svelte.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	let width = $state(800);
	const levels = ['1', '2', '3', '4', '5'];
	const margin = { top: 10, right: 165, bottom: 10, left: 120 };
	const barH = 16;
	const rowH = 52;

	const rows = $derived(
		levels.map((acuity) => ({
			acuity,
			focus: getCell(cube, filters, { acuity }),
			base: getCell(cube, filters, { acuity, group: NON_CARDIAC })
		}))
	);
	const innerW = $derived(Math.max(200, width - margin.left - margin.right));
	const height = $derived(margin.top + rows.length * rowH + margin.bottom);

	function segments(c: Cell | null) {
		if (!c) return [];
		const dist = c.pain.dist.map(nz);
		const total = dist.reduce((a, b) => a + b, 0);
		if (!total) return [];
		let acc = 0;
		return dist.map((v, level) => {
			const s = { level, share: v / total, start: acc / total, count: c.pain.dist[level] };
			acc += v;
			return s;
		});
	}

	const severeShare = (c: Cell | null) => {
		const segs = segments(c);
		return segs.length ? segs.filter((s) => s.level >= 7).reduce((a, s) => a + s.share, 0) : null;
	};

	const overall = $derived({
		focus: severeShare(getCell(cube, filters, { acuity: ALL })),
		base: severeShare(getCell(cube, filters, { acuity: ALL, group: NON_CARDIAC }))
	});
</script>

<div class="legend-row">
	<span>Reported pain:</span>
	<span class="ramp">
		{#each PAIN_COLORS as c, i}
			<span class="sw" style:background={c} title={`pain ${i}`}>{i === 0 || i === 5 || i === 10 ? i : ''}</span>
		{/each}
	</span>
	<span class="hint">0 = no pain · 10 = worst pain</span>
</div>

<div class="chart" bind:clientWidth={width}>
	<svg {width} {height} role="img" aria-label="Distribution of reported pain by triage acuity">
		{#each rows as r, i}
			{@const y0 = margin.top + i * rowH}
			{@const selected = filters.acuity === r.acuity}
			{#if selected}
				<rect x="0" y={y0 - 4} {width} height={rowH - 4} fill="#eef4ff" rx="6" />
			{/if}
			<text
				x="12" y={y0 + rowH / 2 - 2}
				class="lbl" class:sel={selected}
				role="button" tabindex="0"
				onclick={() => toggleFilter('acuity', r.acuity)}
				onkeydown={(e) => e.key === 'Enter' && toggleFilter('acuity', r.acuity)}
			>Acuity {r.acuity}</text>

			{#each [{ c: r.focus, name: filters.group, color: COLORS.focus, dy: 0 }, { c: r.base, name: NON_CARDIAC, color: COLORS.baseline, dy: barH + 4 }] as b}
				{@const y = y0 + 4 + b.dy}
				{@const segs = segments(b.c)}
				<rect x={margin.left - 8} y={y} width="4" height={barH} fill={b.color} rx="1" />
				{#if segs.length}
					{#each segs as s}
						<rect
							role="presentation"
							x={margin.left + s.start * innerW}
							y={y}
							width={Math.max(0, s.share * innerW - 0.5)}
							height={barH}
							fill={PAIN_COLORS[s.level]}
							onmousemove={(e) => showTip(e, [
								`${b.name} · acuity ${r.acuity}`,
								`Pain ${s.level}: ${pct(s.share)} of encounters`,
								s.count == null ? `(fewer than ${cube.meta.min_cell_size} - suppressed)` : `${fmtInt(s.count)} encounters`
							])}
							onmouseleave={hideTip}
						/>
					{/each}
					<text x={width - margin.right + 8} y={y + barH - 3} class="val">
						median {fmt1(b.c!.pain.median)} · n={fmtInt(b.c!.pain.n)}
					</text>
				{:else}
					<text x={margin.left + 4} y={y + barH - 3} class="sub">too few encounters to show</text>
				{/if}
			{/each}
		{/each}
	</svg>
</div>

<p class="takeaway">
	{#if overall.focus != null && overall.base != null}
		Across all acuity levels, <b>{pct(overall.focus)}</b> of
		<b style:color={COLORS.focus}>{filters.group}</b> encounters report severe pain (7–10) vs.
		<b>{pct(overall.base)}</b> of <b style:color={COLORS.baseline}>non-cardiac</b> encounters.
	{/if}
	Each row shows the whole distribution, so two groups with the same average can still look very different.
</p>

<style>
	.chart { width: 100%; }
	svg { display: block; }
	.lbl { font-size: 13px; font-weight: 700; fill: #172033; cursor: pointer; }
	.lbl:hover { text-decoration: underline; }
	.lbl.sel { fill: #2563eb; }
	.val { font-size: 11px; fill: #475569; }
	.sub { font-size: 11px; fill: #94a3b8; }
	.legend-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 12px; color: #475569; margin-bottom: 10px; }
	.ramp { display: inline-flex; border-radius: 4px; overflow: hidden; border: 1px solid #e2e8f0; }
	.sw { width: 22px; height: 18px; font-size: 10px; line-height: 18px; text-align: center; color: #fff; text-shadow: 0 0 2px #0008; }
	.hint { color: #94a3b8; }
</style>
