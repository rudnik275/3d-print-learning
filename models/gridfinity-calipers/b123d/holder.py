"""Gridfinity 6×1 — два штангенциркуля 150 мм и 6 батареек LR44 (build123d).

Та же идея и те же размеры, что в ../holder.scad; построено заново скиллом b123d-modeling
через build123d-mcp: по одной операции с замером, проверка валидности, стенок, печатаемости.

По мотивам MakerWorld 1013744 (tej, CC BY-NC). A — пластиковый электронный, сзади, губки справа;
B — обычный металлический, спереди, губки слева. Лежат на ребре, наружные губки вверх,
внутренние губки и стопорный винт уходят вниз в глубокий карман. Бин режется на две половины 3×1:
6 клеток (251.5 мм) на стол A1 mini (180 мм) не входят, сетка основания держит половины встык.

Оси: X — вдоль бина, Y — поперёк (y = 0 — передняя стенка), Z — вверх.
По одному параметру на строку: так design_audit видит каждый (кортежи он пропускает).

Пересобрать (из этой папки):
    uv run --with build123d python holder.py        # left.stl, right.stl, holder.step
"""
from build123d import (Align, Box, BuildPart, BuildSketch, Cylinder, Location, Plane,
                       RectangleRounded, extrude, loft, export_step, export_stl)

# ---- Gridfinity (мм) ----
GRID = 42.0            # шаг сетки
CLEAR = 0.25           # зазор бина к линии сетки с каждой стороны
CELLS = 6              # клеток вдоль бина
SPLIT_CELLS = 3        # клеток в левой половине
FOOT_CH1 = 0.8         # ножка снизу вверх: фаска 45°
FOOT_V = 1.8           #                    вертикаль
FOOT_CH2 = 2.15        #                    фаска 45°
BIN_R = 3.75           # радиус углов бина 41.5
MAGNETS = True
MAGNET_D = 6.5         # гнёзда под магниты 6×2
MAGNET_H = 2.4
MAGNET_OFF = 13.0      # от центра клетки по X и Y

# ---- Бин ----
HEIGHT = 40.0          # как в оригинале; линейки торчат над краем на 3.5 мм, губки — на ~45
END_WALL = 4.5         # торцевые стенки
BEAM_FLOOR = 27.5      # дно пазов линеек (общее, как в оригинале)
MIN_WALL = 1.6         # стенка между карманами и наружу — не тоньше 4 линий сопла 0.4

# ---- A: пластиковый электронный, сзади, губки у правого торца ----
# Карманы сняты с оригинала 1:1 (проверен на Sangabery 0–6", 240 мм). Система дорожки: x — от
# торцевой стенки у губок вдоль линейки, y — от середины паза, «перед» (минус) — сторона дисплея.
A_Y = 31.0             # середина паза линейки от передней стенки
A_SLOT_LEN = 242.5     # паз линейки по всей длине
A_SLOT_W = 6.13
A_TAIL_LEN = 10.0      # уширение на конце линейки (торец корпуса толще)
A_TAIL_BACK = 6.935
A_HEAD_LEN = 82.5      # карман головки вместе с губками
A_HEAD_FRONT = 13.565  # головка с дисплеем выпирает вперёд
A_HEAD_BACK = 6.435
A_HEAD_FLOOR = 23.25
A_JAW_LEN = 15.0       # глубокий паз внутренних губок
A_JAW_FRONT = 6.065
A_JAW_BACK = 6.435
A_JAW_FLOOR = 10.0

# ---- B: металлический 150 мм, спереди, губки у левого торца ----
# Размеры самого штангенциркуля (типовые, до замера — черновик). Зазоры добавляются ниже.
B_Y = 9.75             # середина паза линейки от передней стенки
B_LEN = 235.0          # длина закрытого: от губок до конца линейки
B_BEAM_T = 3.5         # толщина линейки
B_INNER_JAW = 17.0     # на сколько внутренние губки выступают за кромку линейки
B_JAWS_X = 18.0        # сколько места по длине занимают обе внутренние губки у торца
B_JAW_T = 3.5          # толщина внутренних губок
B_JAW_SIDE = 1.0       # запас паза губок на сторону сверх зазора
B_HEAD_LEN = 80.0      # неподвижная губка + рамка нониуса, по длине
B_HEAD_FRONT = 6.5     # рамка нониуса от середины линейки вперёд (сторона шкалы)
B_HEAD_BACK = 7.5      # и назад (прижимная пружина, ролик)
B_BELOW = 12.0         # рамка + стопорный винт ниже кромки линейки

# ---- зазоры для B ----
CL_SLOT = 1.0          # паз шире детали (суммарно на обе стороны)
CL_LEN = 1.0           # паз длиннее детали
CL_DEPTH = 1.0         # карман глубже детали

# ---- LR44: 6 шт. на ребре, между линейками ----
BAT_N = 6
BAT_PITCH = 11.0       # как в оригинале
BAT_X = 5.75           # толщина LR44 5.4 + зазор
BAT_Y = 11.75          # диаметр 11.6 + зазор
BAT_DEPTH = 5.0        # батарейка торчит на ~6.5 мм — берётся пальцами
BAT_X0 = 95.375        # начало первого гнезда: стык половин приходится на стенку между 3-м и 4-м

# ---- построение ----
FOOT_BURY = 0.5        # ножка заходит в корпус: без касания гранью
TOP_OVERCUT = 1.0      # резцы выходят над бином
BED = 180.0            # стол A1 mini

BASE_H = FOOT_CH1 + FOOT_V + FOOT_CH2   # 4.75
L = CELLS * GRID - 2 * CLEAR            # 251.5
W = GRID - 2 * CLEAR                    # 41.5
X_SPLIT = SPLIT_CELLS * GRID - CLEAR    # 125.75 — линия сетки между половинами
B_SLOT_W = B_BEAM_T + CL_SLOT
BAT_YC = ((B_Y + B_SLOT_W / 2) + (A_Y - A_SLOT_W / 2)) / 2   # посередине между пазами линеек


def cell_x(i):
    return GRID / 2 - CLEAR + i * GRID


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0, align=Align.MIN).moved(Location((x0, y0, z0)))


def foot():
    """Ножка одной клетки по профилю Gridfinity, центр в (0, 0), низ на z = 0."""
    s0 = W - 2 * (FOOT_CH1 + FOOT_CH2)
    s1 = W - 2 * FOOT_CH2
    levels = [  # (z, размер, радиус угла)
        (0.0, s0, BIN_R - FOOT_CH1 - FOOT_CH2),
        (FOOT_CH1, s1, BIN_R - FOOT_CH2),
        (FOOT_CH1 + FOOT_V, s1, BIN_R - FOOT_CH2),
        (BASE_H, W, BIN_R),
        (BASE_H + FOOT_BURY, W, BIN_R),
    ]
    with BuildPart() as p:
        for z, s, r in levels:
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(s, s, r)
        loft(ruled=True)
    return p.part


def blank():
    """Сплошной бин: 6 ножек + корпус до HEIGHT."""
    f = foot()
    body = extrude(RectangleRounded(L, W, BIN_R).moved(Location((L / 2, W / 2, BASE_H))), amount=HEIGHT - BASE_H)
    return body.fuse(*[f.moved(Location((cell_x(i), W / 2, 0))) for i in range(CELLS)]).clean()


def lane(x_origin, y_center, direction, boxes, top=HEIGHT + TOP_OVERCUT):
    """Коробки дорожки (x0, x1, y0, y1, z0[, z1]) из системы дорожки в систему бина.
    direction = +1 / -1 — куда от торцевой стенки идёт линейка."""
    out = []
    for b in boxes:
        x0, x1, y0, y1, z0 = b[:5]
        z1 = b[5] if len(b) > 5 else top
        xa, xb = sorted((x_origin + direction * x0, x_origin + direction * x1))
        out.append(box(xa, xb, y_center + y0, y_center + y1, z0, z1))
    return out[0].fuse(*out[1:]).clean() if len(out) > 1 else out[0]


def lane_A():
    return lane(L - END_WALL, A_Y, -1, [
        (0, A_SLOT_LEN, -A_SLOT_W / 2, A_SLOT_W / 2, BEAM_FLOOR),                        # линейка
        (A_SLOT_LEN - A_TAIL_LEN, A_SLOT_LEN, -A_SLOT_W / 2, A_TAIL_BACK, BEAM_FLOOR),   # конец линейки
        (A_JAW_LEN, A_HEAD_LEN, -A_HEAD_FRONT, A_HEAD_BACK, A_HEAD_FLOOR),               # головка с дисплеем
        (0, A_JAW_LEN, -A_JAW_FRONT, A_JAW_BACK, A_JAW_FLOOR),                           # внутренние губки
    ])


def lane_B():
    return lane(END_WALL, B_Y, +1, [
        (0, B_LEN + CL_LEN, -B_SLOT_W / 2, B_SLOT_W / 2, BEAM_FLOOR),                    # линейка
        (0, B_HEAD_LEN + CL_LEN, -B_HEAD_FRONT - CL_SLOT / 2, B_HEAD_BACK + CL_SLOT / 2,
         BEAM_FLOOR - B_BELOW - CL_DEPTH),                                               # рамка нониуса + винт
        (0, B_JAWS_X + CL_LEN, -(B_JAW_T + CL_SLOT) / 2 - B_JAW_SIDE, (B_JAW_T + CL_SLOT) / 2 + B_JAW_SIDE,
         BEAM_FLOOR - B_INNER_JAW - CL_DEPTH),                                           # внутренние губки
    ])


def battery_slots():
    return [box(BAT_X0 + k * BAT_PITCH, BAT_X0 + k * BAT_PITCH + BAT_X, BAT_YC - BAT_Y / 2, BAT_YC + BAT_Y / 2,
                HEIGHT - BAT_DEPTH, HEIGHT + TOP_OVERCUT) for k in range(BAT_N)]


def magnet_holes():
    return [Cylinder(MAGNET_D / 2, MAGNET_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            .moved(Location((cell_x(i) + sx * MAGNET_OFF, W / 2 + sy * MAGNET_OFF, -1)))
            for i in range(CELLS) for sx in (-1, 1) for sy in (-1, 1)] if MAGNETS else []


def halves(part):
    """Половины 3×1: каждая — полноценный бин со своим зазором CLEAR на линии сетки; правая сдвинута к x = 0."""
    big = 1000.0
    left = part & box(-1, X_SPLIT - CLEAR, -1, W + 1, -big, big)
    right = (part & box(X_SPLIT + CLEAR, L + 1, -1, W + 1, -big, big)).moved(Location((-(X_SPLIT + CLEAR), 0, 0)))
    return left.clean(), right.clean()


def walls(solid_blank, pockets, magnets):
    """Наименьшая толщина стенок: между карманами, от кармана наружу, до гнёзд магнитов снизу
    и от гнезда LR44 до стыка половин. Верх бина не считается — карманы открыты вверх."""
    z_cap = HEIGHT - 0.5
    cap = box(-20, L + 20, -20, W + 20, -10, z_cap)
    outside = box(-10, L + 10, -10, W + 10, -5, z_cap) - solid_blank
    joint = box(X_SPLIT - CLEAR, X_SPLIT + CLEAR, -10, W + 10, -5, z_cap)
    p = {n: s & cap for n, s in pockets.items()}
    names = list(p)
    out = {}
    for i, a in enumerate(names):
        out[f"{a} ↔ наружу"] = p[a].distance_to(outside)
        if magnets:
            out[f"{a} ↔ магнит"] = min(p[a].distance_to(m) for m in magnets)
        if a.startswith("LR44"):
            out[f"{a} ↔ стык"] = p[a].distance_to(joint)
        for b in names[i + 1:]:
            out[f"{a} ↔ {b}"] = p[a].distance_to(p[b])
    return out


# ---- модель ----
solid = blank()
pockets = {"A": lane_A(), "B": lane_B()}
pockets.update({f"LR44-{k + 1}": s for k, s in enumerate(battery_slots())})
magnets = magnet_holes()
holder = solid.cut(*pockets.values(), *magnets).clean()
left, right = halves(holder)
result = holder

# ---- самопроверки: то, что проверялось в MCP-сессии, остаётся в коде ----
assert len(holder.solids()) == 1, "бин распался на несколько тел"
for half in (left, right):
    bb = half.bounding_box()
    assert len(half.solids()) == 1 and bb.size.X < BED and bb.size.Y < BED, "половина не влезает на стол"
WALLS = walls(solid, pockets, magnets)
thinnest = min(WALLS, key=WALLS.get)
assert WALLS[thinnest] >= MIN_WALL, f"стенка {thinnest} = {WALLS[thinnest]:.2f} мм < {MIN_WALL}"


# ---- штангенциркули-призраки: проверка посадки, в STL не попадают ----
# A — примерный Sangabery (корпус с дисплеем, линейка 5 × 16); B — те же типовые размеры, что у карманов.
def caliper_A():
    return lane(L - END_WALL, A_Y, -1, [
        (1, 241, -2.5, 2.5, BEAM_FLOOR, BEAM_FLOOR + 16),                     # линейка
        (16, 82, -13, 6, A_HEAD_FLOOR + 0.5, A_HEAD_FLOOR + 26.5),            # корпус с дисплеем
        (1, 13, -4, 4, BEAM_FLOOR + 16, BEAM_FLOOR + 56),                     # наружные губки вверх
        (13.5, 25.5, -4, 4, BEAM_FLOOR + 16, BEAM_FLOOR + 54),
        (1, 14, -4, 4, A_JAW_FLOOR + 0.5, BEAM_FLOOR),                        # внутренние губки вниз
    ])


def caliper_B():
    body = lane(END_WALL, B_Y, +1, [
        (CL_LEN / 2, B_LEN + CL_LEN / 2, -B_BEAM_T / 2, B_BEAM_T / 2, BEAM_FLOOR, BEAM_FLOOR + 16),   # линейка
        (14, B_HEAD_LEN, -B_HEAD_FRONT, B_HEAD_BACK, BEAM_FLOOR - B_BELOW + 5, BEAM_FLOOR + 22),       # рамка
        (CL_LEN / 2, 12.5, -B_BEAM_T / 2, B_BEAM_T / 2, BEAM_FLOOR + 16, BEAM_FLOOR + 56),            # наружные губки
        (13, 23, -B_BEAM_T / 2, B_BEAM_T / 2, BEAM_FLOOR + 16, BEAM_FLOOR + 54),
        (CL_LEN / 2, B_JAWS_X + CL_LEN / 2, -B_JAW_T / 2, B_JAW_T / 2, BEAM_FLOOR - B_INNER_JAW, BEAM_FLOOR),  # внутренние
    ])
    screw = Cylinder(4, 6, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((END_WALL + 45, B_Y, BEAM_FLOOR - B_BELOW)))                   # стопорный винт вниз
    return body.fuse(screw).clean()


if __name__ == "__main__":
    export_stl(left, "left.stl")
    export_stl(right, "right.stl")
    export_step(holder, "holder.step")
    print(f"бин {L} × {W} × {HEIGHT}, объём {holder.volume / 1000:.1f} см³; "
          f"половины {left.volume / 1000:.1f} + {right.volume / 1000:.1f} см³")
    print(f"самая тонкая стенка: {thinnest} = {WALLS[thinnest]:.2f} мм")
    for c in (caliper_A(), caliper_B()):
        assert (holder & c) is None or (holder & c).volume < 1e-6, "штангенциркуль врезается в бин"
