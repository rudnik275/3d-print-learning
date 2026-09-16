# Урок 3 — калибровка филамента (SUNLU PLA Bone White)

Статус: идёт (2026-09-16). Решение о профилях — `docs/adr/0002-filament-profiles.md`.

## Ход

| Шаг | Стол | Результат |
| --- | --- | --- |
| Flow Rate coarse (−20…+20 %) при 220 °C | `prints/2026-09-16-calib/flow-pass1.3mf`, 27 мин | печатается |
| Башня температур 230 → 195 | `temp-tower-230-195.3mf`, 1 ч 05 | нарезана, ждёт стола |
| Flow Rate fine (−9…0 % от coarse) на выбранной T | `flow2` — собрать после coarse | — |
| Max Volumetric Speed 4 → 30 мм³/с | `mvs-4-30.gcode.3mf` (цилиндр, spiral), ~15 мин, с SD | печатается |
| Пресет `SUNLU PLA @BBL A1M` | `profiles/user/` → Import Configs | — |

## Выводы

—
