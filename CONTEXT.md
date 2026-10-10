# CONTEXT

Снимок на 2026-10-10. Источник правды по железу — Obsidian (`справочники/3d-печать/3d-печать.md`). Учёт пластика не ведётся: какая катушка заправлена — спросить.

## Железо

- Bambu Lab A1 mini соло (без AMS), сопло 0.4, стол Textured PEI. Bambu Studio 02.08.02.61, режим Advanced.
- Открытая рама → потолок по материалам PETG; ABS/ASA не печатать.
- В диалоге отправки (02.10) выключены timelapse, auto bed leveling и flow dynamics calibration — так Дима сейчас отправляет; агент при отправке их не меняет.

## Пресеты Studio на диске

- Пользовательские филаменты: `SUNLU PLA @BBL A1M`, `SUNLU Matte @BBL A1M`, `SUNLU PETG @BBL A1M` (калибровки, таблица ниже).
- Пользовательские процессы: `SUNLU PLA 0.20 A1 mini` (`0.20mm Standard` + мосты SUNLU PLA, ADR-0007) — для обычных печатей SUNLU PLA; `gridfinity` (пакет скилла, 3 стенки, 10 % adaptive cubic + те же мосты); `gridfinity - GRID` (пакет скилла, concentric верх); `Gridfinity PETG 0.20 A1 mini` (`0.20mm Standard` + wall_loops 3, bottom 5, gyroid).
- Базовые значения: `profiles/baseline/*.json` (полностью раскрытые).
  - `SUNLU PLA+ @BBL A1M`: 220 °C / стол 65, MVS 12, flow 1.0, fan 60–80 %, min layer time 6 с.
  - `SUNLU PLA Matte @BBL A1M` (системный, база матового): 220 °C / стол 65, MVS 21, flow 0.98, плотность 1.3, диапазон 205–245, fan 60–80 %, min layer time 6 с.
  - `Generic PETG @BBL A1M`: 255 °C / стол 70, MVS 8, flow 0.95, fan 40–90 %, min layer time 12 с.
  - `0.20mm Standard @BBL A1M`: 2 стенки (0.42 / 0.45), 5 top / 3 bottom, 15 % grid, outer 200 / inner 300 мм/с, seam aligned, scarf off, classic walls, ironing off.
  - Machine 0.4: retraction 0.8 мм / 30 мм/с, z-hop 0.4 Auto Lift, wipe on.
- PA: `enable_pressure_advance = 0` во всех профилях → значение берёт авто-калибровка принтера перед печатью, число в пресете не действует.

## Калиброванные филаменты

| Пресет | База | Температура | Flow ratio | MVS | Дата |
| --- | --- | --- | --- | --- | --- |
| `SUNLU PLA @BBL A1M` (Bone White, Beige) | SUNLU PLA+ @BBL A1M | 220 °C | 1.00 (было 0.98, стол верха 02.10) | 13 мм³/с (предел 15.3) | 2026-10-02 |
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
