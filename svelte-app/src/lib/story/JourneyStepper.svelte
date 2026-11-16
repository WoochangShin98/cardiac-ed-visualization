<!--
  Sticky "where is our patient?" progress bar.
  Highlights the stage whose section is in the middle of the screen; click a stage to jump to it.
-->
<script lang="ts">
	import { filters } from '#lib/state.svelte.ts';
	import { ALL, CARDIAC_ALL } from '#lib/cube.ts';

	const SEXES = [
		{ v: ALL, label: 'All' },
		{ v: 'Female', label: 'Women' },
		{ v: 'Male', label: 'Men' }
	];

	let { stages }: { stages: { id: string; label: string }[] } = $props();

	let active = $state(0);

	$effect(() => {
		const els = stages.map((s) => document.getElementById(s.id));
		const observer = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					if (e.isIntersecting) active = els.indexOf(e.target as HTMLElement);
				}
			},
			{ rootMargin: '-45% 0px -50% 0px' }
		);
		els.forEach((el) => el && observer.observe(el));
		return () => observer.disconnect();
	});
</script>

<nav class="stepper" aria-label="Patient journey progress">
	<ol>
		{#each stages as s, i}
			<li class:done={i < active} class:now={i === active}>
				<a href={`#${s.id}`} aria-current={i === active ? 'step' : undefined}>
					<span class="dot">{i + 1}</span>
					<span class="lbl">{s.label}</span>
				</a>
			</li>
			{#if i < stages.length - 1}
				<li class="line" class:done={i < active} aria-hidden="true"></li>
			{/if}
		{/each}
	</ol>
	<div class="sex" role="group" aria-label="Gender: re-run every story chart for one gender">
		<span class="sex-lbl">Gender</span>
		{#each SEXES as s}
			<button class:on={filters.gender === s.v} aria-pressed={filters.gender === s.v}
				onclick={() => (filters.gender = s.v)}>{s.label}</button>
		{/each}
	</div>
	{#if filters.group !== CARDIAC_ALL}
		<div class="focus">
			Following: <b>{filters.group}</b>
			<button onclick={() => (filters.group = CARDIAC_ALL)}>all cardiac</button>
		</div>
	{/if}
</nav>

<style>
	.stepper {
		position: sticky; top: 0; z-index: 30;
		display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
		padding: 8px 20px; background: rgba(244, 246, 250, 0.94); backdrop-filter: blur(6px);
		border-bottom: 1px solid #e2e8f0;
	}
	ol { list-style: none; margin: 0 auto; padding: 0; display: flex; align-items: center; gap: 6px; flex: 1; max-width: 900px; }
	li a { display: flex; align-items: center; gap: 8px; text-decoration: none; color: #64748b; font-size: 0.85rem; font-weight: 700; white-space: nowrap; }
	.dot {
		width: 26px; height: 26px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
		border: 2px solid #cbd5e1; background: #fff; font-size: 0.75rem; transition: all 0.4s;
	}
	li.done a, li.now a { color: #172b4d; }
	li.done .dot { background: #172b4d; border-color: #172b4d; color: #fff; }
	li.now .dot { background: #ffcc33; border-color: #172b4d; color: #172b4d; box-shadow: 0 0 0 4px #ffe9a6; }
	li.line { flex: 1; height: 3px; min-width: 12px; background: #cbd5e1; border-radius: 2px; transition: background 0.4s; }
	li.line.done { background: #172b4d; }
	.sex { display: inline-flex; align-items: center; gap: 2px; background: #fff; border: 1px solid #cbd5e1; border-radius: 999px; padding: 2px; }
	.sex-lbl { font-size: 0.72rem; font-weight: 800; color: #64748b; padding: 0 6px 0 8px; text-transform: uppercase; letter-spacing: 0.06em; }
	.sex button { font: inherit; font-size: 0.78rem; font-weight: 700; border: 0; background: transparent; color: #334155; border-radius: 999px; padding: 3px 10px; cursor: pointer; transition: background 0.3s, color 0.3s; }
	.sex button.on { background: #172b4d; color: #fff; }
	.focus { font-size: 0.8rem; color: #334155; }
	.focus button { margin-left: 6px; font: inherit; font-size: 0.75rem; border: 1px solid #cbd5e1; background: #fff; border-radius: 999px; padding: 2px 8px; cursor: pointer; }
	@media (max-width: 700px) { .lbl { display: none; } li.now .lbl { display: inline; } }
</style>
