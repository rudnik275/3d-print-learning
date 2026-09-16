# 2026-09-16 — калибровка SUNLU PLA Bone White (пресет SUNLU PLA+ @BBL A1M)

- `flow-pass1.3mf` — Flow Rate coarse: 9 блоков −20…+20 % (`tools/bbs_calib.py flow1`, логика мастера Studio), `flow-pass1.gcode.3mf` — нарезка CLI, 27 мин, 7 слоёв. Раскладка 3×3, ряды сзади→вперёд: −20 −15 −10 / −5 0 +5 / +10 +15 +20 (цифры отлиты на блоках).
- Залит на SD-карту принтера: `/flow-pass1.gcode.3mf` и `/cache/flow-pass1.gcode.3mf`. Старт по MQTT отклонён (Developer Mode выключен).
- Итог coarse → `flow2` (fine, −9…0 % поверх выбранного) → новый пресет филамента.
