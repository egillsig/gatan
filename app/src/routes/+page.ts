import { loadPuzzle, puzzleIds } from '#lib/puzzles.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	const puzzles = await Promise.all(puzzleIds.map(loadPuzzle));
	return {
		puzzles: puzzles.map((p) => ({
			id: p!.id,
			title: p!.title,
			date: p!.date,
			hasSolution: !!p!.solution
		}))
	};
};
