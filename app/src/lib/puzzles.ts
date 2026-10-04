export type Direction = 'across' | 'down';

export interface Clue {
	number: number;
	text: string;
	/** As printed, e.g. "10" or "2,4,4". */
	enumeration: string;
	answer_length: number;
	row: number;
	col: number;
}

export interface Puzzle {
	id: string;
	title: string;
	source: string;
	date: string;
	size: { rows: number; cols: number };
	/** "#" = black, otherwise the cell number or "". */
	grid: string[][];
	clues: Record<Direction, Clue[]>;
	/** One string per row, "#" for black cells. Only present when the answers are known. */
	solution?: string[];
}

// Puzzle JSON lives in ../puzzles (committed alongside the source PDFs) and is
// bundled at build time, one lazy chunk per puzzle.
const modules = import.meta.glob<Puzzle>('../../../puzzles/*.json', { import: 'default' });

const byId = new Map(
	Object.entries(modules).map(([path, load]) => [path.replace(/^.*\/|\.json$/g, ''), load])
);

/** Puzzle ids (= publication dates), newest first. */
export const puzzleIds = [...byId.keys()].sort().reverse();

export async function loadPuzzle(id: string): Promise<Puzzle | undefined> {
	return byId.get(id)?.();
}

const MONTHS = [
	'janúar', 'febrúar', 'mars', 'apríl', 'maí', 'júní',
	'júlí', 'ágúst', 'september', 'október', 'nóvember', 'desember'
];

export function formatDate(iso: string): string {
	const [y, m, d] = iso.split('-').map(Number);
	return `${d}. ${MONTHS[m - 1]} ${y}`;
}
