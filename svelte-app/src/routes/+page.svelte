<script lang="ts">
	import { onMount } from 'svelte';
	import { asset } from '$app/paths';
	import { COLORS, CARDIAC_ALL, NON_CARDIAC, ALL, nz, fmt1, pct, type Cell, type Cube } from '#lib/cube.ts';
	import { filters, resetFilters } from '#lib/state.svelte.ts';
	import { tip } from '#lib/tooltip.svelte.ts';
	import { storyCell } from '#lib/story/story.ts';

	import Hero from '#lib/story/Hero.svelte';
	import StoryScene from '#lib/story/StoryScene.svelte';
	import GapChart from '#lib/story/GapChart.svelte';
	import SplitChart from '#lib/story/SplitChart.svelte';
	import MorphChart from '#lib/story/MorphChart.svelte';
	import ExplodeChart from '#lib/story/ExplodeChart.svelte';
	import JourneyStepper from '#lib/story/JourneyStepper.svelte';
	import PatientScene from '#lib/story/PatientScene.svelte';
	import StageCharts from '#lib/story/StageCharts.svelte';

	import FilterBar from '#lib/components/FilterBar.svelte';
	import LosByAcuity from '#lib/components/LosByAcuity.svelte';
	import PainDistribution from '#lib/components/PainDistribution.svelte';
	import GroupOverview from '#lib/components/GroupOverview.svelte';
	import VitalsPanel from '#lib/components/VitalsPanel.svelte';

	let cube = $state<Cube | null>(null);
	let error = $state('');

	onMount(async () => {
		try {
			// Aggregated summaries only - built by src/build_web_aggregates.py
			const res = await fetch(asset('data/ed_cube.json'));
			if (!res.ok) throw new Error(`Could not load ed_cube.json (HTTP ${res.status}). Run src/build_web_aggregates.py first.`);
			cube = await res.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data.';
		}
	});

	// ---------- numbers used in the narration (all computed from the cube) ----------
	const share = (arr: (number | null)[], from: number) => {
		const v = arr.map(nz);
		const t = v.reduce((a, b) => a + b, 0) || 1;
		return v.slice(from).reduce((a, b) => a + b, 0) / t;
	};
	const admit = (c: Cell | null) => {
		const d = c?.dispo.map(nz) ?? [];
		const t = d.reduce((a, b) => a + b, 0);
		return t ? d[0] / t : 0;
	};
	const sexWord = $derived(filters.gender === 'Female' ? 'female ' : filters.gender === 'Male' ? 'male ' : '');
	const G = $derived(sexWord + (filters.group === CARDIAC_ALL ? 'cardiac' : filters.group));
	const Gc = $derived(G.charAt(0).toUpperCase() + G.slice(1));

	const N = $derived.by(() => {
		if (!cube) return null;
		const cb = cube;
		const f = storyCell(cb, filters.group);
		const b = storyCell(cb, NON_CARDIAC);
		const kOfN = (dispo: string) => {
			let k = 0, n = 0;
			for (const a of ['1', '2', '3', '4', '5']) {
				const x = storyCell(cb, filters.group, { acuity: a, dispo })?.los.median;
				const y = storyCell(cb, NON_CARDIAC, { acuity: a, dispo })?.los.median;
				if (x != null && y != null) { n++; if (x > y) k++; }
			}
			return { k, n };
		};
		const conds = cb.meta.dim_values.group
			.filter((g) => ![ALL, NON_CARDIAC, CARDIAC_ALL].includes(g))
			.map((g) => ({ g, c: storyCell(cb, g) }))
			.filter((x) => x.c);
		const acu12 = (g: string) => {
			const tot = ['1', '2', '3', '4', '5'].reduce((a, x) => a + (storyCell(cb, g, { acuity: x })?.n ?? 0), 0) || 1;
			return ((storyCell(cb, g, { acuity: '1' })?.n ?? 0) + (storyCell(cb, g, { acuity: '2' })?.n ?? 0)) / tot;
		};
		const dx3 = (g: string, dispo: string) => {
			const c = storyCell(cb, g, { dispo });
			return c ? share(c.dx, 3) : 0; // dx labels: 0,1,2,3,... -> index 3 = "3"
		};
		const home = (c: Cell | null) => {
			const d = c?.dispo.map(nz) ?? [];
			const t = d.reduce((a, x) => a + x, 0);
			return t ? d[1] / t : 0;
		};
		const byLos = [...conds].sort((p, q) => nz(p.c!.los.median) - nz(q.c!.los.median));
		const byAdm = [...conds].sort((p, q) => admit(p.c) - admit(q.c));
		return {
			losF: f?.los.median, losB: b?.los.median,
			gap: f?.los.median != null && b?.los.median != null ? f.los.median - b.los.median : null,
			tailF: f ? share(f.los.hist, 6) : 0, tailB: b ? share(b.los.hist, 6) : 0,
			kAll: kOfN(ALL), kAdm: kOfN('Admitted'), kHome: kOfN('Home'),
			sevF: f ? share(f.pain.dist, 7) : 0, sevB: b ? share(b.pain.dist, 7) : 0,
			meanF: f?.pain.mean, meanB: b?.pain.mean,
			losLo: byLos[0], losHi: byLos[byLos.length - 1],
			admLo: byAdm[0], admHi: byAdm[byAdm.length - 1],
			// journey-stage numbers
			ambF: f ? (nz(f.transport[0]) + nz(f.transport[2])) / Math.max(1, f.n) : 0,
			ambB: b ? (nz(b.transport[0]) + nz(b.transport[2])) / Math.max(1, b.n) : 0,
			acu12F: acu12(filters.group), acu12B: acu12(NON_CARDIAC),
			sbpF: f?.vitals.sbp?.median, sbpB: b?.vitals.sbp?.median,
			hrF: f?.vitals.heartrate?.median, hrB: b?.vitals.heartrate?.median,
			admF: admit(f), admB: admit(b),
			homeF: home(f),
			dx3F: f ? share(f.dx, 3) : 0, dx3B: b ? share(b.dx, 3) : 0, // index 3 = "3 diagnoses"
			dx3HomeF: dx3(filters.group, 'Home'), dx3HomeB: dx3(NON_CARDIAC, 'Home'),
			total: cb.meta.total_encounters,
			// hero numbers are always for everyone (not affected by the gender switch)
			cardiac: storyCell(cb, CARDIAC_ALL, { gender: ALL })?.n ?? 0,
			losC: storyCell(cb, CARDIAC_ALL, { gender: ALL })?.los.median ?? 0,
			losNAll: storyCell(cb, NON_CARDIAC, { gender: ALL })?.los.median ?? 0
		};
	});

	const mostly = (x: { k: number; n: number }) => x.n > 0 && x.k >= Math.max(1, x.n - 1);
	const few = (x: { k: number; n: number }) => x.k <= Math.floor(x.n / 2);
	const verdict = (x: { k: number; n: number }) =>
		mostly(x) ? 'urgency alone does <b>not</b> explain the gap' : 'so urgency explains only part of the picture';

	// Scene 3 conclusion depends on where the gap actually lives.
	const admText = $derived(
		N ? (few(N.kAdm)
			? `Only patients <b>admitted</b> to the hospital: longer in just <b>${N.kAdm.k} of ${N.kAdm.n}</b> levels — once admitted, ${G} patients move through the ED about as fast as everyone else.`
			: `Only patients <b>admitted</b> to the hospital: still longer in <b>${N.kAdm.k} of ${N.kAdm.n}</b> levels.`) : ''
	);
	const homeText = $derived(
		N ? (few(N.kAdm) && mostly(N.kHome)
			? `Only patients <b>discharged home</b>: longer in <b>${N.kHome.k} of ${N.kHome.n}</b> levels. The extra time comes mainly from ${G} patients who are eventually <b>sent home</b> — one possible reason is the long work-up needed to rule out a heart problem.`
			: mostly(N.kHome) && mostly(N.kAdm)
				? `Only patients <b>discharged home</b>: longer in <b>${N.kHome.k} of ${N.kHome.n}</b> levels. The pattern holds whichever way the visit ends.`
				: `Only patients <b>discharged home</b>: longer in <b>${N.kHome.k} of ${N.kHome.n}</b> levels.`) : ''
	);
	const painText = $derived(
		N ? `Looking only at <b>severe pain (7–10)</b>: <b class="c">${pct(N.sevF)}</b> of ${G} visits versus <b class="n">${pct(N.sevB)}</b> of non-cardiac visits${N.sevF < N.sevB ? ' — heart problems do not always hurt the most' : ''}. Hover any bar for its sample size.` : ''
	);
	const chestLink = $derived(
		N && N.losHi?.g === N.admLo?.g
			? ` ${N.losHi?.g} visits stay the longest yet are admitted least often — the same "long stay, then home" pattern we just saw.`
			: ''
	);
</script>

<svelte:head>
	<title>Cardiac Patients in the ED | CSCI 5609</title>
	<meta name="description" content="How do cardiac patients' emergency department experiences differ from non-cardiac patients? A scrollytelling exploration of MIMIC-IV-ED (aggregated)." />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
</svelte:head>

{#if error}
	<p class="error">{error}</p>
{:else if !cube || !N}
	<p class="status">Loading…</p>
{:else}
	<Hero total={N.total} cardiac={N.cardiac} losC={N.losC} losN={N.losNAll} />

	<div id="story" class="story">
		<JourneyStepper stages={[
			{ id: 'stage-arrival', label: 'Arrival' },
			{ id: 'stage-triage', label: 'Triage' },
			{ id: 'stage-stay', label: 'ED stay' },
			{ id: 'stage-dispo', label: 'Disposition' },
			{ id: 'explore', label: 'Explore' }
		]} />

		<!-- ================= Stage 1 · Arrival ================= -->
		<div id="stage-arrival">
			<PatientScene stage={0} kicker="Stage 1 · Arrival" title="You arrive at the emergency department"
				narration="You feel a tight pain in your chest and head to the ED. Even how you get here says something." />
			<StoryScene num="1" kicker="Arrival" title="Who comes in, and how?"
				steps={[
					`<b class="c">${pct(N.ambF)}</b> of ${G} patients arrive by ambulance, compared with <b class="n">${pct(N.ambB)}</b> of everyone else.`,
					`At triage, though, their vital signs look much like everyone else’s: systolic blood pressure <b class="c">${fmt1(N.sbpF)}</b> vs <b class="n">${fmt1(N.sbpB)}</b> mmHg, heart rate <b class="c">${fmt1(N.hrF)}</b> vs <b class="n">${fmt1(N.hrB)}</b>. Hover a panel for exact values.`
				]}>
				{#snippet graphic(step)}<StageCharts cube={cube!} {step} kind="arrival" />{/snippet}
			</StoryScene>
		</div>

		<!-- ================= Stage 2 · Triage ================= -->
		<div id="stage-triage">
			<PatientScene stage={1} kicker="Stage 2 · Triage" title="A nurse decides how urgent you are"
				narration="A triage nurse checks your vital signs and asks: on a scale of 0 to 10, how bad is the pain?"
				recap={`${pct(N.ambF)} of ${G} patients arrived by ambulance, yet their vital signs look similar to others’.`} />
			<StoryScene num="2" kicker="Triage" title="More urgent, but less pain"
				steps={[
					`Triage assigns every visit an acuity from <b>1 (most urgent)</b> to <b>5</b>.`,
					`<b class="c">${pct(N.acu12F)}</b> of ${G} visits are triaged as acuity 1–2, versus <b class="n">${pct(N.acu12B)}</b> of other visits.`,
					`In FP1 we compared <b>average</b> pain: ${G} visits report <b class="c">${fmt1(N.meanF)}</b> / 10 and non-cardiac visits <b class="n">${fmt1(N.meanB)}</b> / 10.`,
					`But an average of 4 could mean everyone at 4 — or half at 0 and half at 8. Each bar now shows <b>100% of visits</b>, split into pain levels 0–10. Darker means more pain.`,
					painText
				]}>
				{#snippet graphic(step)}
					{#if step <= 1}<StageCharts cube={cube!} {step} kind="acuity" />{:else}<MorphChart cube={cube!} step={step - 2} />{/if}
				{/snippet}
			</StoryScene>
		</div>

		<!-- ================= Stage 3 · ED stay ================= -->
		<div id="stage-stay">
			<PatientScene stage={2} kicker="Stage 3 · ED stay" title="Then you wait: tests, results, a decision"
				narration="You are moved to an ED bed. Blood tests, an ECG, maybe a repeat test hours later…"
				recap={`<b class="c">${pct(N.acu12F)}</b> of ${G} visits are triaged acuity 1–2 (vs ${pct(N.acu12B)}), yet fewer report severe pain.`} />
			<StoryScene num="3" kicker="ED stay" title="Cardiac patients stay longer"
				steps={[
					`Most emergency visits are short. For <b class="n">non-cardiac</b> patients the median stay is <b class="n">${fmt1(N.losB)} hours</b>.`,
					`<b class="c">${Gc}</b> visits are shifted to the right: a median of <b class="c">${fmt1(N.losF)} hours</b> — about <b>${fmt1(N.gap)} hours longer</b>.`,
					`The difference is clearest in the long tail: <b class="c">${pct(N.tailF)}</b> of ${G} visits last 12 hours or more, versus <b class="n">${pct(N.tailB)}</b> of non-cardiac visits.`
				]}>
				{#snippet graphic(step)}<GapChart cube={cube!} {step} />{/snippet}
			</StoryScene>
			<StoryScene num="3" kicker="ED stay" title="Is it just because they are more urgent?"
				steps={[
					`Maybe ${G} patients are simply more urgent, and urgent patients take longer. If so, the gap should disappear when we compare patients triaged at the <b>same acuity</b>.`,
					`Split by triage acuity, the ${G} median is longer in <b>${N.kAll.k} of ${N.kAll.n}</b> acuity levels — ${verdict(N.kAll)}.`
				]}>
				{#snippet graphic(step)}<SplitChart cube={cube!} {step} />{/snippet}
			</StoryScene>
		</div>

		<!-- ================= Stage 4 · Disposition ================= -->
		<div id="stage-dispo">
			<PatientScene stage={3} kicker="Stage 4 · Disposition" title="Admitted upstairs, or sent home?"
				narration="Finally, the doctor comes back with a decision."
				recap={`${Gc} visits last a median <b class="c">${fmt1(N.losF)} h</b> vs ${fmt1(N.losB)} h, even at the same acuity.`}
				admitted={pct(N.admF)} home={pct(N.homeF)} />
			<StoryScene num="4" kicker="Disposition" title="Who spends the extra time?"
				steps={[admText, homeText]}>
				{#snippet graphic(step)}<SplitChart cube={cube!} step={step + 2} />{/snippet}
			</StoryScene>
			<StoryScene num="4" kicker="Disposition" title="Not all cardiac patients are alike"
				steps={[
					`So far we have treated "cardiac" as one group.`,
					`It is not. Split into five diagnosis groups, median stays range from <b>${fmt1(N.losLo?.c?.los.median)} h</b> (${N.losLo?.g}) to <b>${fmt1(N.losHi?.c?.los.median)} h</b> (${N.losHi?.g}).`,
					`Admission rates differ even more: from <b>${pct(admit(N.admLo?.c ?? null))}</b> (${N.admLo?.g}) to <b>${pct(admit(N.admHi?.c ?? null))}</b> (${N.admHi?.g}).${chestLink}`,
					`<b>Your turn:</b> click a condition. Every chart and the explorer below will retell the journey for that group — scroll up to replay it.`
				]}>
				{#snippet graphic(step)}<ExplodeChart cube={cube!} {step} />{/snippet}
			</StoryScene>
			<StoryScene num="4" kicker="Disposition" title="More diagnoses to sort out"
				steps={[
					`<b class="c">${pct(N.dx3F)}</b> of ${G} visits record 3 or more diagnoses, versus <b class="n">${pct(N.dx3B)}</b> of other visits.`,
					`Among patients <b>sent home</b>, <b class="c">${pct(N.dx3HomeF)}</b> of ${G} visits have 3+ diagnoses vs <b class="n">${pct(N.dx3HomeB)}</b>. More to rule out may mean a longer work-up before discharge — an interpretation we still need to test.`
				]}>
				{#snippet graphic(step)}<StageCharts cube={cube!} {step} kind="dx" />{/snippet}
			</StoryScene>
		</div>
	</div>

	<main id="explore" class="explore">
		<header class="explore-head">
			<span class="num">5</span>
			<div>
				<div class="kicker">Explore</div>
				<h2>Your turn: test the pattern yourself</h2>
				<p>Every chart below is linked. Change a filter, click an acuity label or a condition row, and all views update together. Hover any mark for exact numbers.</p>
			</div>
		</header>

		<FilterBar cube={cube!} />

		<div class="grid">
			<section class="card wide">
				<h3>Length of stay by triage acuity</h3>
				<p class="howto"><b>Read:</b> box = middle 50% of stays, thick tick = median, line = 10th–90th percentile. <b>Try:</b> click an acuity label · switch admitted / home.</p>
				<LosByAcuity cube={cube!} />
			</section>
			<section class="card wide">
				<h3>Reported pain (0–10) by triage acuity</h3>
				<p class="howto"><b>Read:</b> each bar = 100% of visits; darker = more pain. Top bar = focus group, bottom = non-cardiac.</p>
				<PainDistribution cube={cube!} />
			</section>
			<section class="card wide">
				<h3>Patient groups side by side</h3>
				<p class="howto"><b>Try:</b> click a row to make it the focus group for every chart.</p>
				<GroupOverview cube={cube!} />
			</section>
			<section class="card wide">
				<h3>Vital signs at triage</h3>
				<p class="howto">Median (dot) and middle 50% (bar). Green band = typical adult range.</p>
				<VitalsPanel cube={cube!} />
			</section>
		</div>

		<section class="takeaways">
			<div><b>1</b><p>{Gc} visits last about {fmt1(N.gap)} h longer overall{few(N.kAdm) && mostly(N.kHome) ? ' — mostly among patients who are later discharged home' : mostly(N.kAll) ? ', even at the same triage acuity' : ''}.</p></div>
			<div><b>2</b><p>Severe pain (7–10) is reported in {pct(N.sevF)} of {G} vs {pct(N.sevB)} of non-cardiac visits — averages hide this.</p></div>
			<div><b>3</b><p>"Cardiac" is not one group: median stay ranges {fmt1(N.losLo?.c?.los.median)}–{fmt1(N.losHi?.c?.los.median)} h and admission {pct(admit(N.admLo?.c ?? null))}–{pct(admit(N.admHi?.c ?? null))} across conditions.</p></div>
		</section>

		<section class="notes">
			<h3>How to interpret these findings</h3>
			<ul>
				<li>Cardiac groups are defined by keywords in ED diagnosis titles — an exploratory definition, not a clinical one.</li>
				<li>All numbers are aggregated; groups with fewer than {cube.meta.min_cell_size} visits are hidden to protect privacy.</li>
				<li>These are associations, not causes.</li>
				{#if !cube.meta.age_available}<li>Age is not available in MIMIC-IV-ED alone, so it is not yet included.</li>{/if}
			</ul>
			<button class="reset" onclick={resetFilters}>Reset all filters</button>
		</section>
	</main>
{/if}

{#if tip.show}
	<div class="tooltip" style:left="{tip.x + 14}px" style:top="{tip.y + 14}px">
		{#each tip.lines as line, i}
			<div class:first={i === 0}>{line}</div>
		{/each}
	</div>
{/if}

<style>
	:global(*) { box-sizing: border-box; }
	:global(html) { scroll-behavior: smooth; }
	:global(body) {
		margin: 0; background: #f4f6fa; color: #172033;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
		-webkit-font-smoothing: antialiased;
	}
	@media (prefers-reduced-motion: reduce) { :global(html) { scroll-behavior: auto; } }

	.story { position: relative; padding-bottom: 8vh; }

	.explore { max-width: 1240px; margin: 0 auto; padding: 10vh 28px 60px; }
	.explore-head { display: flex; gap: 18px; align-items: baseline; margin-bottom: 18px; }
	.explore-head .num { font-size: 3.4rem; font-weight: 800; color: #dbe4f3; line-height: 1; }
	.explore-head .kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #2563eb; }
	.explore-head h2 { margin: 4px 0 0; font-size: clamp(1.6rem, 3vw, 2.3rem); letter-spacing: -0.025em; }
	.explore-head p { margin: 8px 0 0; color: #475569; max-width: 760px; line-height: 1.6; }

	.grid { display: grid; gap: 20px; }
	.card { background: #fff; border-radius: 18px; padding: 24px 26px; border: 1px solid #e6ebf3; box-shadow: 0 6px 20px rgba(23, 43, 77, 0.05); }
	.card h3 { margin: 0; font-size: 1.15rem; }
	.howto { margin: 6px 0 14px; font-size: 0.85rem; color: #475569; line-height: 1.55; }

	.takeaways { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 28px; }
	.takeaways div { background: #172b4d; color: #fff; border-radius: 16px; padding: 20px 22px; }
	.takeaways b { font-size: 1.6rem; color: #9cc0ff; }
	.takeaways p { margin: 6px 0 0; line-height: 1.55; color: #dbe5f5; }

	.notes { margin-top: 24px; background: #fff; border-radius: 16px; padding: 20px 24px; border: 1px solid #e6ebf3; }
	.notes h3 { margin: 0; font-size: 1.05rem; }
	.notes ul { margin: 10px 0 0; padding-left: 20px; line-height: 1.8; color: #475569; }
	.reset { margin-top: 10px; font: inherit; font-size: 0.85rem; padding: 8px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; }

	:global(.takeaway) { margin: 12px 0 0; padding: 12px 14px; background: #fffbea; border-radius: 10px; font-size: 0.92rem; line-height: 1.6; }
	:global(.controls) { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-bottom: 8px; }
	:global(.ctl-label) { font-size: 12px; font-weight: 700; color: #64748b; margin-right: 4px; }
	:global(.seg) { font: inherit; font-size: 12px; padding: 5px 11px; border: 1px solid #cbd5e1; border-radius: 999px; background: #fff; cursor: pointer; }
	:global(.seg.active) { background: #2563eb; color: #fff; border-color: #2563eb; }

	.status, .error { padding: 40px; }
	.error { color: #b91c1c; }

	.tooltip { position: fixed; z-index: 50; pointer-events: none; background: #172033; color: #fff; font-size: 12px; line-height: 1.5; padding: 8px 10px; border-radius: 8px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2); max-width: 280px; }
	.tooltip .first { font-weight: 700; margin-bottom: 2px; }

	@media (max-width: 760px) {
		.takeaways { grid-template-columns: 1fr; }
		.explore { padding: 8vh 16px 40px; }
	}
</style>