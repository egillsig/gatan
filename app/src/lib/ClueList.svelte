<script lang="ts">
	import type { Game, Slot } from './game.svelte';

	let {
		game,
		onpick,
		onclose
	}: { game: Game; onpick: (slot: Slot) => void; onclose?: () => void } = $props();

	let unansweredOnly = $state(false);

	const sections = [
		{ dir: 'across', title: 'Lárétt' },
		{ dir: 'down', title: 'Lóðrétt' }
	] as const;

	function pattern(slot: Slot) {
		return slot.cells.map((c) => game.entries[c] || '·').join('');
	}

	let list: HTMLElement;
	$effect(() => {
		const id = game.active.id;
		list?.querySelector(`[data-slot="${id}"]`)?.scrollIntoView({ block: 'nearest' });
	});
</script>

<div class="cluelist">
	<header>
		<label>
			<input type="checkbox" bind:checked={unansweredOnly} />
			Aðeins ósvaraðar
		</label>
		{#if onclose}
			<button class="close" onclick={onclose} aria-label="Loka">✕</button>
		{/if}
	</header>
	<div class="scroll" bind:this={list}>
		{#each sections as { dir, title } (dir)}
			<h2>{title}</h2>
			<ol>
				{#each game.slots.filter((s) => s.dir === dir) as slot (slot.id)}
					{@const filled = game.isSlotFilled(slot)}
					{#if !unansweredOnly || !filled || slot === game.active}
						<li>
							<button
								data-slot={slot.id}
								class:active={slot === game.active}
								class:filled
								onclick={() => onpick(slot)}
							>
								<span class="n">{slot.clue.number}</span>
								<span class="t">
									{slot.clue.text} <span class="enum">({slot.clue.enumeration})</span>
									<span class="pattern">{pattern(slot)}</span>
								</span>
							</button>
						</li>
					{/if}
				{/each}
			</ol>
		{/each}
	</div>
</div>

<style>
	.cluelist {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		background: var(--paper);
	}
	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid var(--rule);
	}
	label {
		display: flex;
		gap: 0.4rem;
		align-items: center;
		font-size: 0.9rem;
	}
	.close {
		font-size: 1.1rem;
		padding: 0.4rem 0.6rem;
	}
	.scroll {
		overflow-y: auto;
		flex: 1;
		padding: 0 0.5rem 1rem;
		overscroll-behavior: contain;
	}
	h2 {
		font-size: 0.8rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin: 1rem 0.5rem 0.25rem;
	}
	ol {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	li button {
		display: flex;
		gap: 0.6rem;
		width: 100%;
		text-align: left;
		padding: 0.45rem 0.5rem;
		border-radius: 6px;
		font-size: 0.95rem;
		line-height: 1.35;
	}
	li button.active {
		background: var(--word);
	}
	li button.filled .t {
		color: var(--muted);
	}
	.n {
		font-weight: 700;
		min-width: 1.6em;
		text-align: right;
	}
	.enum {
		white-space: nowrap;
	}
	.pattern {
		display: block;
		font-family: var(--mono);
		font-size: 0.8rem;
		letter-spacing: 0.15em;
		color: var(--muted);
		margin-top: 0.1rem;
	}
</style>
