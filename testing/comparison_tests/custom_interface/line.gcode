; SvgToGcode v1.5.4
; GRBL 1.1, unit=mm, absolute coordinates
; Boundingbox: (X0,Y10) to (X150,Y210)
; rapid movement,XY plane,cutter compensation off,coordinate system 1,move 'unit'/min
G0 G17 G40 G54 G94
G21
G90
; pass #1
G4 P0.4
M5
M9
G0 X0 Y210
; Cut at 300 mm/min, 100% power
M7
M4
G1 X100 Y110 S255 F300
G1 X150
G1 Y60
G1 X0 Y210
G1 X150 Y110
G4 P0.4
M5
M9
G0 X0
; Cut at 300 mm/min, 100% power
M7
G1 X100 Y10
G1 X150
G1 Y60
G1 X0 Y110
G1 X150 Y10
M5
M9
M2
