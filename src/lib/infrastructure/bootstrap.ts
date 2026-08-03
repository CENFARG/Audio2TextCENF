/**
 * Bootstrap core-cenf-ts BootstrapOrchestrator.
 * Wire managers: Config, Log, I18n, Cache, Health, HttpClient, Secret, Validation.
 */
import { BootstrapOrchestrator } from 'core-cenf-ts';

let orchestrator: BootstrapOrchestrator | null = null;

export async function bootstrap() {
  try {
    orchestrator = new BootstrapOrchestrator();
    await orchestrator.startup();
    console.log('core-cenf-ts bootstrapped successfully');
    return orchestrator;
  } catch (e) {
    console.warn('core-cenf-ts bootstrap failed:', e);
    return null;
  }
}

export function getOrchestrator() {
  return orchestrator;
}