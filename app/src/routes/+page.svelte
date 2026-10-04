<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import { readSaved } from '#lib/game.svelte.ts';
	import { formatDate } from '#lib/puzzles.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let progress = $state<Record<string, number>>({});
	onMount(() => {
		for (const p of data.puzzles) {
			const s = readSaved(p.id);
			if (s?.filled && s.total) progress[p.id] = Math.round((100 * s.filled) / s.total);
		}
	});
</script>

<svelte:head>
	<title>Krossgátan</title>
</svelte:head>

<div class="page">
	<h1>Krossgátan</h1>
	<p class="sub">Krossgáta Morgunblaðsins á sunnudögum, til að leysa í símanum.</p>
	<ul>
		{#each data.puzzles as p, i (p.id)}
			<li>
				<a href={resolve('/p/[id]', { id: p.id })}>
					<span class="date">{formatDate(p.date)}</span>
					{#if i === 0}<span class="tag">Nýjust</span>{/if}
					<span class="meta">
						{#if progress[p.id] !== undefined}{progress[p.id]}% útfyllt{:else}Óbyrjuð{/if}
						{#if p.hasSolution}· hægt að athuga{/if}
					</span>
				</a>
			</li>
		{/each}
	</ul>
</div>

<style>
	.page {
		max-width: 36rem;
		margin: 0 auto;
		padding: calc(2rem + env(safe-area-inset-top, 0px)) 1rem 3rem;
	}
	h1 {
		font-family: var(--serif);
		font-size: 2.2rem;
		margin: 0;
	}
	.sub {
		color: var(--muted);
		margin: 0.3rem 0 1.5rem;
	}
	ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	a {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.3rem 0.6rem;
		padding: 1rem;
		background: var(--cell);
		border: 1px solid var(--rule);
		border-radius: 10px;
		color: inherit;
		text-decoration: none;
	}
	a:hover {
		border-color: var(--ink);
	}
	.date {
		font-family: var(--serif);
		font-size: 1.2rem;
		font-weight: 600;
	}
	.tag {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		background: var(--strip);
		color: var(--strip-ink);
		padding: 0.15rem 0.45rem;
		border-radius: 4px;
	}
	.meta {
		width: 100%;
		font-size: 0.85rem;
		color: var(--muted);
	}
</style>
