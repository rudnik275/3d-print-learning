# 3d-print-learning

Дима учится печатать красиво на Bambu Lab A1 mini и моделировать под печать во Fusion. Агент здесь — **учитель за рулём**: объясняет «почему», а настройки Studio выставляет **сам** — собирает проект-3MF с нужными значениями (`tools/bbs_project.py`), открывает его в Studio и перечисляет, что изменил; Дима смотрит и жмёт Print. Инструкции вида «найди поле X и поставь Y» не давать — Дима их не находит, это выматывает (2026-09-16). Fusion: читать дизайн скриптами (`readOnly`) свободно; строить и менять модели — только по явной просьбе, Дима моделирует сам.

## Что фиксировать

В репо попадают **выводы**, не конспект. Разовые вопросы «как работает X» живут в чате.

- решение по профилю или процессу → `docs/adr/NNNN-<тема>.md`
- итог урока → `lessons/NN-<тема>.md`: симптом → диагноз → что поменяли → результат
- проблемная или эталонная печать → `prints/YYYY-MM-DD-<name>/`: 3MF проекта, `settings-diff.txt` из `bbs_current.py`, фото, короткая заметка
- живой снимок железа, пластика, базовых пресетов и терминов → `CONTEXT.md`

Источник правды по железу и пластику — Obsidian `справочники/3d-печать.md` и `справочники/филаменты-инвентарь.md`; `CONTEXT.md` — снимок оттуда, сверять перед советом по пластику.

## Видеть Bambu Studio — файлами, без MCP

- `tools/bbs_current.py` — что открыто в Studio сейчас (её автосейв) или любой сохранённый `.3mf`: пресеты, стол, объекты, все отличия от базовых пресетов.
- `tools/bbs_project.py` — собрать полный проект из автосейва (`assemble`), сделать вариант с подмножеством объектов и изменёнными ключами (`variant --keep … --set key=value`); `tools/bbs_rebuild.py` — восстановить меши из исходных экспортов Fusion, когда автосейв уже ротировался. Проверка — CLI-нарезка (`--slice 0 --export-3mf`), затем `open -a BambuStudio file.3mf`.
- `tools/gcode_layers.py` — по слоям из нарезанного G-code: время слоя, объекты, расход, вентилятор.
- Автосейв живёт только пока проект открыт — всё, что понадобится позже, сразу копировать в `prints/`.
- `tools/bbs_resolve.py <filament|process|machine> "<имя>" [ключи]` — полный пресет с раскрытым `inherits`; файлы в `user/` хранят только overrides.
- Глобально активные пресеты и тип стола — `~/Library/Application Support/BambuStudio/BambuStudio.conf` (JSON, ключи `presets.*`, `app.curr_bed_type`). Читать по ключам: в файле лежит `access_code` принтера.
- `tools/bbs_screenshot.sh` — скриншот окна; нужно разрешение «Запись экрана» процессу `claude`.
- Менять настройки: назвать ключ как в UI (вкладка → поле) и значение; пачку — JSON-пресетом в `profiles/user/` через Import Configs в Studio. Файлы в `user/` под запущенной Studio перезаписывает облачная синхронизация.
- Слайсинг без UI для проверки: `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --help`.
- Access code и serial принтера — только в 1Password, через `with-secrets`.

## Fusion

`tools/fmcp.py` — нативный MCP Fusion (127.0.0.1:27182, живёт пока Fusion запущен). `fusion_mcp_execute` с `featureType=script`, `object={script, readOnly}`; скрипт обязан определять `run(_context)`. Чтение (timeline, ThreadFeature.threadInfo, bRepBodies) — с `readOnly: true`, можно без спроса; шум `[MCP] Bind failed … 9876` в ответе — от add-in'а Faust, игнорировать.
