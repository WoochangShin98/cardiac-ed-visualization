import { DEFAULT_FILTERS, getCell, type Cube, type Filters } from '#lib/cube.ts';

/** Story scenes use only the focus group (no other filters) so the narrative stays stable. */
export function storyCell(cube: Cube, group: string, override: Partial<Filters> = {}) {
	return getCell(cube, { ...DEFAULT_FILTERS, group }, override);
}

export function reduceMotion() {
	return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}
