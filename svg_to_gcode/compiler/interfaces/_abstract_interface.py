class Interface:

    """
    Classes which inherit from the abstract Interface class provide a consistent interface_class for the gcode parser.

    The abstract methods below are necessary for the gcode parser to function. Some child classes may choose to also
    implement additional methods like specify_unit and home_axis to provide additional functionality to the parser.

    :param self.position stores the current tool position in 2d
    """

    # Todo convert to abc class
    # Todo add requirement self.position

    def set_machine_parameters(self, params) -> str:
        """
        Set machine parameters.

        :return: ''.
        """
        raise NotImplementedError("Interface class must implement code_initialize")

    def code_initialize(self) -> str:
        """
        Initialize machine.

        :return: Appropriate commands.
        """
        raise NotImplementedError("Interface class must implement code_initialize")

    def set_movement_speed(self, speed) -> str:
        """
        Changes the speed at which the tool moves.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_movemend_speed")

    def rapid_move(self, x=None, y=None, z=None) -> str:
        """
        Moves the tool in rapid motion.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement rapid_move")

    def linear_move(self, x=None, y=None, z=None) -> str:
        """
        Moves the tool in a straight line.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement linear_move")

    def laser_off(self) -> str:
        """
        Powers off the laser beam.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement laser_off")

    def set_laser_power(self, power) -> str:
        """
        If the target machine supports pwm, change the laser power. Regardless of pwm support, powers on the laser beam
        for values of power > 0.

        :param power: Defines the power level of the laser. Valid values range between 0 and 1.
        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_laser_power")

    def set_laser_mode(self, mode) -> str:
        """
        Set lasermode to either 'constant' or 'dynamic'.

        :return: ''.
        """
        raise NotImplementedError("Interface class must implement set_laser_mode")

    def set_distance_mode(self, distance_mode) -> str:
        """
        Set distance mode to either 'absolute' or 'relative' coordinates.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_distance_mode")

    def set_absolute_coordinates(self) -> str:
        """
        Make the coordinate space absolute. ie. move relative to origin not current position.

        return '' if the target of the interface only supports absolute space. If the target only supports
        relative coordinate space, this command should return '' and the child class must transform all future inputs from
        absolute positions to relative positions until set_relative_coordinates is called.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_absolute_coordinates")

    def set_relative_coordinates(self) -> str:
        """
        Make the coordinate space relative. ie. move relative to current position not origin.

        return '' if the target of the interface only supports relative space. If the target only supports
        absolute coordinate space, this command should return '' and the child class must transform all future inputs from
        relative positions to absolute positions until set_absolute_coordinates is called.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_relative_coordinates")

    def set_unit(self, unit):
        """
        Specify the unit of measurement.

        :return: Appropriate command.
        """
        raise NotImplementedError("Interface class must implement set_unit")

    # Optional commands #
    def program_end(self) -> str:
        """
        Optional method, if implemented return 'program end', if not return ''

        :return: Appropriate command.
        """
        pass

    def dwell(self, milliseconds) -> str:
        """
        Optional method, if implemented dwells for a determined number of milliseconds before moving to the next command.

        :param milliseconds: Defines number of milliseconds before moving on. Floating point value >= 0.
        :return: Appropriate command.
        """
        pass

    def set_origin_at_position(self) -> str:
        """
        Optional method, if implemented translates coordinate space such that the current position is the new origin.
        If the target of the interface does not implement this command, return '' and the child class must translate all
        input positions to the new coordinate space.

        :return: Appropriate command.
        """
        pass

    def home_axes(self):
        """
        Optional method, if implemented homes all axes.

        :return: Appropriate command. If not implemented return ''.
        """
        pass
