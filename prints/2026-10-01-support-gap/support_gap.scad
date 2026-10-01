// Support gap specimen: a 4-mm post with an 18-mm shelf cantilevered at z = 8, the gap value raised on the shelf top.
// The shelf underside is the only overhang, so the tree under it is the only support on the part.
label = "0.20";

post = [4, 16];          // x, y
shelf = [18, 16, 3];     // overhang length (x), width (y), thickness
under = 8;               // shelf underside above the bed

cube([post[0], post[1], under + shelf[2]]);
translate([post[0], 0, under]) cube(shelf);
translate([post[0] + shelf[0] / 2, post[1] / 2, under + shelf[2]])
    linear_extrude(0.6) text(label, size = 4, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
