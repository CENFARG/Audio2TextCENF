/**
 * Bootstrap core-cenf-ts BootstrapOrchestrator.
 * Wire managers: Config, Log, I18n, Cache, Health, HttpClient, Secret, Validation.
 *
 * NOTE: core-cenf-ts is not yet installed. This module is a no-op placeholder.
 * When the package is available, uncomment the import and initialization.
 */

let orchestrator: unknown = null;

export async function bootstrap() {
  try {
    // TODO: Uncomment when core-cenf-ts is installed
    // import { BootstrapOrchestrator } from 'core-cenf-ts';
    // orchestrator = new BootstrapOrchestrator();
    // await orchestrator.startup();
    console.log('core-cenf-ts bootstrap skipped (package not installed)');
    return orchestrator;
  } catch (e) {
    console.warn('core-cenf-ts bootstrap failed:', e);
    return null;
  }
}

export function getOrchestrator() {
  return orchestrator;
}