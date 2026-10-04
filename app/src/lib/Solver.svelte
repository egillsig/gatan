<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { resolve } from '$app/paths';
	import { Game, normalizeLetter, type Slot } from './game.svelte';
	import { formatDate, type Puzzle } from './puzzles';
	import Grid from './Grid.svelte';
	import ClueList from './ClueList.svelte';

	let { puzzle }: { puzzle: Puzzle } = $props();

	const game = untrack(() => new Game(puzzle));

	// The hidden input always holds this one character so that Backspace on an
	// "empty" field still produces an input event on mobile keyboards.
	const SENTINEL = '​';

	let input: HTMLInputElement;
	let loaded = $state(false);
	let showList = $state(false);
	let showMenu = $state(false);
	let confirmClear = $state(false);
	let toast = $state<string | null>(null);
	let toastTimer: ReturnType<typeof setTimeout>;

	function say(msg: string) {
		toast = msg;
		clearTimeout(toastTimer);
		toastTimer = setTimeout(() => (toast = null), 2500);
	}

	function focusInput() {
		input?.focus({ preventScroll: true });
		resetInput();
	}

	function resetInput() {
		if (!input) return;
		input.value = SENTINEL;
		input.setSelectionRange(1, 1);
	}

	// --- typing ---------------------------------------------------------------

	function onkeydown(e: KeyboardEvent) {
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		const keys: Record<string, () => void> = {
			Backspace: () => game.backspace(),
			Delete: () => game.clearCell(),
			ArrowLeft: () => game.arrow(0, -1),
			ArrowRight: () => game.arrow(0, 1),
			ArrowUp: () => game.arrow(-1, 0),
			ArrowDown: () => game.arrow(1, 0),
			Tab: () => game.stepSlot(e.shiftKey ? -1 : 1),
			Enter: () => game.stepSlot(1),
			' ': () => game.toggleDir()
		};
		const action = keys[e.key];
		if (!action) return; // letters arrive through the input event
		e.preventDefault();
		action();
	}

	function oninput(e: Event) {
		const ev = e as InputEvent;
		const value = input.value;
		const letters = [...value.replaceAll(SENTINEL, '')]
			.map(normalizeLetter)
			.filter((l): l is string => !!l);

		if (letters.length) {
			for (const l of letters) game.type(l);
		} else if (!value.includes(SENTINEL)) {
			game.backspace();
		} else if (ev.isComposing) {
			return; // e.g. a dead key (´) waiting for its letter — leave the composition alone
		}
		resetInput();
	}

	// --- selection ------------------------------------------------------------

	function onTap(cell: number) {
		// The first tap after the keyboard was away just (re)selects the cell.
		game.tap(cell, document.activeElement === input);
		focusInput();
	}

	function pick(slot: Slot) {
		game.selectSlot(slot);
		showList = false;
		focusInput();
	}

	// Swipe on the clue strip moves between clues.
	let swipeX: number | null = null;
	function stripDown(e: PointerEvent) {
		swipeX = e.clientX;
	}
	function stripUp(e: PointerEvent) {
		if (swipeX === null) return;
		const dx = e.clientX - swipeX;
		swipeX = null;
		if (Math.abs(dx) > 40) game.stepSlot(dx < 0 ? 1 : -1);
		focusInput();
	}

	// --- check ----------------------------------------------------------------

	function runCheck(kind: 'cell' | 'word' | 'grid') {
		showMenu = false;
		const wrong = kind === 'cell' ? game.checkCell() : kind === 'word' ? game.checkWord() : game.checkGrid();
		if (wrong) say(wrong === 1 ? '1 rangur stafur' : `${wrong} rangir stafir`);
		else say(kind === 'grid' && game.isSolved ? 'Allt rétt!' : 'Ekkert rangt');
		focusInput();
	}

	function clearAll() {
		if (!confirmClear) {
			confirmClear = true;
			return;
		}
		game.clearAll();
		confirmClear = false;
		showMenu = false;
	}

	// --- lifecycle ------------------------------------------------------------

	onMount(() => {
		game.load();
		loaded = true;

		// Keep the layout sized to the *visible* viewport so the clue strip sits
		// right above the on-screen keyboard.
		const vv = window.visualViewport;
		const root = document.documentElement;
		const fit = () => {
			if (!vv) return;
			root.style.setProperty('--app-h', `${vv.height}px`);
			root.style.setProperty('--app-top', `${vv.offsetTop}px`);
		};
		fit();
		vv?.addEventListener('resize', fit);
		vv?.addEventListener('scroll', fit);

		if (matchMedia('(hover: hover) and (pointer: fine)').matches) focusInput();

		return () => {
			vv?.removeEventListener('resize', fit);
			vv?.removeEventListener('scroll', fit);
		};
	});

	$effect(() => {
		if (loaded) game.save();
	});

	let wasSolved = false;
	$effect(() => {
		const solved = game.isSolved;
		if (loaded && solved && !wasSolved) say('Til hamingju! Krossgátan er rétt leyst.');
		wasSolved = solved;
	});

	const active = $derived(game.active);
</script>

<svelte:head>
	<title>{puzzle.title} · {formatDate(puzzle.date)}</title>
</svelte:head>

<div class="app">
	<header class="top">
		<a class="back" href={resolve('/')} aria-label="Allar gátur">‹</a>
		<div class="title">
			<strong>{puzzle.title}</strong>
			<span>{formatDate(puzzle.date)}</span>
		</div>
		<button class="listbtn" onclick={() => (showList = true)}>Vísbendingar</button>
		<div class="menuwrap">
			<button onclick={() => ((showMenu = !showMenu), (confirmClear = false))} aria-expanded={showMenu}>
				Athuga ▾
			</button>
			{#if showMenu}
				<div class="menu" role="menu">
					{#if game.solution}
						<button role="menuitem" onclick={() => runCheck('cell')}>Athuga reit</button>
						<button role="menuitem" onclick={() => runCheck('word')}>Athuga orð</button>
						<button role="menuitem" onclick={() => runCheck('grid')}>Athuga allt</button>
					{:else}
						<p class="note">Lausnin er ekki komin fyrir þessa gátu, svo ekki er hægt að athuga.</p>
					{/if}
					<hr />
					<button role="menuitem" class="danger" onclick={clearAll}>
						{confirmClear ? 'Ertu viss? Hreinsa allt' : 'Hreinsa allt'}
					</button>
				</div>
			{/if}
		</div>
	</header>

	<main>
		<div class="gridwrap">
			<div class="gridbox" style:aspect-ratio="{game.cols} / {game.rows}">
				<Grid {game} ontap={onTap} />
			</div>
		</div>
		<aside class="side">
			<ClueList {game} onpick={pick} />
		</aside>
	</main>

	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="strip" onpointerdown={stripDown} onpointerup={stripUp}>
		<button class="nav" onpointerdown={(e) => e.stopPropagation()} onclick={() => (game.stepSlot(-1), focusInput())} aria-label="Fyrri vísbending">‹</button>
		<div class="clue">
			<span class="label">{active.clue.number} {active.dir === 'across' ? 'lárétt' : 'lóðrétt'}</span>
			<span class="text">{active.clue.text} <span class="enum">({active.clue.enumeration})</span></span>
		</div>
		<button class="nav" onpointerdown={(e) => e.stopPropagation()} onclick={() => (game.stepSlot(1), focusInput())} aria-label="Næsta vísbending">›</button>
	</div>


	<input
		bind:this={input}
		class="hidden-input"
		type="text"
		value={SENTINEL}
		autocomplete="off"
		autocorrect="off"
		autocapitalize="characters"
		spellcheck="false"
		inputmode="text"
		enterkeyhint="next"
		aria-label="Sláðu inn staf"
		{onkeydown}
		{oninput}
	/>

	{#if toast}
		<div class="toast" role="status">{toast}</div>
	{/if}
</div>

{#if showList}
	<div class="sheet">
		<ClueList {game} onpick={pick} onclose={() => (showList = false)} />
	</div>
{/if}

<style>
	.app {
		position: fixed;
		left: 0;
		right: 0;
		top: var(--app-top, 0px);
		height: var(--app-h, 100dvh);
		display: flex;
		flex-direction: column;
		padding-top: env(safe-area-inset-top, 0px);
		background: var(--paper);
	}
	.top {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 0.75rem;
		border-bottom: 1px solid var(--rule);
	}
	.back {
		font-size: 1.6rem;
		line-height: 1;
		text-decoration: none;
		color: inherit;
		padding: 0 0.4rem 0.15rem 0;
	}
	.title {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		line-height: 1.15;
	}
	.title strong {
		font-family: var(--serif);
		font-size: 1.1rem;
	}
	.title span {
		font-size: 0.75rem;
		color: var(--muted);
	}
	.top button {
		font-size: 0.85rem;
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--rule);
		border-radius: 999px;
		background: var(--cell);
	}
	.menuwrap {
		position: relative;
	}
	.menu {
		position: absolute;
		right: 0;
		top: calc(100% + 0.4rem);
		z-index: 20;
		min-width: 13rem;
		background: var(--cell);
		border: 1px solid var(--rule);
		border-radius: 10px;
		box-shadow: 0 8px 24px rgb(0 0 0 / 0.15);
		padding: 0.3rem;
		display: flex;
		flex-direction: column;
	}
	.menu button {
		border: 0;
		border-radius: 6px;
		text-align: left;
		padding: 0.6rem 0.75rem;
		font-size: 0.95rem;
	}
	.menu button:hover {
		background: var(--word);
	}
	.menu .danger {
		color: var(--wrong);
	}
	.menu hr {
		border: 0;
		border-top: 1px solid var(--rule);
		margin: 0.3rem 0;
	}
	.note {
		margin: 0.4rem 0.75rem;
		font-size: 0.85rem;
		color: var(--muted);
	}

	main {
		flex: 1;
		min-height: 0;
		display: flex;
	}
	.gridwrap {
		flex: 1;
		min-width: 0;
		container-type: size;
		display: grid;
		place-items: center;
		padding: 4px;
	}
	.gridbox {
		width: min(100cqw, 100cqh);
		max-width: 100%;
		max-height: 100%;
	}
	.side {
		display: none;
	}

	.strip {
		display: flex;
		align-items: stretch;
		background: var(--strip);
		color: var(--strip-ink);
		min-height: 3.6rem;
		padding-bottom: env(safe-area-inset-bottom, 0px);
		touch-action: pan-y;
		user-select: none;
		-webkit-user-select: none;
	}
	.strip .nav {
		flex: none;
		width: 2.6rem;
		font-size: 1.6rem;
		color: inherit;
	}
	.clue {
		flex: 1;
		min-width: 0;
		padding: 0.4rem 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		line-height: 1.3;
	}
	.clue .label {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.75;
	}
	.clue .text {
		font-size: 0.95rem;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.enum {
		white-space: nowrap;
	}


	.hidden-input {
		position: absolute;
		top: 0;
		left: 0;
		width: 1px;
		height: 1px;
		opacity: 0;
		font-size: 16px; /* prevents iOS zoom-on-focus */
		caret-color: transparent;
		border: 0;
		padding: 0;
	}

	.toast {
		position: absolute;
		left: 50%;
		top: 4rem;
		transform: translateX(-50%);
		background: var(--strip);
		color: var(--strip-ink);
		padding: 0.6rem 1rem;
		border-radius: 999px;
		font-size: 0.95rem;
		box-shadow: 0 6px 20px rgb(0 0 0 / 0.2);
		z-index: 30;
		white-space: nowrap;
	}

	.sheet {
		position: fixed;
		inset: 0;
		z-index: 40;
		padding-top: env(safe-area-inset-top, 0px);
		background: var(--paper);
	}

	@media (min-width: 900px) {
		.side {
			display: block;
			width: 24rem;
			border-left: 1px solid var(--rule);
		}
		.listbtn {
			display: none;
		}
		.gridwrap {
			padding: 1rem;
		}
	}
</style>
