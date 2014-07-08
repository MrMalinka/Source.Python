# ../filters/entities.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
#   Entities
from entities import EntityGenerator
from entities.entity import BaseEntity
from entities.helpers import basehandle_from_edict
from entities.helpers import index_from_edict
from entities.helpers import inthandle_from_edict
from entities.helpers import pointer_from_edict
#   Filters
from filters.registry import _ReturnTypeRegistry
from filters.iterator import _IterObject


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
# Add all the global variables to __all__
__all__ = [
    'EntityIter',
]


# =============================================================================
# >> MAIN ENTITY ITER CLASSES
# =============================================================================
class _EntityIterManager(object):
    '''Filter management class specifically for entity iterating'''

    def __init__(self):
        '''Store the return type registry instance'''
        self._return_types = _ReturnTypeRegistry(self.__class__.__name__)

    def register_return_type(self, return_type, function):
        '''Registers the given return type to the class'''
        self._return_types.register(return_type, function)

    def unregister_return_type(self, return_type):
        '''Unregisters the given return type from the class'''
        self._return_types.unregister(return_type)

# Get the _EntityIterManager instance
_EntityIterManagerInstance = _EntityIterManager()


class EntityIter(_IterObject):
    '''Entity iterate class'''

    # Store the manager for the entity iterator
    manager = _EntityIterManagerInstance

    # Store the base iterator
    iterator = staticmethod(EntityGenerator)

    def __init__(self, class_names=[], exact_match=True, return_types='index'):
        '''Stores the base attributes for the generator'''

        # Is there only one class name given?
        if isinstance(class_names, str):

            # Convert the class name to a list
            class_names = [class_names]

        # Store the base attributes given
        self._class_names = class_names
        self._exact_match = exact_match
        self._return_types = return_types

    def _is_valid(self, edict):
        '''Checks to see whether the given edict
            is one that should be iterated over'''

        # Are there any class names to be checked?
        if not self._class_names:

            # Return True for all entities
            return True

        # Get the edict's class name
        class_name = edict.get_class_name()

        # Loop through all class names for the generator
        for check_name in self._class_names:

            # Does the current class name match part of the edict's class name?
            if not self._exact_match and check_name in class_name:
                return True

            # Does the current class name match exactly the edict's class name?
            elif self._exact_match and check_name == class_name:
                return True

        # If none of the class names returned True, return False
        return False


# =============================================================================
# >> RETURN TYPES
# =============================================================================
# Register the return type functions
_EntityIterManagerInstance.register_return_type('index', index_from_edict)
_EntityIterManagerInstance.register_return_type('edict', lambda edict: edict)
_EntityIterManagerInstance.register_return_type(
    'basehandle', basehandle_from_edict)
_EntityIterManagerInstance.register_return_type(
    'inthandle', inthandle_from_edict)
_EntityIterManagerInstance.register_return_type('pointer', pointer_from_edict)
_EntityIterManagerInstance.register_return_type(
    'entity', lambda edict: BaseEntity(index_from_edict(edict)))
_EntityIterManagerInstance.register_return_type(
    'classname', lambda edict: edict.get_class_name())
