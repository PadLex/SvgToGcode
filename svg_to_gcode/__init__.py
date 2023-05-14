from typing import Any

TOLERANCES 	= {"approximation": 10 ** -2, "input": 10 ** -3, "operation": 10**-6}
UNITS      	= {"mm", "inch"}
LASERMODE	= {"constant", "dynamic"}
DISTANCEMODE 	= {"absolute", "incremental"}
SETTING 	= {
    # Machine parameters
    "laser_mode_enable", 	# boolean 		    sets grlb 1.1 laser mode (set default on most laser cutters)
    "minimum_laser_power",	# positive integer	sets lowest power value for laser
    "maximum_laser_power",	# positive integer	sets highest power value for laser (make sure this is set to the machine max)
    "x_axis_maximum_rate",	# positive integer	maximum X-axis speed (typically mm/sec or mm/min) (NOTE: currently unused)
    "y_axis_maximum_rate",	# positive integer	maximum Y-axis speed (typically mm/sec or mm/min) (NOTE: currently unused)
    "x_axis_maximum_travel",# positive integer	X-axis length of machine work area (mm)
    "y_axis_maximum_travel",# positive integer	Y-axis length of machine work area (mm)
    "fan",			        # boolean		    when true 'set_laser_power' enables the fan and 'laser_off' disables the fan.
    # Toolparameters
    "pass_depth",		    # positive integer	sets tool cutting depth in machine units (Z-axis: the depth your laser cuts in a pass; note that
				            # 			        this depends on laser power and material!)
    "dwell_time", 		    # positive integer	sets the number of ms the tool should wait before moving to another cut (useful for pen plotters)
    "movement_speed",		# positive integer	F(eed Rate) parameter; sets the movement speed of the tool while cutting (typically mm/sec or mm/min)
    "laser_power",		    # float range [0..1] 	sets the laser intensity (Spindle Speed) of the tool. Note that machine parameters
				            #			            'minimum_laser_power' and 'maximum_laser_power' must be set for this to work
    "laser_mode",		    # LASERMODE		        set constant or dynamic laser power mode
    "maximum_image_laser_power",# positive integer  sets laser power (maximum) for image drawings (this is typically 1/3) of 'maximum_laser_power')
    "image_movement_speed",     # positive integer  sets movement speed when drawing an image (typically a lot less than the 'maximum_rate')
    # Configuration
    "unit",			        # UNITS			    sets machine unit (milimeters, inches), this also defines the Feed (movement) parameter (mm/min or in/min)
    "distance_mode",		# DISTANCEMODE		sets machine distance mode ('absolute' from 0,0 or 'incremental' from current position)
    "rapid_move",		    # boolean		    when false, do not use rapid move (G0) to go to the next line chain, use a 'slow' (G1) move with laser
				            # 			        power off (S0) (note that the first move - to the start of the first line chain - is still a rapid move)
    "pixel_size",           # float             sets image pixel size (in mm)
    "showimage"             # boolean           show image used for conversion to gcode
}

# Set defaults 'minimum_laser_power', 'pass_depth', 'dwell_time', 'laser_power', 'laser_mode', 'unit', 'distance_mode'
DEFAULT_SETTING 	= {
    # Machine parameters
    "laser_mode_enable": 	None,		# usually already on
    "minimum_laser_power": 	0,		    # default set to 0
    "maximum_laser_power": 	None,		# MANDATORY ('enter $$' on the machine console to get this - and other machine parameters)
    "x_axis_maximum_rate": 	None,		# currently unused
    "y_axis_maximum_rate": 	None,		# currently unused
    "x_axis_maximum_travel":None,	    # set this to the length of the machine x-axis (in mm)
    "y_axis_maximum_travel":None,	    # set this to the length of the machine y-axis (in mm)
    "fan":			        False,	    # default set to false (no fan, not on)
    # Toolparameters
    "pass_depth": 		    0,		    # default set to 0 (no depth)
    "dwell_time": 		    0,		    # default set to 0 (do not linger)
    "movement_speed": 	    None,		# MANDATORY
    "laser_power": 		    1,		    # default set to 1
    "laser_mode": 		    "dynamic",	# default set to dynamic (M4 safest mode, laser is off when not moving)
    "maximum_image_laser_power":None,   # MANDATORY should be ("maximum_laser_power" - "minimum_laser_power" / 3)
    "image_movement_speed": None,       # MANDATORY
    # Configuration
    "unit": 			    "mm",		# default set to milimeters
    "distance_mode": 	    "absolute",	# default set to absolute
    "rapid_move":		    True,		# default set to true
    "pixel_size":           0.1,        # laser kerf is mostly < 0.1mm
    "showimage":            False       # default image is not shown
}

def check_setting(setting: dict[str,Any] =None) -> bool:

    """
    Check all settings on type and value range.
    :paran setting: dictionary containg all settings.
    :return returns True when all settings are of the right type and within range.

    Note that because these settings determain real world parameters of machines that have possibly lots of (laser) power, type and range
    mistakes can have serious consequences. Also in general, to contain programming errors, it is best to - in this case - use 'mypy' and
    'pylint' to check typing and formatting problems.

    """

    if setting is None:
        return False

    for key in setting.keys():
        if key not in SETTING:
            raise ValueError(f"Unknown setting {key}. Please specify one of the following: {SETTING}")
        # Machine parameters
        if key == "laser_mode_enable" and setting[key] not in {True,False}:
            raise ValueError(f"Unknown '{key}' value '{setting[key]}'. Please specify one of the following: {{True,False}}")
        if key in {"minimum_laser_power","maximum_laser_power","x_axis_maximum_rate","y_axis_maximum_rate", "movement_speed",
                   "x_axis_maximum_travel","y_axis_maximum_travel", "maximum_image_laser_power",
                   "image_movement_speed" } and (not isinstance(setting[key],int) or setting[key] < 0):
            raise ValueError(f"'{key}' has type {type(setting[key])} and value {setting[key]}, but should be of type {type(1)} and have a value >= 0")
        # Toolparameters
        if key in {"pass_depth","dwell_time"}:
            if not isinstance(setting[key],(int,float)) or setting[key] < 0:
                raise ValueError(f"'{key}' has type {type(setting[key])} and value {setting[key]}, but should be of type {type(1)} and have a value >= 0")
            setting[key] = float(setting[key])
        if key == "laser_power":
            if not isinstance(setting[key],(int,float)):
                raise TypeError(f"'{key}' is of type '{type(setting[key])}' but should be of type {type(1.0)}")
            if setting[key] > 1 or setting[key] < 0:
                raise ValueError(f"'{key}' value {setting[key]} is not in range [0..1]")
            setting[key] = float(setting[key])
        if key == "laser_mode" and setting[key] not in LASERMODE:
            raise ValueError(f"Unknown '{key}' '{setting[key]}'. Please specify one of the following: {LASERMODE}")
        # Configuration
        if key == "unit" and setting[key] not in UNITS:
            raise ValueError(f"Unknown '{key}' value '{setting[key]}'. Please specify one of the following: {UNITS}")
        if key == "distance_mode" and setting[key] not in DISTANCEMODE:
            raise ValueError(f"Unknown '{key}' value '{setting[key]}'. Please specify one of the following: {DISTANCEMODE}")
        if key == "rapid_move" and setting[key] not in {True,False}:
            raise ValueError(f"Unknown '{key}' value '{setting[key]}'. Please specify one of the following: {{True,False}}")
        if key in {"fan","showimage"} and setting[key] not in {True,False}:
            raise ValueError(f"Unknown '{key}' value '{setting[key]}'. Please specify one of the following: {{True,False}}")
        if key == "pixel_size" and setting[key] and (not isinstance(setting[key],(float)) or setting[key] <= 0):
            raise TypeError(f"'{key}' is of type '{type(setting[key])}' but should be of type {type(1.0)} and have a value > 0.0")

    return True
