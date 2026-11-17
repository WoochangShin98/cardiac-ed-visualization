import { DEFAULT_FILTERS, getCell, type Cube, type Filters } from '#lib/cube.ts';
import { filters } from '#lib/state.svelte.ts';

/**
 * Story scenes use the focus group + the gender switch (a third dimension that applies to every
 * story chart). Other filters (acuity, disposition...) stay at "All" so the narrative stays stable.
 */
export function storyCell(cube: Cube, group: string, override: Partial<Filters> = {}) {
	return getCell(cube, { ...DEFAULT_FILTERS, group, gender: filters.gender }, override);
}

export function reduceMotion() {
	return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

/** One fixed color per heart condition (used by the condition map and the stay matrix). */
export const COND_COLORS: Record<string, string> = {
	'MI / ischemia': '#7c3aed',
	'Heart failure': '#db2777',
	Arrhythmia: '#0891b2',
	'Other cardiovascular': '#65a30d',
	'Chest pain / symptoms': '#d97706'
};
