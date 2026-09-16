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
- `tools/bbs_project.py` — собрать полный проект из автосейва (`assemble`), сделать вариант с подмножеством объектов и изменёнными ключами (`variant --keep … --set key=value`); `tools/bbs_rebuild.py` — восстановить меши из исходных экспортов Fusion, когда автосейв уже ротировался. Ключевая ловушка: при загрузке 3MF Studio сбрасывает на текущий системный пресет все ключи, не перечисленные в `different_settings_to_system` (список по вкладкам process;filament;machine) — `variant` заполняет его сам; без него изменение молча пропадает (2026-09-16). Проверка — CLI-нарезка (`--slice 0 --export-3mf`), затем `open -a BambuStudio file.3mf` — при выключенном single-instance это запускает **второе окно Studio** (свой pid, свой автосейв): сказать Диме, в каком окне тест, лишнее закрыть без сохранения.
- `tools/gcode_layers.py` — по слоям из нарезанного G-code: время слоя, объекты, расход, вентилятор.
- Автосейв живёт только пока проект открыт — всё, что понадобится позже, сразу копировать в `prints/`.
- `tools/bbs_resolve.py <filament|process|machine> "<имя>" [ключи]` — полный пресет с раскрытым `inherits`; файлы в `user/` хранят только overrides.
- Глобально активные пресеты и тип стола — `~/Library/Application Support/BambuStudio/BambuStudio.conf` (JSON, ключи `presets.*`, `app.curr_bed_type`). Читать по ключам: в файле лежит `access_code` принтера.
- `tools/UIDrive.app` — клики/клавиши в Studio: `open -W --stdout out.txt -a tools/UIDrive.app --args click X Y | key 36 | type …` (разрешение Accessibility выдано 2026-09-16; **бинарник не пересобирать** — ad-hoc подпись, TCC привязан к хэшу). Рецепт клика по кнопке: `winctl front <pid>` → `winctl windows <pid>` даёт x y w h окна в поинтах → скриншот окна без тени (`ScreenGrab --args -x -o -l <windowID>`), координата кнопки на снимке ÷ 2 (Retina) + x/y окна → `click`. После клика — снова скриншот, убедиться. **Клавиатурный ввод (`type`/`key`) — только когда Дима явно не за Маком**: события идут в активное окно, и если он в этот момент печатает в Telegram, текст и Enter улетят туда (случай 2026-09-16). Меню Studio через клавиатуру не водить; скриншот через ScreenGrab закрывает открытые меню (перехват фокуса). Кадр с камеры принтера — `tools/bbl_printer.py camera out.jpg`.
- `tools/bbs_screenshot.sh` — скриншот экрана через `tools/ScreenGrab.app` (обёртка над screencapture: macOS даёт «Запись экрана» только .app-бандлам); один раз включить ScreenGrab в Системных настройках.
- Менять настройки: вариант проекта (`bbs_project.py variant --set`), а не инструкции по UI; постоянные изменения — JSON-пресетом в `profiles/user/` через Import Configs в Studio. Файлы в `user/` под запущенной Studio перезаписывает облачная синхронизация.
- Слайсинг без UI для проверки: `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --help`.
- Принтер по LAN: `tools/bbl_printer.py status|upload|print|stop|camera` (IP/serial в `.printer.json`, не в git; access code скрипт читает **в процессе** из `BambuStudio.conf` → `access_code[serial]` и никогда не печатает — в чат/репо он не попадает). Статус, заливка по FTPS и `system.ledctrl` работают; **все команды семейства `print` (`project_file`, `gcode_line`, `print_speed`) прошивка 01.08.01 отвечает `err_code 84033543` — авторизация сторонних клиентов, нужен Developer Mode на экране принтера** (2026-09-16). Без него удалённый старт — только через Bambu Handy с телефона: файл уже лежит на SD-карте.
- Калибровочные столы без мастера Studio: `tools/bbs_calib.py flow1|flow2` (логика 1:1 из CalibUtils.cpp), затем CLI-нарезка → `.gcode.3mf` → принтер.

## Fusion

`tools/fmcp.py` — нативный MCP Fusion (127.0.0.1:27182, живёт пока Fusion запущен). `fusion_mcp_execute` с `featureType=script`, `object={script, readOnly}`; скрипт обязан определять `run(_context)`. Чтение (timeline, ThreadFeature.threadInfo, bRepBodies) — с `readOnly: true`, можно без спроса; шум `[MCP] Bind failed … 9876` в ответе — от add-in'а Faust, игнорировать.
