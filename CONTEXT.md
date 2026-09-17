# CONTEXT

Снимок на 2026-09-16. Источник правды по железу и пластику — Obsidian (`справочники/3d-печать.md`, `справочники/филаменты-инвентарь.md`).

## Железо

- Bambu Lab A1 mini соло (без AMS), сопло 0.4, стол Textured PEI. Bambu Studio 02.08.02.61, режим Advanced.
- Открытая рама → потолок по материалам PETG; ABS/ASA не печатать.
- Перед каждой печатью включены bed leveling, flow calibration (авто flow dynamics) и timelapse.

## Филаменты (инвентарь 14.09.2026)

SUNLU PLA Bone White, PLA Beige, PLA Matte Grey, PLA Matte Oak, PETG Olive Green — все 1.75 мм. PLA Bone White / Beige печатаются на калиброванном `SUNLU PLA @BBL A1M` (таблица ниже); Matte — на системном `SUNLU PLA Matte @BBL A1M`, PETG — на `SUNLU PETG Olive Green @BBL A1M` (оба не калибровались).

## Пресеты Studio на диске

- Пользовательские: `SUNLU PLA @BBL A1M` (калибровка, `profiles/user/`); `SUNLU PETG Olive Green @BBL A1M` (клон `Generic PETG @BBL A1M` без изменений); `Gridfinity PETG 0.20 A1 mini` (`0.20mm Standard` + wall_loops 3, bottom 5, gyroid).
- Базовые значения: `profiles/baseline/*.json` (полностью раскрытые).
  - `SUNLU PLA+ @BBL A1M`: 220 °C / стол 65, MVS 12, flow 1.0, fan 60–80 %, min layer time 6 с.
  - `Generic PETG @BBL A1M`: 255 °C / стол 70, MVS 8, flow 0.95, fan 40–90 %, min layer time 12 с.
  - `0.20mm Standard @BBL A1M`: 2 стенки (0.42 / 0.45), 5 top / 3 bottom, 15 % grid, outer 200 / inner 300 мм/с, seam aligned, scarf off, classic walls, ironing off.
  - Machine 0.4: retraction 0.8 мм / 30 мм/с, z-hop 0.4 Auto Lift, wipe on.
- PA: `enable_pressure_advance = 0` во всех профилях → значение берёт авто-калибровка принтера перед печатью, число в пресете не действует.

## Калиброванные филаменты

| Пресет | База | Температура | Flow ratio | MVS | Дата |
| --- | --- | --- | --- | --- | --- |
| `SUNLU PLA @BBL A1M` (Bone White, Beige) | SUNLU PLA+ @BBL A1M | 220 °C | 0.98 | 12 мм³/с (предел 13) | 2026-09-16 |

## Термины (как в Bambu Studio)

- **wall loops / outer / inner wall** — периметры; **line width** — ширина дорожки.
- **seam** — шов слоя (aligned / back / random); **scarf seam** — наклонный шов, `seam_slope_type`.
- **PA / flow dynamics** — pressure advance.
- **MVS** — max volumetric speed, мм³/с; реальная скорость стенки = min(скорость профиля, MVS / (line width × layer height)).
- **VFA** — vertical fine artifacts, вертикальные полоски от резонанса на определённых скоростях.
- **ringing / ghosting** — эхо углов вдоль стенки; **Z-banding** — горизонтальные полосы, повторяющиеся по высоте.
