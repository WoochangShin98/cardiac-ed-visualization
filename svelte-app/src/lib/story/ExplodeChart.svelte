<!--
  Scene 5 graphic: "Cardiac" explodes into five conditions.
  step 0: cardiac vs non-cardiac · step 1: explode by condition (median stay) · step 2: admission rate
  step 3: click a condition -> it becomes the focus group for the whole page.
-->
<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut } from 'svelte/easing';
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, ALL, nz, fmt1, fmtInt, pct, type Cell, type Cube } from '#lib/cube.ts';
	import { filters, toggleFilter } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube, step }: { cube: Cube; step: number } = $props();

	let w = $state(700);
	let h = $state(420);
	const m = { top: 14, right: 70, bottom: 30, left: 190 };

	const groups = $derived([NON_CARDIAC, CARDIAC_ALL, ...cube.meta.dim_values.group.filter((g) => g !== ALL && g !== NON_CARDIAC && g !== CARDIAC_ALL)]);
	const metric = $derived(step >= 2 ? 'admit' : 'los');

	const admitRate = (c: Cell | null) => {
		const d = c?.dispo.map(nz) ?? [];
		const t = d.reduce((a, b) => a + b, 0);
		return t ? d[0] / t : 0;
	};
	const rows = $derived(
		groups.map((g) => {
			const c = storyCell(cube, g);
			return { g, c, los: c?.los.median ?? 0, admit: admitRate(c) };
		})
	);
	const val = (r: (typeof rows)[0]) => (metric === 'los' ? r.los : r.admit);
	const maxV = $derived(Math.max(0.001, ...rows.map(val)) * 1.12);

	const iw = $derived(Math.max(100, w - m.left - m.right));
	const ih = $derived(Math.max(100, h - m.top - m.bottom));
	const rowH = $derived(Math.min(92, ih / groups.length));
	const top = $derived(Math.max(0, (ih - groups.length * rowH) / 2));
	const bh = $derived(Math.min(44, rowH * 0.56));

	const geo = Tween.of(
		() =>
			rows.map((r, i) => {
				const exploded = step >= 1;
				const slot = i < 2 ? i : exploded ? i : 1;
				return { y: (top + slot * rowH + (i >= 2 && exploded ? 6 : 0)) / ih, w: val(r) / maxV, op: i < 2 || exploded ? 1 : 0 };
			}),
		{ duration: reduceMotion() ? 0 : 850, easing: cubicInOut }
	);

	const color = (g: string) => (g === NON_CARDIAC ? COLORS.baseline : g === filters.group ? COLORS.focus : g === CARDIAC_ALL ? '#7ea3ee' : '#94a3b8');
	const label = (r: (typeof rows)[0]) => (metric === 'los' ? `${fmt1(r.los)} h` : pct(r.admit));
</script>

<div class="title">{metric === 'los' ? 'Median length of stay' : 'Share of visits admitted to the hospital'}</div>
<div class="sub">{step >= 3 ? 'Click a condition to make it the focus group for the whole page' : 'Cardiac visits split into five diagnosis groups'}</div>

<div class="wrap" bind:clientWidth={w} bind:clientHeight={h}>
	<svg width={w} height={h} role="img" aria-label="Cardiac conditions compared">
		{#each geo.current as g0, i}
			{@const r = rows[i]}
			{@const gg = { ...g0, y: m.top + g0.y * ih, w: g0.w * iw }}
			{@const clickable = r.g !== NON_CARDIAC && step >= 1}
			<g style:opacity={gg.op} class="row" class:clickable class:sel={r.g === filters.group}
				role={clickable ? 'button' : 'presentation'}
				tabindex={clickable ? 0 : undefined}
				onclick={() => clickable && toggleFilter('group', r.g)}
				onkeydown={(e) => clickable && e.key === 'Enter' && toggleFilter('group', r.g)}
				onmousemove={(e) => showTip(e, [r.g, `Median stay ${fmt1(r.los)} h`, `Admitted ${pct(r.admit)}`, `n = ${fmtInt(r.c?.n)}`])}
				onmouseleave={hideTip}>
				<rect x="0" y={gg.y} width={w} height={rowH} fill="transparent" />
				<text x={i >= 2 ? 18 : 4} y={gg.y + rowH / 2 + 4} class="lbl" style:fill={r.g === filters.group ? COLORS.focus : '#172033'}>
					{r.g === NON_CARDIAC ? 'Non-cardiac' : r.g === CARDIAC_ALL ? 'All cardiac' : r.g}
				</text>
				<rect x={m.left} y={gg.y + (rowH - bh) / 2} width={Math.max(0, gg.w)} height={bh} rx="4" style:fill={color(r.g)} class="bar" />
				<text x={m.left + gg.w + 8} y={gg.y + rowH / 2 + 4} class="val">{label(r)}</text>
			</g>
		{/each}
	</svg>
</div>

<style>
	.title { font-size: 1.1rem; font-weight: 700; }
	.sub { font-size: 0.82rem; color: #64748b; margin-top: 4px; }
	.wrap { flex: 1 1 auto; min-height: 0; }
	svg { display: block; }
	.lbl { font-size: 13.5px; font-weight: 700; transition: fill 0.4s; }
	.val { font-size: 13px; font-weight: 700; fill: #334155; }
	.bar { transition: fill 0.5s ease; }
	.row { transition: opacity 0.4s; }
	.row.clickable { cursor: pointer; }
	.row:focus { outline: none; }
	.row:focus-visible .lbl { text-decoration: underline; }
	.row.clickable:hover .lbl { text-decoration: underline; }
</style>
