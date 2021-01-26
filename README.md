
# Svg to Gcode - Flamma project
### The definitive NPM module to construct gcode from svg files.
Don't feel like coding? Use the [Inkscape extension](https://github.com/JTechPhotonics/J-Tech-Photonics-Laser-Tool).

This library's intended purpose is to laser-cut svg images. However, it is structured such that it can be easily 
expanded to parse other image formats or compile to different numerical control languages. 

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
remember to select your own cutting and movement speeds.  

```python
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# Instantiate a compiler, specifying the interface type and the speed at which the tool should move. pass_depth controls
# how far down the tool moves after every pass. Set it to 0 if your machine does not support Z axis movement.
gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)

curves = parse_file("drawing.svg") # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file("drawing.gcode", passes=2)
```

### Custom interfaces
Interfaces exist to abstract commands used by the compiler. In this way, you can compile for a non-standard printer or 
to a completely new numerical control language without modifying the compiler. You can easily write custom interfaces to
 perform additional operations (like powering a fan) or to modify the gcode commands used to perform existing operations
  (some DIY laser cutters, for example, control the laser diode from the fan output). 

The code bellow implements a custom interface which powers on a fan every time the laser is powered on. 
```python
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.formulas import linear_map

class CustomInterface(interfaces.Gcode):
    def __init__(self):
        super().__init__()
        self.fan_speed = 1
    
    # Override the laser_off method such that it also powers off the fan.
    def laser_off(self):
        if self._current_power is None or self._current_power > 0:
            self._current_power = 0
            return "M107;\n" + "M5;" # Turn off the fan + turn off the laser

        return ''
    
    # Override the set_laser_power method
    def set_laser_power(self, power):
        self._current_power = power

        if power < 0 or power > 1:
            raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                             f"The interface will scale it correctly.")

        return f"M106 S255\n" + f"M3 S{linear_map(0, 255, power)};" # Turn on the fan + change laser power

# Instantiate a compiler, specifying the custom interface and the speed at which the tool should move.
gcode_compiler = Compiler(CustomInterface, movement_speed=1000, cutting_speed=300, pass_depth=5)

curves = parse_file("drawing.svg") # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file("drawing.gcode")
```

### Insert or Modify Geometry

Before compiling, you could append or modify geometric curves. I'm not sure why you would want to, but you can.
The code below draws a fractal and compiles it to gcode.

```python
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.formulas import linear_map

# Instantiate a compiler, specifying the custom interface and the speed at which the tool should move.
gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)

curves = parse_file("drawing.svg") # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file("drawing.gcode")
```

### Approximation tolerance
Gcode only supports liner and circular arcs. Currently I've only implemented a line segment approximation. As such, 
geometric curves are compiled to a chain of line-segments. The exact length of the segments is adjusted dynamically such
that it never diverges from the original curve by more then the value of the TOLERANCES['approximation'] key.

The default value is 0.1. Smaller values improve accuracy, larger ones result in shorter gcode files.

```python
from svg_to_gcode import TOLERANCES

TOLERANCES['approximation'] = 0.01
```


### Support for additional formats
For now, this library only converts svgs to gcode files. However, its modular design makes it simple to 
support other formats. If you're looking to support a specific format, pull requests are always welcome. Just make sure 
to read [CONTRIBUTING.md](CONTRIBUTING.md) to get a feeling for the internal structure and best practices.
