# profiles

- `user/` — копии пользовательских пресетов из `~/Library/Application Support/BambuStudio/user/<id>/` (только overrides поверх `inherits`). Обновлять руками после изменений в Studio.
- `baseline/` — полностью раскрытые системные пресеты Studio 02.08.02.61 на 2026-09-16 (`tools/bbs_resolve.py`), чтобы видеть, от чего отталкиваемся.
- `orca/` — те же пресеты для OrcaSlicer 2.4.2 (с 2026-10-03 основной слайсер Димы), копия того, что лежит в `~/Library/Application Support/OrcaSlicer/user/default/`. Пересобираются из Studio командой `tools/orca_presets.py` — правка в Studio, затем скрипт, затем перезапуск Orca; руками не редактировать. Что скрипт переносит и почему мосты в Orca записаны иначе, чем в Studio (толстые мосты, внутренний поток = 1 / поток моста), — в его докстринге.
