// Lid bridge specimen (after MakerWorld 2050964, own geometry): a box open at the bottom, 4-mm walls on the bed,
// a roof over a 40 x 40 pocket with its underside at z = 6 — the bridge is anchored on all four sides.
label = "10/1.6";

span = 40;
wall = 4;
under = 6;       // roof underside above the bed
roof = 2;
outer = span + 2 * wall;

difference() {
    cube([outer, outer, under + roof]);
    translate([wall, wall, -1]) cube([span, span, under + 1]);
}
translate([outer / 2, outer / 2, under + roof]) linear_extrude(0.6)
    text(label, size = 6, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
