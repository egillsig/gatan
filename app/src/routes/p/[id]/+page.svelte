<script lang="ts">
	import Solver from '#lib/Solver.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

{#key data.puzzle.id}
	<Solver puzzle={data.puzzle} />
{/key}
