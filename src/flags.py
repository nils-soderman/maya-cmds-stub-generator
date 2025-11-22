import enum

class GeneratorFlag(enum.Flag):
    NONE = 0
    INCLUDE_UNDOCUMENTED_FUNCTIONS = enum.auto()
    """ Include all functions available in cmds, even the undocumented ones """
    CACHE = enum.auto()
    """ Cache downloaded documentation to disk """
    TUPLE_PARAMS = enum.auto()
    """ Use tuple parameters for functions, will otherwise use Sequence which is less strict """
