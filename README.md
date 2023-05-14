# Svg to Gcode - Flamma project
Don't feel like coding? Use the [Inkscape extension](https://github.com/JTechPhotonics/J-Tech-Photonics-Laser-Tool).

This library's intended purpose is to laser-cut svg drawings (<svg:path ..> tags) and engrave images (<svg: image ..> tags).
However, it is structured such that it can be easily expanded to parse other image formats or compile to different numerical control languages.

A commandline steering program is available: see project svg2gcode.

* [Installation](#Installation)
* [Documentation](#Documentation)
    * [Basic Usage](#Basic-Usage)
    * [Custom interfaces](#Custom-interfaces)
    * [Insert or Modify Geometry](#Insert-or-Modify-Geometry)
    * [Approximation tolerance](#Approximation-tolerance)
    * [Support for additional formats](#Support-for-additional-formats)
* [Contribution guidelines](CONTRIBUTING.md)


## Installation
Svg to Gcode is available on pip. To install it, execute:
> pip install svg-to-gcode

Of course, you could also just download the sourcecode.

## Documentation
The module is divided in three sub-modules:
* svg_to_gcode.**geometry** offers a general representation of geometric curves.
* svg_to_gcode.**parser** parses svg files, converting them to geometric curves.
* svg_to_gcode.**compiler** transforms geometric curves into gcode. 

### Basic Usage
If all you need is to compile an svg image to gcode, for a standard cnc machine, this is all the code you need. Just 
remember to set machine dependend parameter 'maximum laser power' and select your own cutting speed.
Note that all current parameters and defaults can be viewed in svg_to_code/__init__.py

```python
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# Instantiate a compiler, specifying the interface type, maximum_laser_power and speed at which the tool moves while 
# cutting. (Note that rapid moves - moves to and from cuts - move at a machine defined speed and are not set here.)
# pass_depth controls how far down the tool moves - how deep the laser cuts - after every pass. Set it to 0 (default)
# if your machine # does not support Z axis movement.
gcode_compiler = Compiler(interfaces.Gcode, params={"maximum_laser_power":1000","movement_speed":900,"pass_depth":5})

# Parse an svg file into geometric curves, and compile to gcode
curves = parse_file("drawing.svg")
gcode_compiler.append_curves(curves)

# do final compilation and emit gcode 2 ('passes') times
gcode_compiler.compile(passes=2)

# or, to combine the above 2 steps into one and emit to a file:
# gcode_compiler.compile_to_file("drawing.gcode", parse_file("drawing.svg"), passes=2)
```

### Custom interfaces
Interfaces exist to abstract commands used by the compiler. In this way, you can compile for a non-standard printer or 
to a completely new numerical control language without modifying the compiler. You can easily write custom interfaces to
 perform additional operations (like powering a fan) or to modify the gcode commands used to perform existing operations
  (some DIY laser cutters, for example, control the laser diode from the fan output). 

The code bellow implements a custom interface which powers on a - special mode - fan every time the laser is powered on. 
```python

from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.formulas import linear_map

class CustomInterface(interfaces.Gcode):

    # Override the set_laser_power method, use gcode M7 - mist coolant - instead of M8 - flood coolant - 
    # (note that setting 'fan' must be True for this to work)
    def set_laser_power(self, power):
        if power < 0 or power > 1:
            raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                             f"The interface will scale it correctly.")
	# set power for next linear move   
        self._next_laser_power = int(linear_map(self._machine_params['minimum_laser_power'], self._machine_params['maximum_laser_power'], power))

        # (fan on when available, use M7 instead of M8), laser_on
        new_mode = ("\nM7" if self._machine_params['fan'] else '') + ("\n" + self._laser_mode if self._laser_mode_changed else '')
        self._laser_mode_changed = False
	# return laser mode (M3 constant laser power or M4 dynamic laser power) when laser mode changed
        return f"; Cut at {self._next_speed} {self._unit}/min, {int(power * 100)}% power{new_mode}"

gcode_compiler = Compiler(CustomInterface, params={"laser_power":1.0,"movement_speed":300,"maximum_laser_power":255,"dwell_time":400,"fan":True})

# Parse an svg file into geometric curves, and compile to gcode
curves = parse_file("drawing.svg")
gcode_compiler.append_curves(curves)

# do final compilation and emit gcode
gcode_compiler.compile()

# or, to combine the above 2 steps into one and emit to a file:
# gcode_compiler.compile_to_file("drawing.gcode", parse_file("drawing.svg"))
```

### Insert or Modify Geometry

Before compiling, you could append or modify geometric curves. I'm not sure why you would want to, but you can.
The code below draws a fractal and compiles it to gcode.

```
Ups. Looks like this example was never filled in...
```

### Approximation tolerance
Gcode only supports liner and circular arcs. Currently I've only implemented a line segment approximation. As such, 
geometric curves are compiled to a chain of line-segments. The exact length of the segments is adjusted dynamically such
that it never diverges from the original curve by more then the value specified by TOLERANCES['approximation'].

The default value is 0.1. Smaller values improve accuracy, larger ones result in shorter gcode files.

```python
from svg_to_gcode import TOLERANCES

TOLERANCES['approximation'] = 0.01
```


### Support for additional formats
For now, this library only converts svgs to gcode files. However, its modular design makes it simple to 
support other formats. If you're looking to support a specific format, pull requests are always welcome. Just make sure 
to read [CONTRIBUTING.md](CONTRIBUTING.md) to get a feeling for the internal structure and best practices.
