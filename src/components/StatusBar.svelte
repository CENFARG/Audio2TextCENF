<script lang="ts">
  import { listen } from "@tauri-apps/api/event";

  interface HealthData {
    alive: boolean;
    uptime: number;
  }

  let alive = $state(false);
  let uptime = $state(0);
  let connected = $state(false);

  function formatUptime(seconds: number): string {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  $effect(() => {
    const unlisten = listen<HealthData>("health_check", (event) => {
      alive = event.payload.alive;
      uptime = event.payload.uptime;
      connected = true;
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  });
</script>

<div class="status-bar">
  <div class="status-item">
    <span class="dot" class:alive></span>
    <span>Sidecar</span>
  </div>

  <div class="status-item">
    <span class="label">Uptime:</span>
    <span>{formatUptime(uptime)}</span>
  </div>

  <div class="status-item">
    <span class="label">Connection:</span>
    <span class:connected>{connected ? "OK" : "—"}</span>
  </div>
</div>

<style>
  .status-bar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 0.4rem 1rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border);
    font-size: 0.7rem;
    color: var(--text-secondary);
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #555;
    transition: background 0.3s;
  }

  .dot.alive {
    background: var(--accent-green);
    box-shadow: 0 0 4px var(--accent-green);
  }

  .label {
    opacity: 0.7;
  }

  .connected {
    color: var(--accent-green);
  }
</style>
