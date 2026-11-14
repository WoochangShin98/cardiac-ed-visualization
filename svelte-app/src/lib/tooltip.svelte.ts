// One tooltip shared by all charts (rendered once in +page.svelte).
export const tip = $state({ show: false, x: 0, y: 0, lines: [] as string[] });

export function showTip(e: MouseEvent, lines: string[]) {
	tip.show = true;
	tip.x = e.clientX;
	tip.y = e.clientY;
	tip.lines = lines;
}

export function hideTip() {
	tip.show = false;
}
