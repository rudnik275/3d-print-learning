// Top surface specimen: a 24 x 24 x 3 mm square; the label is engraved 0.4 mm into the bottom, mirrored, so the top
// stays clean and the label reads right when the square is flipped over.
line1 = "200";
line2 = "1.00";

size = 24;
h = 3;

difference() {
    cube([size, size, h]);
    translate([size / 2, size / 2, -1]) linear_extrude(1.4) mirror([1, 0, 0]) {
        translate([0, 3.2]) text(line1, size = 4.5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
        translate([0, -3.6]) text(line2, size = 4.5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}
