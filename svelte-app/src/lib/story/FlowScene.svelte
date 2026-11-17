<!--
  The whole journey in one picture: arrival mode -> triage acuity -> outcome.
  Ribbon widths come from aggregated cells (group x acuity), each with its transport and disposition mix.
  Moving dots are illustrative: each dot samples a path from those shares (acuity first, then arrival and
  outcome given acuity), so the dot traffic matches the ribbon widths.
-->
<script lang="ts">
	import { COLORS, NON_CARDIAC, CARDIAC_ALL, nz, pct, type Cube } from '#lib/cube.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { storyCell, reduceMotion } from './story.ts';
	import { showTip, hideTip } from '#lib/tooltip.svelte.ts';

	let { cube }: { cube: Cube } = $props();

	let who = $state<'focus' | 'base'>('focus');
	const group = $derived(who === 'focus' ? filters.group : NON_CARDIAC);
	const color = $derived(who === 'focus' ? COLORS.focus : COLORS.baseline);
	const focusName = $derived(filters.group === CARDIAC_ALL ? 'Cardiac' : filters.group);

	const COLS = [
		{ title: 'Arrival', nodes: ['Ambulance', 'Walk-in', 'Other'] },
		{ title: 'Triage acuity', nodes: ['Acuity 1–2 (urgent)', 'Acuity 3', 'Acuity 4–5'] },
		{ title: 'Outcome', nodes: ['Admitted', 'Sent home', 'Other'] }
	];
	const ACU = [['1', '2'], ['3'], ['4', '5']];

	// per acuity bucket: n, transport shares (3), dispo shares (3)
	const model = $derived.by(() => {
		const rows = ACU.map((levels) => {
			let n = 0;
			const tr = [0, 0, 0], dp = [0, 0, 0];
			for (const a of levels) {
				const c = storyCell(cube, group, { acuity: a });
				if (!c) continue;
				n += c.n;
				const t = c.transport.map(nz); // AMBULANCE, WALK IN, HELICOPTER, OTHER, UNKNOWN
				const tt = [t[0] + t[2], t[1], t[3] + t[4]];
				const ts = tt.reduce((x, y) => x + y, 0) || 1;
				tt.forEach((v, i) => (tr[i] += (v / ts) * c.n));
				const d = c.dispo.map(nz);
				const ds = d.reduce((x, y) => x + y, 0) || 1;
				d.forEach((v, i) => (dp[i] += (v / ds) * c.n));
			}
			return { n, tr: tr.map((v) => (n ? v / n : 0)), dp: dp.map((v) => (n ? v / n : 0)) };
		});
		const total = rows.reduce((s, r) => s + r.n, 0) || 1;
		const pA = rows.map((r) => r.n / total);
		// link values as shares of all visits
		const L1 = [0, 1, 2].map((t) => rows.map((r, a) => pA[a] * r.tr[t])); // [transport][acuity]
		const L2 = rows.map((r, a) => r.dp.map((v) => pA[a] * v)); // [acuity][dispo]
		const col0 = L1.map((row) => row.reduce((s, v) => s + v, 0));
		const col2 = [0, 1, 2].map((d) => L2.reduce((s, row) => s + row[d], 0));
		return { rows, pA, L1, L2, sizes: [col0, pA, col2] };
	});

	// layout (viewBox 1000 x 470)
	const W = 1000, H = 470, TOP = 46, BOT = 20, NW = 18, PAD = 22;
	const XS = [150, 500, 850];
	const avail = H - TOP - BOT - PAD * 2;
	const nodePos = $derived(
		model.sizes.map((sz) => {
			let y = TOP;
			return sz.map((v) => {
				const h = Math.max(2, v * avail);
				const r = { y, h };
				y += h + PAD;
				return r;
			});
		})
	);
	// ribbons with stacked offsets
	const ribbons = $derived.by(() => {
		const out: { k: string; d: string; v: number; from: string; to: string; y0: number; y1: number; x0: number; x1: number }[] = [];
		const outOff = nodePos.map((col) => col.map((n) => n.y));
		const inOff = nodePos.map((col) => col.map((n) => n.y));
		const add = (c: number, i: number, j: number, v: number) => {
			const h = v * avail;
			const y0 = outOff[c][i] + h / 2, y1 = inOff[c + 1][j] + h / 2;
			outOff[c][i] += h; inOff[c + 1][j] += h;
			const x0 = XS[c] + NW / 2, x1 = XS[c + 1] - NW / 2, mx = (x0 + x1) / 2;
			out.push({
				k: `${c}-${i}-${j}`, v, y0, y1, x0, x1,
				from: COLS[c].nodes[i], to: COLS[c + 1].nodes[j],
				d: `M${x0},${y0} C${mx},${y0} ${mx},${y1} ${x1},${y1}`
			});
			return h;
		};
		const widths: number[] = [];
		for (let t = 0; t < 3; t++) for (let a = 0; a < 3; a++) widths.push(add(0, t, a, model.L1[t][a]));
		for (let a = 0; a < 3; a++) for (let d = 0; d < 3; d++) widths.push(add(1, a, d, model.L2[a][d]));
		return out.map((r, i) => ({ ...r, w: widths[i] }));
	});

	// ---------------- particles ----------------
	type Dot = { id: number; t: number; a: number; tr: number; dp: number; jitter: number[]; speed: number };
	let dots = $state<Dot[]>([]);
	let raf = 0, last = 0, acc = 0, nextId = 0, visible = false;
	let el: HTMLElement;

	const pick = (w: number[]) => {
		let r = Math.random() * (w.reduce((s, v) => s + v, 0) || 1);
		for (let i = 0; i < w.length; i++) { r -= w[i]; if (r <= 0) return i; }
		return w.length - 1;
	};
	function spawn(): Dot {
		const a = pick(model.pA);
		return { id: nextId++, t: 0, a, tr: pick(model.rows[a].tr), dp: pick(model.rows[a].dp), jitter: [Math.random() - 0.5, Math.random() - 0.5], speed: 0.16 + Math.random() * 0.06 };
	}
	const rib = (c: number, i: number, j: number) => ribbons.find((r) => r.k === `${c}-${i}-${j}`);
	const bez = (p0: number, p1: number, p2: number, p3: number, u: number) =>
		(1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * p3;
	function pos(d: Dot) {
		const first = d.t < 0.5;
		const r = first ? rib(0, d.tr, d.a) : rib(1, d.a, d.dp);
		if (!r) return null;
		const u = first ? d.t * 2 : (d.t - 0.5) * 2;
		const mx = (r.x0 + r.x1) / 2;
		const j = d.jitter[first ? 0 : 1] * Math.max(0, r.w - 4);
		return { x: bez(r.x0, mx, mx, r.x1, u), y: bez(r.y0, r.y0, r.y1, r.y1, u) + j };
	}
	function frame(now: number) {
		const dt = Math.min(0.05, (now - last) / 1000);
		last = now;
		if (visible) {
			acc += dt * 34; // dots per second
			const fresh: Dot[] = [];
			while (acc >= 1) { fresh.push(spawn()); acc -= 1; }
			dots = [...dots.filter((d) => d.t < 1).map((d) => ({ ...d, t: d.t + dt * d.speed })), ...fresh];
		}
		raf = requestAnimationFrame(frame);
	}
	$effect(() => {
		if (reduceMotion()) return;
		const obs = new IntersectionObserver((es) => { for (const e of es) visible = e.isIntersecting; }, { threshold: 0.2 });
		obs.observe(el);
		last = performance.now();
		raf = requestAnimationFrame(frame);
		return () => { obs.disconnect(); cancelAnimationFrame(raf); };
	});
	// restart the stream when the group changes
	$effect(() => { group; dots = []; });
</script>

<section class="flow" bind:this={el} aria-label="Patient flow from arrival to outcome">
	<div class="head">
		<span class="kicker">The whole journey in one picture</span>
		<h3>From the door to the decision</h3>
		<p class="sub">Ribbon width = share of visits. Each moving dot is an illustrative patient following those shares. Hover a ribbon for its value.</p>
		<div class="toggle" role="group" aria-label="Group to show">
			<button class:on={who === 'focus'} style:--c={COLORS.focus} onclick={() => (who = 'focus')}>{focusName}</button>
			<button class:on={who === 'base'} style:--c={COLORS.baseline} onclick={() => (who = 'base')}>Non-cardiac</button>
		</div>
	</div>

	<svg viewBox="0 0 {W} {H}" role="img" aria-label={`Flow of ${who === 'focus' ? focusName : 'non-cardiac'} visits from arrival mode to triage acuity to outcome`}>
		{#each COLS as col, c}
			<text x={XS[c]} y="22" text-anchor="middle" class="coltitle">{col.title}</text>
		{/each}
		{#each ribbons as r (r.k)}
			<path d={r.d} fill="none" stroke={color} stroke-opacity="0.18" stroke-width={Math.max(1, r.w)} class="ribbon"
				role="presentation"
				onmousemove={(e) => showTip(e, [`${r.from} → ${r.to}`, `${pct(r.v)} of visits`])} onmouseleave={hideTip} />
		{/each}
		{#each dots as d (d.id)}
			{@const p = pos(d)}
			{#if p}<circle cx={p.x} cy={p.y} r="3.2" fill={color} opacity="0.85" />{/if}
		{/each}
		{#each nodePos as col, c}
			{#each col as n, i}
				<rect x={XS[c] - NW / 2} y={n.y} width={NW} height={n.h} rx="4" fill="#172b4d" />
				{@const right = c >= 1}
				<text x={right ? XS[c] + NW / 2 + 8 : XS[c] - NW / 2 - 8} y={n.y + n.h / 2 + 4}
					text-anchor={right ? 'start' : 'end'} class="node halo">{COLS[c].nodes[i]}</text>
				<text x={right ? XS[c] + NW / 2 + 8 : XS[c] - NW / 2 - 8} y={n.y + n.h / 2 + 20}
					text-anchor={right ? 'start' : 'end'} class="share halo">{pct(model.sizes[c][i])}</text>
			{/each}
		{/each}
	</svg>
</section>

<style>
	.flow { max-width: 1100px; margin: 0 auto; padding: 10vh 28px 6vh; }
	.kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #b45309; }
	h3 { margin: 4px 0 6px; font-size: clamp(1.4rem, 2.6vw, 2rem); letter-spacing: -0.02em; }
	.sub { margin: 0 0 10px; color: #475569; }
	.toggle { display: inline-flex; gap: 4px; background: #fff; border: 1px solid #cbd5e1; border-radius: 999px; padding: 3px; margin-bottom: 14px; }
	.toggle button { font: inherit; font-size: 0.85rem; font-weight: 700; border: 0; background: transparent; color: #334155; border-radius: 999px; padding: 5px 14px; cursor: pointer; transition: all 0.3s; }
	.toggle button.on { background: var(--c); color: #fff; }
	svg { width: 100%; height: auto; display: block; background: #fff; border: 1px solid #e6ebf3; border-radius: 18px; box-shadow: 0 12px 34px rgba(23, 43, 77, 0.08); }
	.ribbon { transition: stroke-width 0.6s, stroke 0.6s; }
	.ribbon:hover { stroke-opacity: 0.35; }
	.coltitle { font-size: 14px; font-weight: 800; fill: #64748b; letter-spacing: 0.06em; text-transform: uppercase; }
	.node { font-size: 13.5px; font-weight: 700; fill: #172033; }
	.share { font-size: 12px; fill: #64748b; }
	.halo { paint-order: stroke; stroke: #fff; stroke-width: 4px; stroke-linejoin: round; pointer-events: none; }
</style>
