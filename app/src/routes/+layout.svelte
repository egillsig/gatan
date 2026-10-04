<script lang="ts">
	import { asset } from '$app/paths';
	import type { LayoutProps } from './$types';
	import './app.css';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={asset('icon.svg')} type="image/svg+xml" />
	<link rel="apple-touch-icon" href={asset('apple-touch-icon.png')} />
	<link rel="manifest" href={asset('manifest.webmanifest')} />
</svelte:head>

{@render children()}
