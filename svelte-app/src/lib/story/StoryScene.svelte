<!--
  One scrollytelling scene: text steps on the left, sticky chart on the right.
  `steps` are short HTML strings we write ourselves (numbers come from the cube).
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import Scrolly from './Scrolly.svelte';

	let {
		num,
		kicker,
		title,
		steps,
		graphic,
		step = $bindable(0)
	}: {
		num: string;
		kicker: string;
		title: string;
		steps: string[];
		graphic: Snippet<[number]>;
		step?: number;
	} = $props();
</script>

<section class="scene">
	<header class="scene-head">
		<span class="num">{num}</span>
		<div>
			<div class="kicker">{kicker}</div>
			<h2>{title}</h2>
		</div>
	</header>

	<div class="layout">
		<div class="steps">
			<Scrolly bind:value={step}>
				{#each steps as text, i}
					<div class="step" class:active={step === i}>
						<div class="card">
							<span class="dot">{i + 1}/{steps.length}</span>
							<p>{@html text}</p>
						</div>
					</div>
				{/each}
			</Scrolly>
			<div class="spacer"></div>
		</div>
		<div class="graphic">
			<div class="graphic-inner">
				{@render graphic(step)}
			</div>
		</div>
	</div>
</section>

<style>
	.scene { margin: 0 auto; max-width: 1400px; padding: 8vh 28px 0; scroll-margin-top: 60px; }
	.scene-head { display: flex; gap: 18px; align-items: baseline; margin-bottom: 4vh; }
	.num { font-size: 3.4rem; font-weight: 800; color: #dbe4f3; line-height: 1; }
	.kicker { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #2563eb; }
	h2 { margin: 4px 0 0; font-size: clamp(1.6rem, 3vw, 2.3rem); letter-spacing: -0.025em; line-height: 1.15; }

	.layout { display: grid; grid-template-columns: minmax(250px, 0.62fr) minmax(0, 1.9fr); gap: 32px; }
	.steps { position: relative; z-index: 2; }
	.step { min-height: 78vh; display: flex; align-items: center; }
	.step:first-child { min-height: 50vh; align-items: flex-start; }
	.spacer { height: 20vh; }
	.card {
		background: #fff; border-radius: 16px; padding: 22px 24px;
		box-shadow: 0 10px 30px rgba(23, 43, 77, 0.08); border: 1px solid #e6ebf3;
		opacity: 0.35; transform: translateY(8px);
		transition: opacity 0.4s ease, transform 0.4s ease, border-color 0.4s;
	}
	.step.active .card { opacity: 1; transform: none; border-color: #bfd3fb; }
	.dot { font-size: 0.72rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.08em; }
	.card p { margin: 6px 0 0; font-size: 1.05rem; line-height: 1.65; color: #1e293b; }
	.card :global(b.c) { color: #2563eb; }
	.card :global(b.n) { color: #d9622b; }

	.graphic { position: relative; }
	.graphic-inner {
		position: sticky; top: calc(8vh + 52px); height: calc(84vh - 52px);
		background: #fff; border-radius: 20px; border: 1px solid #e6ebf3;
		box-shadow: 0 16px 40px rgba(23, 43, 77, 0.08);
		padding: 22px 24px; display: flex; flex-direction: column;
	}

	@media (max-width: 860px) {
		.layout { grid-template-columns: 1fr; }
		.graphic { grid-row: 1; position: sticky; top: 0; z-index: 1; }
		.graphic-inner { position: relative; top: 0; height: 55vh; }
		.steps { margin-top: -10vh; }
		.card { background: rgba(255, 255, 255, 0.95); }
	}
</style>
