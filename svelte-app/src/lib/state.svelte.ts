// Shared filter state = the "glue" for multi-view linking.
// Any chart can write here; every chart reads from here.
import { ALL, DEFAULT_FILTERS, type Dim, type Filters } from './cube.ts';

export const filters: Filters = $state({ ...DEFAULT_FILTERS });

/** Click once to select, click the same value again to clear (back to All). */
export function toggleFilter(dim: Dim, value: string) {
	if (dim === 'group') {
		// group always has a focus; clicking the active one returns to the default
		filters.group = filters.group === value ? DEFAULT_FILTERS.group : value;
		return;
	}
	filters[dim] = filters[dim] === value ? ALL : value;
}

export function setFilter(dim: Dim, value: string) {
	filters[dim] = value;
}

export function resetFilters() {
	Object.assign(filters, DEFAULT_FILTERS);
}
