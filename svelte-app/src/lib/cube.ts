// Types + helpers for the aggregated data cube produced by
// src/build_web_aggregates.py (static/data/ed_cube.json).
// The site never sees patient-level rows - only these summaries.

export type Dim = 'group' | 'acuity' | 'dispo' | 'gender' | 'age';
export type Filters = Record<Dim, string>;

export type Quart = {
	n: number;
	q1: number | null;
	median: number | null;
	q3: number | null;
};

export type Cell = {
	n: number;
	los: Quart & {
		p10: number | null;
		p90: number | null;
		mean: number | null;
		hist: (number | null)[];
	};
	pain: Quart & { mean: number | null; dist: (number | null)[] };
	dispo: (number | null)[];
	dx: (number | null)[];
	transport: (number | null)[];
	vitals: Record<string, Quart>;
};

export type Cube = {
	meta: {
		total_encounters: number;
		min_cell_size: number;
		dims: Dim[];
		dim_values: Record<Dim, string[]>;
		los_bins: string[];
		pain_levels: number[];
		dispo_levels: string[];
		dx_labels: string[];
		transport_levels: string[];
		vitals: string[];
		age_available: boolean;
	};
	cells: Record<string, Cell>;
};

export const ALL = 'All';
export const CARDIAC_ALL = 'Cardiac (all)';
export const NON_CARDIAC = 'Non-cardiac';

export const DIMS: Dim[] = ['group', 'acuity', 'dispo', 'gender', 'age'];

export const DIM_LABELS: Record<Dim, string> = {
	group: 'Patient group',
	acuity: 'Triage acuity',
	dispo: 'Disposition',
	gender: 'Gender',
	age: 'Age group'
};

export const DEFAULT_FILTERS: Filters = {
	group: CARDIAC_ALL,
	acuity: ALL,
	dispo: ALL,
	gender: ALL,
	age: ALL
};

/** Look up one cell. `override` replaces some filter values. Returns null when suppressed. */
export function getCell(cube: Cube, filters: Filters, override: Partial<Filters> = {}): Cell | null {
	const f = { ...filters, ...override };
	const key = DIMS.map((d) => f[d] ?? ALL).join('|');
	return cube.cells[key] ?? null;
}

/** Suppressed counts are null - treat as 0 for drawing, but flag it. */
export const nz = (v: number | null | undefined) => v ?? 0;
export const hasSuppressed = (arr: (number | null)[]) => arr.some((v) => v === null);

export const fmtInt = (v: number | null | undefined) =>
	v == null ? '—' : Math.round(v).toLocaleString('en-US');
export const fmt1 = (v: number | null | undefined) => (v == null ? '—' : v.toFixed(1));
export const pct = (v: number) => `${Math.round(v * 100)}%`;

// Encoding shared by every chart (kept from FP1).
export const COLORS = {
	focus: '#2563eb', // cardiac / selected group
	baseline: '#e87945', // non-cardiac comparison
	muted: '#cbd5e1',
	ink: '#172033',
	grid: '#e5e9f0'
};

/** Sequential palette for pain 0-10 (light = no pain, dark = worst pain). */
export const PAIN_COLORS = [
	'#f1f5f9', '#e0ecf8', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6',
	'#2171b5', '#08519c', '#08306b', '#3b1f66', '#2a0f4d'
];
