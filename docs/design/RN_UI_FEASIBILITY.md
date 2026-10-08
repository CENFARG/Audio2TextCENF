# Factibilidad UI/UX del prototipo landing en React Native

> Referencia visual: `docs/design/landing_prototipo.html` (+ preview `landing_preview.png`)
> Veredicto: **100% factible en React Native** — cada elemento del prototipo tiene equivalente directo.

## Design tokens extraídos del prototipo

| Token | Valor | Uso |
|---|---|---|
| bg | `#080d18` | Fondo base (dark navy) |
| surface / surface-2 | `#101827` / `#141f32` | Cards y superficies |
| text / muted | `#f2f7ff` / `#9aaac2` | Texto principal/secundario |
| cyan | `#56e5e3` | Acento primario (waveform, CTAs) |
| blue | `#6b8cff` | Acento secundario |
| violet | `#ad82ff` | Acento terciario (gradientes) |

Tipografía: sans moderna (Inter o similar), títulos grandes con gradiente.

## Mapeo elemento → React Native

| Elemento del prototipo | Implementación RN |
|---|---|
| Texto con gradiente ("Tu voz. En texto.") | `MaskedView` + `expo-linear-gradient` |
| Botones CTA con gradiente cian | `expo-linear-gradient` + Pressable |
| Waveform decorativa (cian/violeta) | `react-native-svg` path + `reanimated`; en vivo: visualización desde mic |
| Efecto typewriter "TRANSCRIPCIÓN EN VIVO" | `reanimated` + intervalo |
| Cards flotantes con borde | RN styling (border + borderRadius + shadow/elevation) |
| Badges/chips ("Conectado", "Atajos globales") | View + estilo |
| Fade-ins al scroll ("Menos fricción...") | `reanimated` scroll hooks (useAnimatedScrollHandler) |
| Dark theme completo | Theme object con estos tokens (sin dependencias) |

## Doble uso del prototipo

1. **Landing web publicable tal cual**: es HTML standalone → GitHub Pages = presencia web inmediata, costo cero, sin esperar RN.
2. **Design system de referencia para la app RN** (Fase 1/2 del plan H): el mockup de la app DENTRO de la landing es esencialmente el diseño objetivo de la app móvil.

## Conclusión

No hay ningún elemento del prototipo que RN no pueda reproducir. La estética "hermosa" que ves es CSS 2D estándar (gradientes, glass, waveforms) — todo tiene librería madura en el ecosistema RN/Expo.
