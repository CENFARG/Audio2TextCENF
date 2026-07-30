/**
 * Bootstrap core-cenf-ts BootstrapOrchestrator.
 * Wire managers: Config, Log, I18n, Cache, Health, HttpClient, Secret, Validation.
 */
export async function bootstrap() {
  try {
    const pkg = '@cenf/core-cenf-ts';
    const { BootstrapOrchestrator } = await import(pkg);
    const orchestrator = new BootstrapOrchestrator();
    await orchestrator.startup();
    console.log('core-cenf-ts bootstrapped successfully');
    return orchestrator;
  } catch (e) {
    console.warn('core-cenf-ts not available — using mock bootstrap');
    return null;
  }
}