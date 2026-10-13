# CONTEXT

Снимок на 2026-10-12. Источник правды по железу — Obsidian (`справочники/3d-печать/3d-печать.md`). Учёт пластика не ведётся: какая катушка заправлена — спросить.

## Железо

- Bambu Lab A1 mini соло (без AMS), сопло 0.4. Bambu Studio 02.08.02.61, режим Advanced.
- **Пластины две** (с 2026-10-12): Textured PEI — основная, и Smooth PEI. **Какая стоит на столе — спрашивать** перед нарезкой: температура стола лежит в пресете филамента по типу пластины (PLA: 65 °C на Textured, 60 на Smooth, PETG — 70 на обеих), CLI режет под пластину, выбранную в Orca (`app.curr_bed_type`), а распознавания пластины у A1 mini нет — принтер греет то, что в файле. Гладкая в Studio/Orca — пункт «Smooth PEI Plate / High Temp Plate».
- Оси смазаны 2026-10-12 — впервые с покупки (2026-08); винт Z — консистентной смазкой из коробки. Регламент Bambu: рельсы X/Z и валы Y — масло раз в месяц, винт Z и ролик ремня X — раз в 3 месяца; журнал смазок и ссылки на регламент — Obsidian `справочники/3d-печать/3d-печать-обслуживание.md`, напоминания — Google Calendar. Полосы на стенках SUNLU PLA (одинаковые на всех объектах стола на одной высоте) были от сухого винта Z: тот же файл после смазки — чистый (#104 закрыт, урок 03). Повторяющийся по слоям дефект на всех объектах стола → сначала смазка, потом калибровка.
- Открытая рама → потолок по материалам PETG; ABS/ASA не печатать.
- В диалоге отправки (02.10) выключены timelapse, auto bed leveling и flow dynamics calibration — так Дима сейчас отправляет; агент при отправке их не меняет.

## Пресеты Studio на диске

- Пользовательские филаменты: `SUNLU PLA @BBL A1M`, `SUNLU Matte @BBL A1M`, `SUNLU PETG @BBL A1M` (калибровки, таблица ниже).
- Пользовательские процессы: `SUNLU PLA 0.20 A1 mini` (`0.20mm Standard` + мосты SUNLU PLA, ADR-0007) — для обычных печатей SUNLU PLA; `Gridfinity 0.20 A1 mini` (ADR-0008, с 2026-10-13: один пресет на PLA и PETG, бины и сетку — 3 стенки Arachne, gyroid 10 %, 4/5 слоёв, concentric верх, слоновья нога 0.15, шов back, нависания 10 мм/с, мосты стандартные, пакет качества). Старые `gridfinity`, `gridfinity - GRID` и `Gridfinity PETG 0.20 A1 mini` удалены.
- Базовые значения: `profiles/baseline/*.json` (полностью раскрытые).
  - `SUNLU PLA+ @BBL A1M`: 220 °C / стол 65, MVS 12, flow 1.0, fan 60–80 %, min layer time 6 с.
  - `SUNLU PLA Matte @BBL A1M` (системный, база матового): 220 °C / стол 65, MVS 21, flow 0.98, плотность 1.3, диапазон 205–245, fan 60–80 %, min layer time 6 с.
  - `Generic PETG @BBL A1M`: 255 °C / стол 70, MVS 8, flow 0.95, fan 40–90 %, min layer time 12 с.
  - `0.20mm Standard @BBL A1M`: 2 стенки (0.42 / 0.45), 5 top / 3 bottom, 15 % grid, outer 200 / inner 300 мм/с, seam aligned, scarf off, classic walls, ironing off.
  - Machine 0.4: retraction 0.8 мм / 30 мм/с, z-hop 0.4 Auto Lift, wipe on.
- PA: `enable_pressure_advance = 0` во всех профилях, число в пресете не действует. Пока калибровка flow dynamics при отправке была включена, k мерил принтер перед каждой печатью; с 02.10 она выключена → принтер печатает с k по умолчанию (0.02 в данных катушки) для всех пластиков. Вручную PA не калиброван — на столах потока это видно как грубые края блоков при чистой середине.

## Калиброванные филаменты

| Пресет | База | Температура | Flow ratio | MVS | Дата |
| --- | --- | --- | --- | --- | --- |
| `SUNLU PLA @BBL A1M` (Bone White, Beige, Mint) | SUNLU PLA+ @BBL A1M (все три значения записаны явно) | 225 °C (башня 240→205 плоская — выбрано по потолку расхода) | 0.96 | 12 мм³/с (первый дефект 39 мм на рампе 5→26 = 16.7 номинал, 221 мм/с; −28 %) | 2026-10-12, перекалибровка с нуля от Generic PLA — `lessons/03`, `prints/2026-10-12-sunlu-pla-recal/` |
| `SUNLU Matte @BBL A1M` (Matte Grey, Oak) | SUNLU PLA Matte @BBL A1M | 225 °C | 0.975 | 24 мм³/с (чисто до 26, предел выше) | 2026-09-19 |
| `SUNLU PETG @BBL A1M` (Olive Green) | Generic PETG @BBL A1M | 245 °C | 0.95 | 16 мм³/с | 2026-09-22; обдув 30 %, мосты и нависания 70 % — 29.09 |

SUNLU PLA, процесс (ADR-0007, `lessons/07-supports-bridges-top.md`): мосты `bridge_speed 10` × `bridge_flow 1.6`, нависания 2/4 и 3/4 — 10 мм/с (в пресетах `SUNLU PLA 0.20 A1 mini` и `gridfinity`); поддержки под плоский низ — `normal(auto)` с зазором 0.10, под органику — деревья; ironing — по модели, с `top_solid_infill_flow_ratio 1.04`.

## Термины (как в Bambu Studio)

- **wall loops / outer / inner wall** — периметры; **line width** — ширина дорожки.
- **seam** — шов слоя (aligned / back / random); **scarf seam** — наклонный шов, `seam_slope_type`.
- **PA / flow dynamics** — pressure advance.
- **MVS** — max volumetric speed, мм³/с; реальная скорость стенки = min(скорость профиля, MVS / (line width × layer height)).
- **VFA** — vertical fine artifacts, вертикальные полоски от резонанса на определённых скоростях.
- **ringing / ghosting** — эхо углов вдоль стенки; **Z-banding** — горизонтальные полосы, повторяющиеся по высоте.
