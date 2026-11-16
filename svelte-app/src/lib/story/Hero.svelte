<!-- Scene 1: full-screen hook with count-up numbers. -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { Tween } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { fmt1, fmtInt } from '#lib/cube.ts';
	import { reduceMotion } from './story.ts';

	let { total, cardiac, losC, losN }: { total: number; cardiac: number; losC: number; losN: number } = $props();

	const t = new Tween(0, { duration: reduceMotion() ? 0 : 1600, easing: cubicOut });
	onMount(() => {
		t.target = 1;
	});
</script>

<header class="hero">
	<div class="glow" aria-hidden="true"></div>
	<div class="inner">
		<div class="eyebrow">CSCI 5609 · The Outliers · Woochang Shin, Sruti Paladugu, Ananya Nair</div>
		<h1>How does a cardiac patient’s ED journey differ from everyone else’s?</h1>
		<p class="lede">
			Chest pain is one of the most common reasons people come to an emergency department. Using
			MIMIC-IV-ED (Beth Israel Deaconess Medical Center, 2011–2019), we follow one patient from arrival
			to disposition — and test whether the differences survive a closer look.
		</p>
		<p class="lede hint">
			Tip: use the <b>Gender</b> switch in the bar at the top to re-run every chart for women or men only
			and check whether each pattern still holds.
		</p>
		<div class="metrics">
			<div class="metric"><span>ED visits analysed</span><strong>{fmtInt(total * t.current)}</strong></div>
			<div class="metric"><span>Cardiac-related</span><strong>{fmtInt(cardiac * t.current)}</strong></div>
			<div class="metric"><span>Median stay · cardiac</span><strong class="c">{fmt1(losC * t.current)} h</strong></div>
			<div class="metric"><span>Median stay · non-cardiac</span><strong class="n">{fmt1(losN * t.current)} h</strong></div>
		</div>
		<div class="actions">
			<a class="scroll" href="#story">Scroll to begin the story ↓</a>
			<a class="skip" href="#explore">Skip to the explorer</a>
		</div>
	</div>
</header>

<style>
	.hero {
		position: relative; overflow: hidden; min-height: 100vh; display: flex; align-items: center;
		background: radial-gradient(1200px 600px at 85% 10%, #22407a 0%, #142849 45%, #0d1b33 100%);
		color: #fff;
	}
	.glow {
		position: absolute; right: -10%; bottom: -30%; width: 70vw; height: 70vw; border-radius: 50%;
		background: radial-gradient(circle, rgba(232, 121, 69, 0.18), transparent 60%);
	}
	.inner { position: relative; max-width: 1180px; margin: 0 auto; padding: 80px 28px; }
	.eyebrow { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #9cc0ff; }
	h1 { margin: 18px 0 0; max-width: 940px; font-size: clamp(2.2rem, 5vw, 4rem); line-height: 1.06; letter-spacing: -0.035em; }
	.lede.hint { margin-top: 12px; font-size: 0.98rem; color: #aebfdc; }
	.lede.hint b { color: #ffcc33; }
	.lede { max-width: 720px; margin: 22px 0 0; font-size: 1.12rem; line-height: 1.7; color: #d3def0; }
	.metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 44px; }
	.metric { padding: 18px 20px; border-radius: 16px; background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.1); }
	.metric span { display: block; font-size: 0.8rem; color: #b6c4dc; }
	.metric strong { display: block; margin-top: 6px; font-size: clamp(1.5rem, 2.6vw, 2.2rem); font-variant-numeric: tabular-nums; }
	.c { color: #8fb4ff; }
	.n { color: #ffb08a; }
	.actions { display: flex; gap: 18px; align-items: center; margin-top: 46px; flex-wrap: wrap; }
	.scroll { color: #fff; font-weight: 700; text-decoration: none; padding: 12px 20px; border-radius: 999px; background: #2563eb; animation: bob 2.2s ease-in-out infinite; }
	.skip { color: #b6c4dc; font-size: 0.9rem; }
	@keyframes bob { 50% { transform: translateY(4px); } }
	@media (max-width: 700px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
	@media (prefers-reduced-motion: reduce) { .scroll { animation: none; } }
</style>
