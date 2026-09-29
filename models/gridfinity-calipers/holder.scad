// Gridfinity 6×1 — два штангенциркуля 150 мм и 6 батареек LR44.
//
// По мотивам MakerWorld 1013744 «Gridfinity 1x6 6" Calipers Holder + 6 LR44 Battery» (tej, CC BY-NC).
// Там одна дорожка под пластиковый электронный штангенциркуль. Здесь в ту же ширину одной
// клетки легли два: пластиковый (A, сзади) и обычный металлический (B, спереди), головками в
// разные стороны. Батарейки — один ряд, в середине между линейками. Бин разрезан на две
// половины 3×1: 6 клеток (251.5 мм) на стол A1 mini (180 мм) не входят, а сетка основания
// сама держит половины встык.
//
// Как лежит штангенциркуль (как в оригинале): на ребре, наружные губки смотрят вверх и служат
// ручкой. Линейка стоит нижней кромкой на дне паза, головка — в кармане, внутренние губки и
// стопорный винт уходят вниз, в глубокий паз у торца.
//
// Оси: X — вдоль бина, Y — поперёк (y = 0 — передняя стенка), Z — вверх.
//
// Пересобрать (из этой папки):
//   "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD" -o left.stl  -D 'part="left"'  holder.scad   # половина с головкой металлического
//   "/Applications/OpenSCAD Dev.app/Contents/MacOS/OpenSCAD" -o right.stl -D 'part="right"' holder.scad   # половина с головкой пластикового

/* [Что рендерить] */
part = "both";          // ["left", "right", "both", "whole"]
show_calipers = true;   // призраки штангенциркулей в превью (в STL не попадают)

/* [Бин] */
height = 40;            // как в оригинале; линейки торчат над краем на 3.5 мм, губки — на ~45
magnets = true;         // гнёзда 6.5 × 2.4 под магниты 6 × 2 в углах каждой клетки
end_wall = 4.5;         // торцевые стенки
beam_floor = 27.5;      // дно пазов линеек (общее, как в оригинале)

/* [A — пластиковый электронный, сзади, головка справа] */
// Карманы сняты с оригинала 1:1 (он проверен на пластиковом 6"-штангенциркуле Sangabery 240 мм).
// Отсчёт по X — от торцевой стенки у губок, по Y — от середины паза линейки, «перед» — сторона дисплея.
a_y = 31.0;             // середина паза линейки от передней стенки
a_slot_len = 242.5;     // паз линейки по всей длине
a_slot_w = 6.13;
a_tail_len = 10;        // уширение на конце линейки (торец корпуса толще)
a_tail_back = 6.935;
a_head_len = 82.5;      // карман головки вместе с губками
a_head_front = 13.565;  // головка с дисплеем выпирает вперёд
a_head_back = 6.435;
a_head_floor = 23.25;
a_jaw_len = 15;         // глубокий паз внутренних губок
a_jaw_front = 6.065;
a_jaw_back = 6.435;
a_jaw_floor = 10;

/* [B — обычный металлический, спереди, головка слева] */
// Размеры самого штангенциркуля (типовой 150 мм, до замера — черновик). Зазоры добавляются ниже.
b_y = 9.75;             // середина паза линейки от передней стенки
b_len = 235;            // длина закрытого: от губок до конца линейки
b_beam_t = 3.5;         // толщина линейки
b_inner_jaw = 17;       // на сколько внутренние губки выступают за кромку линейки
b_jaws_x = 18;          // сколько места по длине занимают обе внутренние губки у торца
b_jaw_t = 3.5;          // толщина внутренних губок
b_head_len = 80;        // неподвижная губка + рамка нониуса, по длине
b_head_front = 6.5;     // рамка нониуса от середины линейки вперёд (сторона шкалы)
b_head_back = 7.5;      // и назад (прижимная пружина, ролик)
b_below = 12;           // рамка + стопорный винт ниже кромки линейки (в сторону внутренних губок)

/* [Зазоры для B] */
cl_slot = 1.0;          // паз шире детали на столько (суммарно на обе стороны)
cl_len = 1.0;           // паз длиннее детали на столько
cl_depth = 1.0;         // карман глубже детали на столько

/* [Батарейки LR44 — 6 шт. на ребре, между линейками] */
bat_n = 6;
bat_pitch = 11;         // как в оригинале
bat_x = 5.75;           // гнездо: по X (толщина LR44 5.4 + зазор)
bat_y = 11.75;          //         по Y (диаметр 11.6 + зазор)
bat_depth = 5;          // батарейка торчит на ~6.5 мм — берётся пальцами
bat_x0 = 95.375;        // начало первого гнезда; стык половин (x = 125.75) приходится на стенку между 3-м и 4-м

/* [Hidden] */
$fn = 48;
GRID = 42; CLEAR = 0.25; BASE_H = 4.75;
CELLS = 6; SPLIT = 3;
L = CELLS * GRID - 2 * CLEAR;   // 251.5
W = GRID - 2 * CLEAR;           // 41.5
BIG = 100;

// ---------- Gridfinity ----------
module rrect(w, h, r) { offset(r = r) square([w - 2 * r, h - 2 * r], center = true); }
module slab(s, r, z) { translate([0, 0, z]) linear_extrude(0.01) rrect(s, s, r); }

// ножка клетки по стандарту: снизу вверх фаска 0.8, вертикаль 1.8, фаска 2.15 → 41.5 с R3.75
module foot() {
    hull() { slab(35.6, 0.8, 0);   slab(37.2, 1.6, 0.8); }
    hull() { slab(37.2, 1.6, 0.8); slab(37.2, 1.6, 2.6); }
    hull() { slab(37.2, 1.6, 2.6); slab(41.5, 3.75, BASE_H); }
}
function cell_x(i) = GRID / 2 - CLEAR + i * GRID;   // центр клетки в координатах бина
CELL_Y = W / 2;

module bin_body() {
    for (i = [0 : CELLS - 1]) translate([cell_x(i), CELL_Y, 0]) foot();
    translate([L / 2, W / 2, BASE_H]) linear_extrude(height - BASE_H) rrect(L, W, 3.75);
}

module magnet_holes() {
    if (magnets)
        for (i = [0 : CELLS - 1], sx = [-1, 1], sy = [-1, 1])
            translate([cell_x(i) + sx * 13, CELL_Y + sy * 13, -1]) cylinder(d = 6.5, h = 2.4 + 1);
}

// ---------- дорожка под штангенциркуль ----------
// Система дорожки: x — от торцевой стенки у губок вдоль линейки, y — от середины паза (минус — перед).
module box(x0, x1, y0, y1, z0) { translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, BIG]); }

module lane_A() {
    box(0, a_slot_len, -a_slot_w / 2, a_slot_w / 2, beam_floor);                      // линейка
    box(a_slot_len - a_tail_len, a_slot_len, -a_slot_w / 2, a_tail_back, beam_floor); // конец линейки
    box(a_jaw_len, a_head_len, -a_head_front, a_head_back, a_head_floor);             // головка
    box(0, a_jaw_len, -a_jaw_front, a_jaw_back, a_jaw_floor);                         // внутренние губки
}

module lane_B() {
    sw = b_beam_t + cl_slot;
    box(0, b_len + cl_len, -sw / 2, sw / 2, beam_floor);                                           // линейка
    box(0, b_head_len + cl_len, -b_head_front - cl_slot / 2, b_head_back + cl_slot / 2,
        beam_floor - b_below - cl_depth);                                                          // рамка нониуса + винт
    box(0, b_jaws_x + cl_len, -(b_jaw_t + cl_slot) / 2 - 1, (b_jaw_t + cl_slot) / 2 + 1,
        beam_floor - b_inner_jaw - cl_depth);                                                      // внутренние губки
}

module battery_slots() {
    yc = ((b_y + (b_beam_t + cl_slot) / 2) + (a_y - a_slot_w / 2)) / 2;   // посередине между пазами
    for (k = [0 : bat_n - 1])
        translate([bat_x0 + k * bat_pitch, yc - bat_y / 2, height - bat_depth]) cube([bat_x, bat_y, BIG]);
}

module cutters() {
    translate([L - end_wall, a_y, 0]) mirror([1, 0, 0]) lane_A();   // A: губки у правого торца
    translate([end_wall, b_y, 0]) lane_B();                          // B: губки у левого торца
    battery_slots();
    magnet_holes();
}

module whole() { difference() { bin_body(); cutters(); } }

// половины 3×1: каждая — полноценный бин со своим зазором 0.25 на линии сетки
X_SPLIT = SPLIT * GRID - CLEAR;   // 125.75 — линия сетки в координатах бина
module left_half()  { intersection() { whole(); translate([-1, -1, -1]) cube([X_SPLIT - CLEAR + 1, W + 2, BIG]); } }
module right_half() { intersection() { whole(); translate([X_SPLIT + CLEAR, -1, -1]) cube([L, W + 2, BIG]); } }

// ---------- призраки для превью ----------
module ghost_A() {   // в системе дорожки A
    color("DimGray", 0.55) {
        translate([1, -2.5, beam_floor]) cube([240, 5, 16]);                    // линейка
        translate([16, -13, a_head_floor + 0.5]) cube([66, 19, 26]);            // корпус с дисплеем
        translate([1, -4, beam_floor + 16]) cube([12, 8, 40]);                  // наружные губки вверх
        translate([13.5, -4, beam_floor + 16]) cube([12, 8, 38]);
        translate([1, -4, a_jaw_floor + 0.5]) cube([13, 8, beam_floor - a_jaw_floor]);   // внутренние губки вниз
    }
}
module ghost_B() {   // в системе дорожки B
    color("Silver", 0.7) {
        translate([0.5, -b_beam_t / 2, beam_floor]) cube([b_len, b_beam_t, 16]);                    // линейка
        translate([14, -b_head_front, beam_floor - b_below + 5]) cube([b_head_len - 14, b_head_front + b_head_back, 16 + b_below - 5 + 6]); // рамка
        translate([45, 0, beam_floor - b_below]) cylinder(d = 8, h = 6);                           // стопорный винт вниз
        translate([0.5, -b_beam_t / 2, beam_floor + 16]) cube([12, b_beam_t, 40]);                  // наружные губки вверх
        translate([13, -b_beam_t / 2, beam_floor + 16]) cube([10, b_beam_t, 38]);
        translate([0.5, -b_jaw_t / 2, beam_floor - b_inner_jaw]) cube([b_jaws_x, b_jaw_t, b_inner_jaw]); // внутренние губки вниз
    }
}

// ---------- вывод ----------
if (part == "left") left_half();
else if (part == "right") translate([-(X_SPLIT + CLEAR), 0, 0]) right_half();
else if (part == "whole") whole();
else {
    color("WhiteSmoke") { left_half(); translate([4, 0, 0]) right_half(); }
    if (show_calipers && $preview) {
        translate([L - end_wall + 4, a_y, 0]) mirror([1, 0, 0]) ghost_A();
        translate([end_wall, b_y, 0]) ghost_B();
    }
}
