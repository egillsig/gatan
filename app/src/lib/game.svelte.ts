import type { Clue, Direction, Puzzle } from './puzzles';

export interface Slot {
	id: string; // e.g. "12-across"
	dir: Direction;
	clue: Clue;
	/** Flat cell indices (row * cols + col), in answer order. */
	cells: number[];
	/** Word boundaries from the enumeration: a break after cells[i]. */
	breaks: { after: number; kind: 'space' | 'hyphen' }[];
}

const STORAGE_PREFIX = 'gatan:v1:';

/** Letters we accept as input: anything alphabetic, upper-cased Icelandic-style. */
export function normalizeLetter(ch: string): string | null {
	const up = ch.normalize('NFC').toLocaleUpperCase('is');
	return /^\p{L}$/u.test(up) ? up : null;
}

export class Game {
	readonly puzzle: Puzzle;
	readonly rows: number;
	readonly cols: number;
	readonly black: boolean[];
	readonly numbers: string[];
	readonly slots: Slot[];
	/** For each cell, the across/down slot it belongs to (if any). */
	readonly cellSlots: Partial<Record<Direction, Slot>>[];
	readonly solution: string[] | null;

	entries = $state<string[]>([]);
	/** Cells flagged wrong by Check; cleared when the cell changes. */
	wrong = $state<boolean[]>([]);
	cursor = $state(0);
	dir = $state<Direction>('across');

	constructor(puzzle: Puzzle) {
		this.puzzle = puzzle;
		const { rows, cols } = puzzle.size;
		this.rows = rows;
		this.cols = cols;
		const flat = puzzle.grid.flat();
		this.black = flat.map((v) => v === '#');
		this.numbers = flat.map((v) => (v === '#' ? '' : v));
		this.solution = puzzle.solution
			? puzzle.solution.flatMap((row) => [...row.normalize('NFC')])
			: null;

		this.cellSlots = flat.map(() => ({}));
		this.slots = [];
		for (const dir of ['across', 'down'] as const) {
			for (const clue of puzzle.clues[dir]) {
				const cells = Array.from({ length: clue.answer_length }, (_, i) =>
					dir === 'across'
						? clue.row * cols + clue.col + i
						: (clue.row + i) * cols + clue.col
				);
				const breaks: Slot['breaks'] = [];
				let pos = 0;
				for (const m of clue.enumeration.matchAll(/(\d+)([,-]?)/g)) {
					pos += Number(m[1]);
					if (m[2]) breaks.push({ after: pos - 1, kind: m[2] === '-' ? 'hyphen' : 'space' });
				}
				const slot: Slot = { id: `${clue.number}-${dir}`, dir, clue, cells, breaks };
				this.slots.push(slot);
				for (const c of cells) this.cellSlots[c][dir] = slot;
			}
		}

		this.entries = flat.map(() => '');
		this.wrong = flat.map(() => false);
		this.cursor = this.slots[0]?.cells[0] ?? 0;
		this.dir = this.slots[0]?.dir ?? 'across';
	}

	get active(): Slot {
		const s = this.cellSlots[this.cursor];
		return (s[this.dir] ?? s.across ?? s.down)!;
	}

	get filledCount(): number {
		return this.entries.filter((e, i) => e && !this.black[i]).length;
	}

	get whiteCount(): number {
		return this.black.filter((b) => !b).length;
	}

	get isComplete(): boolean {
		return this.filledCount === this.whiteCount;
	}

	get isSolved(): boolean {
		return !!this.solution && this.entries.every((e, i) => this.black[i] || e === this.solution![i]);
	}

	isSlotFilled(slot: Slot): boolean {
		return slot.cells.every((c) => this.entries[c]);
	}

	// --- navigation ---------------------------------------------------------

	/** Tap on a cell: select it; tapping the selected cell swaps direction. */
	tap(cell: number, allowToggle = true) {
		if (this.black[cell]) return;
		const s = this.cellSlots[cell];
		if (cell === this.cursor) {
			if (!allowToggle) return;
			const other: Direction = this.dir === 'across' ? 'down' : 'across';
			if (s[other]) this.dir = other;
		} else {
			this.cursor = cell;
			if (!s[this.dir]) this.dir = s.across ? 'across' : 'down';
		}
	}

	toggleDir() {
		this.tap(this.cursor);
	}

	selectSlot(slot: Slot, cell?: number) {
		this.dir = slot.dir;
		this.cursor = cell ?? slot.cells.find((c) => !this.entries[c]) ?? slot.cells[0];
	}

	stepSlot(delta: 1 | -1) {
		const i = this.slots.indexOf(this.active);
		const next = this.slots[(i + delta + this.slots.length) % this.slots.length];
		this.selectSlot(next);
	}

	/** Arrow keys: first press across the current direction turns, then moves. */
	arrow(dr: number, dc: number) {
		const want: Direction = dr === 0 ? 'across' : 'down';
		if (this.dir !== want && this.cellSlots[this.cursor][want]) {
			this.dir = want;
			return;
		}
		let r = Math.floor(this.cursor / this.cols) + dr;
		let c = (this.cursor % this.cols) + dc;
		while (r >= 0 && r < this.rows && c >= 0 && c < this.cols) {
			const cell = r * this.cols + c;
			if (!this.black[cell]) {
				this.cursor = cell;
				if (!this.cellSlots[cell][this.dir]) this.dir = this.dir === 'across' ? 'down' : 'across';
				return;
			}
			r += dr;
			c += dc;
		}
	}

	// --- editing ------------------------------------------------------------

	private set(cell: number, value: string) {
		if (this.entries[cell] !== value) {
			this.entries[cell] = value;
			this.wrong[cell] = false;
		}
	}

	/** Write a letter at the cursor and advance within the current word. */
	type(letter: string) {
		const slot = this.active;
		this.set(this.cursor, letter);
		const i = slot.cells.indexOf(this.cursor);
		if (i < slot.cells.length - 1) this.cursor = slot.cells[i + 1];
	}

	backspace() {
		const slot = this.active;
		if (this.entries[this.cursor]) {
			this.set(this.cursor, '');
			return;
		}
		const i = slot.cells.indexOf(this.cursor);
		if (i > 0) {
			this.cursor = slot.cells[i - 1];
			this.set(this.cursor, '');
		}
	}

	clearCell() {
		this.set(this.cursor, '');
	}

	clearAll() {
		this.entries = this.entries.map(() => '');
		this.wrong = this.wrong.map(() => false);
	}

	// --- checking -----------------------------------------------------------

	/** Flag wrong letters in the given cells; returns how many were wrong. */
	check(cells: number[]): number {
		if (!this.solution) return 0;
		let n = 0;
		for (const c of cells) {
			if (this.entries[c] && this.entries[c] !== this.solution[c]) {
				this.wrong[c] = true;
				n++;
			}
		}
		return n;
	}

	checkCell() {
		return this.check([this.cursor]);
	}

	checkWord() {
		return this.check(this.active.cells);
	}

	checkGrid() {
		return this.check(this.entries.map((_, i) => i).filter((i) => !this.black[i]));
	}

	// --- persistence --------------------------------------------------------

	private get storageKey() {
		return STORAGE_PREFIX + this.puzzle.id;
	}

	load() {
		const saved = readSaved(this.puzzle.id);
		if (!saved) return;
		if (saved.entries.length === this.entries.length) {
			this.entries = saved.entries.map((e, i) => (this.black[i] ? '' : (e ?? '')));
		}
		if (saved.wrong?.length === this.wrong.length) this.wrong = saved.wrong;
		if (typeof saved.cursor === 'number' && !this.black[saved.cursor]) this.cursor = saved.cursor;
		if (saved.dir === 'across' || saved.dir === 'down') this.dir = saved.dir;
		if (!this.cellSlots[this.cursor][this.dir]) this.toggleDir();
	}

	save() {
		try {
			localStorage.setItem(
				this.storageKey,
				JSON.stringify({
					entries: this.entries,
					wrong: this.wrong,
					cursor: this.cursor,
					dir: this.dir,
					filled: this.filledCount,
					total: this.whiteCount,
					updated: Date.now()
				} satisfies Saved)
			);
		} catch {
			// storage full or unavailable (private mode) — progress just won't persist
		}
	}
}

export interface Saved {
	entries: string[];
	wrong?: boolean[];
	cursor?: number;
	dir?: Direction;
	filled?: number;
	total?: number;
	updated?: number;
}

export function readSaved(id: string): Saved | null {
	try {
		const raw = localStorage.getItem(STORAGE_PREFIX + id);
		const saved = raw ? (JSON.parse(raw) as Saved) : null;
		return Array.isArray(saved?.entries) ? saved : null;
	} catch {
		return null;
	}
}
