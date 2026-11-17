<!--
  "Follow one patient" interlude shown before each stage.
  The patient walks from the previous station to this stage's station when the scene scrolls into view,
  then the narration and the finding carried over from the last stage appear.
-->
<script lang="ts">
	import { reduceMotion } from './story.ts';
	import { filters } from '#lib/state.svelte.ts';
	import { CARDIAC_ALL } from '#lib/cube.ts';

	// the avatar follows the Gender switch and the selected condition
	const female = $derived(filters.gender === 'Female');
	const male = $derived(filters.gender === 'Male');
	const tag = $derived(filters.group === CARDIAC_ALL ? '' : filters.group);

	let {
		stage,
		kicker,
		title,
		narration,
		recap = '',
		admitted = null,
		home = null,
		terms = []
	}: {
		stage: 0 | 1 | 2 | 3;
		kicker: string;
		title: string;
		narration: string;
		recap?: string;
		admitted?: string | null;
		home?: string | null;
		terms?: { t: string; d: string }[];
	} = $props();

	// x position of the patient at each station (viewBox units)
	const STOP = [120, 330, 575, 790];
	const START = [-60, 120, 330, 575];

	let el: HTMLElement;
	let arrived = $state(false);
	let walking = $state(false);

	$effect(() => {
		const obs = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					if (e.isIntersecting && !arrived) {
						arrived = true;
						walking = !reduceMotion();
						setTimeout(() => (walking = false), 1900);
					}
				}
			},
			{ threshold: 0.45 }
		);
		obs.observe(el);
		return () => obs.disconnect();
	});

	const x = $derived(arrived ? STOP[stage] : START[stage]);
	const label = ['Check-in', 'Triage', 'ED bed', 'Decision'];
</script>

{#snippet body(kind: 'f' | 'm')}
	{#if kind === 'f'}
		<path d="M-19 122 Q-20 100 0 102 Q20 100 19 122 L21 156 Q0 162 -21 156 Z" fill="#4b3621" class="av" />
	{/if}
	<circle cx="0" cy="124" r="16" fill="#f1c7a3" />
	{#if kind === 'm'}
		<path d="M-16 119 Q-15 104 0 104 Q15 104 16 119 Q8 112 0 113 Q-8 112 -16 119 Z" fill="#2b1d12" class="av" />
		<rect x="-18" y="143" width="36" height="58" rx="11" fill="#2563eb" />
	{:else}
		<path d="M-11 117 Q0 104 11 117" fill="none" stroke="#4b3621" stroke-width="4" />
		<path d="M-14 143 L14 143 L24 205 L-24 205 Z" fill="#2563eb" class="av" />
	{/if}
	<path d="M-2 160 q-6 -6 -10 0 q0 6 10 12 q10 -6 10 -12 q-4 -6 -10 0z" fill="#fff" opacity="0.9" />
	<line class="leg l" x1="-8" y1="200" x2="-8" y2="236" stroke="#1e3a8a" stroke-width="8" stroke-linecap="round" />
	<line class="leg r" x1="8" y1="200" x2="8" y2="236" stroke="#1e3a8a" stroke-width="8" stroke-linecap="round" />
{/snippet}

<section class="ps" bind:this={el} aria-label={`Stage ${stage + 1}: ${title}`}>
	<div class="head">
		<span class="kicker">{kicker}</span>
		<h2>{title}</h2>
	</div>

	<svg viewBox="0 0 1000 300" role="img" aria-label={`Illustration: the patient moves to ${label[stage]}`}>
		<!-- floor & corridor -->
		<rect x="0" y="0" width="1000" height="300" rx="18" fill="#eef2f8" />
		<rect x="0" y="236" width="1000" height="64" fill="#dde4ef" />
		<line x1="0" y1="236" x2="1000" y2="236" stroke="#c4cedd" stroke-width="2" />
		{#each STOP as sx, i}
			<circle cx={sx} cy="262" r="7" fill={i <= stage ? '#172b4d' : '#c4cedd'} />
			{#if i < 3}<line x1={sx + 10} y1="262" x2={STOP[i + 1] - 10} y2="262" stroke={i < stage ? '#172b4d' : '#c4cedd'} stroke-width="3" stroke-dasharray="6 6" />{/if}
			<text x={sx} y="290" text-anchor="middle" class="st" class:on={i === stage}>{label[i]}</text>
		{/each}

		<!-- 1 · entrance / check-in -->
		<g opacity={stage === 0 ? 1 : 0.55}>
			<rect x="40" y="70" width="120" height="166" rx="6" fill="#fff" stroke="#9fb0c7" stroke-width="3" />
			<line x1="100" y1="70" x2="100" y2="236" stroke="#9fb0c7" stroke-width="3" />
			<rect x="62" y="34" width="76" height="28" rx="5" fill="#b91c1c" />
			<text x="100" y="54" text-anchor="middle" class="sign">EMERGENCY</text>
			<rect x="160" y="170" width="60" height="66" rx="4" fill="#cbd5e1" />
		</g>

		<!-- 2 · triage desk with nurse -->
		<g opacity={stage === 1 ? 1 : 0.55}>
			<rect x="380" y="170" width="90" height="66" rx="4" fill="#cbd5e1" />
			<rect x="400" y="140" width="34" height="24" rx="3" fill="#475569" />
			<polyline points="404,152 412,152 416,145 421,159 425,152 430,152" fill="none" stroke="#4ade80" stroke-width="2" />
			<g transform="translate(470 0)">
				<circle cx="0" cy="128" r="15" fill="#f3c9a8" />
				<path d="M-15 124 Q0 104 15 124" fill="#3b2f2f" />
				<rect x="-17" y="146" width="34" height="56" rx="10" fill="#14b8a6" />
				<line x1="-8" y1="202" x2="-8" y2="236" stroke="#0f766e" stroke-width="7" stroke-linecap="round" />
				<line x1="8" y1="202" x2="8" y2="236" stroke="#0f766e" stroke-width="7" stroke-linecap="round" />
			</g>
			<text x="470" y="96" text-anchor="middle" class="who">Triage nurse</text>
		</g>

		<!-- 3 · ED bed with monitor -->
		<g opacity={stage === 2 ? 1 : 0.55}>
			<rect x="610" y="176" width="130" height="22" rx="6" fill="#fff" stroke="#9fb0c7" stroke-width="3" />
			<rect x="610" y="160" width="34" height="18" rx="6" fill="#e2e8f0" />
			<line x1="618" y1="198" x2="618" y2="236" stroke="#9fb0c7" stroke-width="4" />
			<line x1="732" y1="198" x2="732" y2="236" stroke="#9fb0c7" stroke-width="4" />
			<line x1="760" y1="96" x2="760" y2="236" stroke="#9fb0c7" stroke-width="3" />
			<rect x="748" y="96" width="24" height="30" rx="5" fill="#bfdbfe" stroke="#9fb0c7" />
			<rect x="640" y="104" width="54" height="38" rx="4" fill="#475569" />
			<polyline points="646,124 656,124 661,114 667,134 672,124 688,124" fill="none" stroke="#4ade80" stroke-width="2" />
			<text x="705" y="88" text-anchor="middle" class="who">Hours of tests &amp; monitoring</text>
		</g>

		<!-- 4 · decision: ward or home, doctor -->
		<g opacity={stage === 3 ? 1 : 0.55}>
			<g transform="translate(850 0)">
				<circle cx="0" cy="128" r="15" fill="#e8b48f" />
				<path d="M-15 124 Q0 106 15 124" fill="#1f2937" />
				<rect x="-18" y="146" width="36" height="58" rx="10" fill="#fff" stroke="#94a3b8" stroke-width="2" />
				<path d="M-6 150 Q-10 170 -2 176" fill="none" stroke="#475569" stroke-width="2" />
				<line x1="-8" y1="204" x2="-8" y2="236" stroke="#334155" stroke-width="7" stroke-linecap="round" />
				<line x1="8" y1="204" x2="8" y2="236" stroke="#334155" stroke-width="7" stroke-linecap="round" />
			</g>
			<text x="850" y="96" text-anchor="middle" class="who">Doctor</text>
			<g transform="translate(905 30)">
				<rect x="0" y="0" width="80" height="48" rx="6" fill="#fff" stroke="#9fb0c7" stroke-width="2" />
				<text x="40" y="20" text-anchor="middle" class="dest">Admitted</text>
				<text x="40" y="38" text-anchor="middle" class="pct">{admitted ?? ''}</text>
			</g>
			<g transform="translate(905 150)">
				<rect x="0" y="0" width="80" height="48" rx="6" fill="#fff" stroke="#9fb0c7" stroke-width="2" />
				<text x="40" y="20" text-anchor="middle" class="dest">Sent home</text>
				<text x="40" y="38" text-anchor="middle" class="pct">{home ?? ''}</text>
			</g>
		</g>

		<!-- the patient (moves between stations) -->
		<g class="patient" class:walking style:transform={`translateX(${x}px)`}>
			{#if female}
				{@render body('f')}
			{:else if male}
				{@render body('m')}
			{:else}
				<!-- "All": a woman and a man walk together -->
				<g transform="translate(-19 18) scale(0.86)">{@render body('f')}</g>
				<g transform="translate(19 18) scale(0.86)" class="p2">{@render body('m')}</g>
			{/if}
			<text x="0" y="96" text-anchor="middle" class="you">You</text>
			{#if tag}
				<g class="av">
					<rect x={-tag.length * 3.6 - 8} y="62" width={tag.length * 7.2 + 16} height="20" rx="10" fill="#2563eb" />
					<text x="0" y="76" text-anchor="middle" class="tag">{tag}</text>
				</g>
			{/if}
		</g>
	</svg>

	<div class="talk" class:show={arrived}>
		<p class="nar">{narration}</p>
		{#if recap}<p class="recap"><b>So far:</b> {@html recap}</p>{/if}
		{#if terms.length}
			<div class="terms" aria-label="Key terms for this stage">
				<span class="tl">Key terms</span>
				{#each terms as k}
					<div class="term"><b>{k.t}</b><span>{k.d}</span></div>
				{/each}
			</div>
		{/if}
	</div>
</section>

<style>
	.ps { max-width: 1100px; margin: 0 auto; padding: 14vh 28px 4vh; scroll-margin-top: 60px; }
	.head { display: flex; flex-direction: column; gap: 4px; margin-bottom: 18px; }
	.kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #b45309; }
	h2 { margin: 0; font-size: clamp(1.7rem, 3.4vw, 2.6rem); letter-spacing: -0.025em; line-height: 1.12; }
	svg { width: 100%; height: auto; display: block; border-radius: 18px; box-shadow: 0 12px 34px rgba(23, 43, 77, 0.08); }
	.st { font-size: 15px; font-weight: 700; fill: #94a3b8; }
	.st.on { fill: #172b4d; }
	.sign { font-size: 11px; font-weight: 800; fill: #fff; letter-spacing: 0.05em; }
	.who { font-size: 13px; font-weight: 700; fill: #475569; }
	.dest { font-size: 12px; font-weight: 700; fill: #334155; }
	.pct { font-size: 14px; font-weight: 800; fill: #2563eb; }
	.tag { font-size: 11.5px; font-weight: 800; fill: #fff; }
	.av { animation: pop 0.4s ease-out; }
	@keyframes pop { from { opacity: 0; } }
	.you { font-size: 13px; font-weight: 800; fill: #2563eb; }
	.patient { transition: transform 1.8s cubic-bezier(0.4, 0, 0.2, 1); }
	.patient.walking { animation: bob 0.45s ease-in-out infinite; }
	.patient.walking .leg.l { animation: swingL 0.45s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 0; }
	.patient.walking .leg.r { animation: swingR 0.45s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 0; }
	.patient.walking .p2 .leg { animation-delay: -0.22s; }
	@keyframes swingL { 50% { transform: rotate(18deg); } }
	@keyframes swingR { 50% { transform: rotate(-18deg); } }
	@keyframes bob { 50% { translate: 0 -3px; } }
	.talk { margin-top: 18px; opacity: 0; transform: translateY(10px); transition: opacity 0.6s 1.2s, transform 0.6s 1.2s; }
	.talk.show { opacity: 1; transform: none; }
	.nar { margin: 0; font-size: 1.25rem; line-height: 1.6; font-style: italic; color: #1e293b; max-width: 820px; }
	.recap { margin: 12px 0 0; display: inline-block; padding: 8px 14px; border-radius: 10px; background: #fffbea; font-size: 0.95rem; color: #334155; }
	.recap :global(b.c) { color: #2563eb; }
	.terms { margin-top: 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; align-items: stretch; }
	.tl { grid-column: 1 / -1; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #64748b; }
	.term { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 14px; display: flex; flex-direction: column; gap: 3px; box-shadow: 0 4px 14px rgba(23, 43, 77, 0.05); }
	.term b { font-size: 0.92rem; color: #172b4d; }
	.term span { font-size: 0.86rem; line-height: 1.45; color: #475569; }
	@media (prefers-reduced-motion: reduce) { .patient { transition: none; } .talk { transition: none; } }
</style>
