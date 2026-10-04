<script lang="ts">
	import type { Game } from './game.svelte';

	let { game, ontap }: { game: Game; ontap: (cell: number) => void } = $props();

	const S = 32; // viewBox units per cell
	const width = $derived(game.cols * S);
	const height = $derived(game.rows * S);

	let svg: SVGSVGElement;

	const activeCells = $derived(new Set(game.active.cells));

	// Word-break bars for multi-word answers, e.g. (2,4,4).
	const bars = $derived(game.slots.flatMap((slot) =>
		slot.breaks.map(({ after, kind }) => {
			const cell = slot.cells[after];
			const r = Math.floor(cell / game.cols);
			const c = cell % game.cols;
			return { across: slot.dir === 'across', kind, x: (c + 1) * S, y: (r + 1) * S, r, c };
		})
	));

	function onclick(e: MouseEvent) {
		const rect = svg.getBoundingClientRect();
		// viewBox has a 1-unit frame around the cells
		const c = Math.floor((((e.clientX - rect.left) / rect.width) * (width + 2) - 1) / S);
		const r = Math.floor((((e.clientY - rect.top) / rect.height) * (height + 2) - 1) / S);
		if (r < 0 || r >= game.rows || c < 0 || c >= game.cols) return;
		ontap(r * game.cols + c);
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
<svg
	bind:this={svg}
	viewBox="-1 -1 {width + 2} {height + 2}"
	role="application"
	aria-label="Krossgátureitir"
	{onclick}
>
	<rect x="-1" y="-1" width={width + 2} height={height + 2} class="frame" />
	{#each game.black as isBlack, i (i)}
		{@const x = (i % game.cols) * S}
		{@const y = Math.floor(i / game.cols) * S}
		{#if !isBlack}
			<rect
				{x}
				{y}
				width={S}
				height={S}
				class="cell"
				class:word={activeCells.has(i)}
				class:cursor={i === game.cursor}
			/>
			{#if game.numbers[i]}
				<text x={x + 2} y={y + 9} class="num">{game.numbers[i]}</text>
			{/if}
			{#if game.entries[i]}
				<text x={x + S / 2} y={y + S / 2 + 2} class="letter" class:wrong={game.wrong[i]}
					>{game.entries[i]}</text
				>
				{#if game.wrong[i]}
					<line x1={x + 4} y1={y + S - 4} x2={x + S - 4} y2={y + 4} class="slash" />
				{/if}
			{/if}
		{/if}
	{/each}
	{#each bars as b, i (i)}
		{#if b.kind === 'space'}
			{#if b.across}
				<line x1={b.x} y1={b.y - S} x2={b.x} y2={b.y} class="bar" />
			{:else}
				<line x1={b.x - S} y1={b.y} x2={b.x} y2={b.y} class="bar" />
			{/if}
		{:else if b.across}
			<line x1={b.x - 5} y1={b.y - S / 2} x2={b.x + 5} y2={b.y - S / 2} class="bar" />
		{:else}
			<line x1={b.x - S / 2} y1={b.y - 5} x2={b.x - S / 2} y2={b.y + 5} class="bar" />
		{/if}
	{/each}
</svg>

<style>
	svg {
		display: block;
		width: 100%;
		height: 100%;
		touch-action: manipulation;
		user-select: none;
		-webkit-user-select: none;
		-webkit-tap-highlight-color: transparent;
		cursor: pointer;
	}
	.frame {
		fill: var(--black);
	}
	.cell {
		fill: var(--cell);
		stroke: var(--black);
		stroke-width: 1;
	}
	.cell.word {
		fill: var(--word);
	}
	.cell.cursor {
		fill: var(--cursor);
	}
	.num {
		font-size: 8.5px;
		fill: var(--ink);
		font-family: var(--sans);
	}
	.letter {
		font-size: 19px;
		font-weight: 500;
		text-anchor: middle;
		dominant-baseline: middle;
		fill: var(--ink);
		font-family: var(--sans);
	}
	.letter.wrong {
		fill: var(--wrong);
	}
	.slash {
		stroke: var(--wrong);
		stroke-width: 1.5;
	}
	.bar {
		stroke: var(--black);
		stroke-width: 4;
	}
</style>
