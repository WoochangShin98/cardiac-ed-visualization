<!--
  Scroll-driven step tracker (scrollytelling).
  Wrap `.step` elements; `value` = index of the step crossing the middle of the screen.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';

	let { value = $bindable(0), children }: { value?: number; children: Snippet } = $props();

	let container: HTMLDivElement;

	$effect(() => {
		const steps = Array.from(container.querySelectorAll<HTMLElement>('.step'));
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) value = steps.indexOf(entry.target as HTMLElement);
				}
			},
			{ rootMargin: '-50% 0px -50% 0px' }
		);
		steps.forEach((s) => observer.observe(s));
		return () => observer.disconnect();
	});
</script>

<div bind:this={container}>
	{@render children()}
</div>
