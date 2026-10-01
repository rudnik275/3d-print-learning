// Bridge row: a deck 10 mm wide over spans 15 / 25 / 35 / 45 mm, underside at z = 6, 1.6 mm thick (8 layers at 0.2).
// Span lengths are raised on the deck, the row label (its bridge_flow) on the left tab.
label = "1.0";
label_size = 3.6;

spans = [15, 25, 35, 45];
tab = 10;        // left block under the label
post = 4;        // pillar width along the bridge
w = 10;          // deck / pillar width (y)
under = 6;       // deck underside above the bed
deck = 1.6;

function x0(i) = tab + post * i + (i == 0 ? 0 : spans[0]) + (i > 1 ? spans[1] : 0) + (i > 2 ? spans[2] : 0);   // start of span i
total = tab + post * 3 + spans[0] + spans[1] + spans[2] + spans[3] + post;

cube([tab, w, under + deck]);
for (i = [0 : 3]) translate([x0(i) + spans[i], 0, 0]) cube([post, w, under + deck]);
translate([0, 0, under]) cube([total, w, deck]);
translate([tab / 2, w / 2, under + deck]) linear_extrude(0.4)
    text(label, size = label_size, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
for (i = [0 : 3]) translate([x0(i) + spans[i] / 2, w / 2, under + deck]) linear_extrude(0.4)
    text(str(spans[i]), size = 4, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
