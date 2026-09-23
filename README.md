# 3d-print-learning

Учебный проект: печать на Bambu Lab A1 mini и моделирование под печать во Fusion. Здесь только выводы — уроки, решения, проблемные печати с настройками. Правила для агента — `CLAUDE.md`, факты — `CONTEXT.md`.

## Структура

| Папка | Что |
| --- | --- |
| `.claude/skills/print-model/` | как агент готовит любую модель к печати: шаги + справочники по качеству нарезки и калибровке пластика |
| `lessons/` | итоги уроков: симптом → диагноз → что поменяли → результат |
| `docs/adr/` | решения по профилям и инструментам |
| `prints/` | печати с настройками (3MF + diff + фото) |
| `profiles/` | пользовательские пресеты Studio (`user/`) и снимки базовых (`baseline/`) |
| `tools/` | чтение состояния Bambu Studio и Fusion |

## Руководство по Bambu Studio

`docs/guide/bambu-studio-guide.pdf` — где какая опция в Studio 02.08, что она делает, как опции влияют друг на друга, калибровка, симптом → что крутить; со скриншотами. Исходник `docs/guide/guide.html`, пересборка: `uv run --with playwright --with pypdf python docs/guide/build.py`.

## Уроки

1. `lessons/01-walls-calibration.md` — горбы на стенках коробки: состав стола, переходы геометрии, шов. Коробка закрыта 17.09 на пакете скилла (`prints/2026-09-17-box-skill-test/`): остаток — кромки окна, лечит фаска в дизайне; тест 1 (scarf seam) ждёт.
2. `lessons/02-threads.md` — резьба под FDM во Fusion: best practices, лестница зазоров.
3. `lessons/03-filament-calibration.md` — SUNLU PLA откалиброван: 220 °C · flow 0.98 · MVS 12 → пресет `SUNLU PLA @BBL A1M`.
4. `lessons/04-makerworld-presets.md` — проект с MakerWorld приносит принтер/филамент/процесс автора; принтер и филамент — свои, из процесса переносить только авторские правки (`bbs_project.py retarget`).
5. `lessons/05-steps-not-speed.md` — «рябь» на пологих скатах оказалась ступеньками слоёв, а не скоростью; лечит тонкий слой на этой полосе (`mesh_slopes.py` → `bbs_project.py ranges`).
6. `lessons/06-matte-calibration.md` — SUNLU PLA Matte откалиброван: 225 °C · flow 0.975 · MVS 24 → пресет `SUNLU Matte @BBL A1M`.

Очередь тем: гладкая верхняя поверхность (ironing, top layers), скругления и оверхенги, корпус с защёлками (snap-fit под PETG/PLA), допуски и посадки, шов (seam / scarf), VFA-тест.
