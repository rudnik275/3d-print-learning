# 2026-09-16 — коробка, горбы на стенках

- `studio-project-settings.3mf` — автосейв проекта Studio на 10:17 (настройки + список объектов, без мешей).
- `Body1-rounded-box.3mf` — скруглённая коробка 35.7×45×35.7 (экспорт Fusion, 8576 граней); `Body4/5/6.3mf` — пластина 40×1.2×60 и корпус 67.6×44×51.6 с крышкой-стенкой (стенки 0.8–1.8 мм).
- `settings-diff.txt` — вывод `tools/bbs_current.py`: SUNLU PLA+ @BBL A1M / 0.20mm Standard / A1 mini 0.4, Textured PEI, отличий от базы нет.
- `full-plate.3mf` — тот же стол, пересобранный из исходников (`tools/bbs_rebuild.py`); CLI-нарезка совпадает с утренней (2ч05м, 225 слоёв).
- `test1-seam-scarf.3mf` — кольца + болт, единственное изменение `seam_slope_type = external` (Scarf seam type = Contour). 1ч23м.
- `test2-box-3walls.3mf` — коробка одна, `wall_loops = 3`, `precise_outer_wall = 1`. 37 мин.
