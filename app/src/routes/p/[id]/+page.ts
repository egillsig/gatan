import { error } from '@sveltejs/kit';
import { loadPuzzle, puzzleIds } from '#lib/puzzles.ts';
import type { EntryGenerator, PageLoad } from './$types';

export const entries: EntryGenerator = () => puzzleIds.map((id) => ({ id }));

export const load: PageLoad = async ({ params }) => {
	const puzzle = await loadPuzzle(params.id);
	if (!puzzle) error(404, 'Gáta fannst ekki');
	return { puzzle };
};
