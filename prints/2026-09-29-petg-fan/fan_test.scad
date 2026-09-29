// Калибровка обдува: две детали на одном столе, обдув меняется полосами по 10 мм (переписывается в G-code, build.py).
//   tower — две колонны: мост 20 мм между ними и уступы 45° и 60° на внешних гранях, в каждой полосе заново;
//           насечки на передней грани колонны — границы полос.
//   tube  — плоская трубка в две стенки для излома руками; рёбра на границах полос (излом приходится внутрь полосы).
// Длинная сторона обеих деталей идёт вдоль Y — по ходу стола A1 mini.

part = "tower";   // ["tower", "tube"]
plinth = 2;       // основание, печатается с выключенным обдувом первых слоёв
band = 10;
bands = 6;
H = plinth + band * bands;

gap = 20;         // пролёт моста
col = 10;         // колонна 10 × 10
bridge_t = 1.4;   // мост у верха каждой полосы
ledge_h = 8.6;    // высота наклонной части уступа, выше — полка 1.4 мм

module ledge(angle, side) {   // side -1: наружу от левой колонны, +1: от правой
    w = ledge_h * tan(angle);
    x0 = side < 0 ? 0 : 2 * col + gap;
    for (k = [0 : bands - 1]) {
        z0 = plinth + k * band;
        translate([x0, 0, 0]) rotate([90, 0, 0]) translate([0, 0, -col])
            linear_extrude(col) polygon([[0, z0], [0, z0 + band], [side * w, z0 + band], [side * w, z0 + ledge_h]]);
    }
}

module tower() {
    difference() {
        union() {
            translate([-1, -2, 0]) cube([2 * col + gap + 2, col + 4, plinth]);
            cube([col, col, H]);
            translate([col + gap, 0, 0]) cube([col, col, H]);
            for (k = [0 : bands - 1])
                translate([col, 0, plinth + k * band + band - bridge_t]) cube([gap, col, bridge_t]);
            ledge(45, -1);
            ledge(60, 1);
        }
        for (k = [1 : bands - 1], x = [0, col + gap])   // насечки 0.6 × 0.6 на передней грани (y = 0)
            translate([x - 1, -0.01, plinth + k * band - 0.3]) cube([col + 2, 0.6, 0.6]);
    }
}

tube_l = 24; tube_w = 6; tube_wall = 0.85; rib = 0.6;
module tube() {
    difference() {
        union() {
            translate([-tube_l / 2, -tube_w / 2, 0]) cube([tube_l, tube_w, H]);
            for (k = [1 : bands - 1])
                translate([-tube_l / 2 - rib, -tube_w / 2 - rib, plinth + k * band - 0.3]) cube([tube_l + 2 * rib, tube_w + 2 * rib, 0.6]);
        }
        translate([-tube_l / 2 + tube_wall, -tube_w / 2 + tube_wall, plinth]) cube([tube_l - 2 * tube_wall, tube_w - 2 * tube_wall, H]);
    }
}

rotate([0, 0, 90]) { if (part == "tower") tower(); else tube(); }
