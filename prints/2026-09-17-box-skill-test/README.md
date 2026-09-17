# 2026-09-17 — коробка из урока 1 на пакете скилла print-model

Первая полевая проверка скилла: та же прямоугольная коробка Body5 (67.6 × 51.6 × 44), что утром 16.09 дала горизонтальные полосы на 6.2 / 18 / 34.2 мм (`lessons/01`). Сравнение — с той утренней печатью, не с одной переменной: проверяется пакет целиком.

- Источник: `prints/2026-09-16-box/test2-box-3walls.3mf` → `retarget` на `SUNLU PLA @BBL A1M` (калиброванный: 220 °C, flow 0.98, MVS 12) + `variant --set`.
- Что стоит поверх `0.20mm Standard @BBL A1M`: `wall_loops 3`, `precise_outer_wall 1` (из теста 2 урока 1); «всегда»-ключи скилла — `resolution 0.004`, `slice_closing_radius 0.01`, `reduce_crossing_wall 1`, `max_travel_detour_distance 300`; против линии пола — `wall_sequence = inner-outer-inner wall`.
- Не трогал: вентилятор 60–80 %, `slow_down_for_layer_cooling`, `infill_wall_overlap 15 %`, `ensure_vertical_shell_thickness` — следующие кандидаты, если полосы останутся.
- CLI-нарезка: **33 мин 32 с, 220 слоёв**. Файл: `~/Downloads/Box-skill-test.gcode.3mf`, на SD как `Box-skill-test.gcode.3mf`; проект — `Box-skill-test.3mf` там же.
- Ожидание: полоса на 18 мм исчезает (коробка одна на столе, время слоя ровное), полосы на 6.2 и 34.2 (внутренние полки) — слабеют от `inner-outer-inner` и precise wall. Если остаются — это дизайн: фаска по рёбрам полок (clean-prints §1).
- Результат: —
