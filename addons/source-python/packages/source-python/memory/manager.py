# =============================================================================
# >> IMPORTS
# =============================================================================
# Python
from configobj import ConfigObj

# Source.Python
from memory_c import *
from memory.helpers import *


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = [
    'EXPOSED_CLASSES',
    'CustomType',
    'TypeManager',
    'manager',

    # From memory.helpers
    'Type'
]


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
EXPOSED_CLASSES = get_exposed_classes()


# =============================================================================
# >> CustomType
# =============================================================================
class CustomType(BasePointer):
    '''
    Subclass this class if you want to create a new type. Make sure that you
    have set the metaclass attribute to a valid TypeManager instance.
    '''

    # This should always hold a TypeManager instance. It's set automatically
    # by the metaclass.
    _manager = None

    # This is required if TypeManager.function() is used. It should contain
    # the path to the binary that defines this type
    _binary = None

    # Optional -- this gets passed to BinaryFile.find_binary()
    _srv_check = True

    # Optional -- specifies the size of the type
    _size = None

    # Optional -- will be called when an instance of the type is created
    _constructor = None

    # TODO: Implement this!
    # Optional -- will be called when an instance of the type is deleted
    _destructor = None

    def __init__(self, *args, wrap=True, auto_dealloc=False):
        '''
        Initializes the custom type.
        '''

        # _manager must be an instance of TypeManager. Otherwise the type
        # wasn't registered by a TypeManager.
        if not isinstance(self._manager, TypeManager):
            raise ValueError(
                'Attribute _manager must be an instance of "TypeManager".')

        # Do we want to wrap a pointer?
        if wrap:
            # Check if only the this pointer was passed
            if len(args) != 1:
                raise ValueError(
                    'If <wrap> is true only one argument is accepted.')

            super(CustomType, self).__init__(args[0])

        # Obviously, we want to create a new instance
        else:
            # Was a size specified?
            if self._size is None:
                raise ValueError(
                    'In order to create an instance _size is required.')

            # Allocate some space
            super(CustomType, self).__init__(alloc(self._size, False))
            self.auto_dealloc = auto_dealloc

            # Optionally, call a constructor
            if self._constructor is not None:
                self._constructor(*args)

            # No constructor, but arguments? Hmm, the user is doing something
            # wrong
            elif args:
                raise ValueError(
                    'No constructor was specified, but arguments were passed.')

    def on_dealloc(self):
        '''
        This method is automatically called, when the pointer gets
        deallocated. It then calls the destructor if it was specified.
        '''

        # Call the destructor if it was specified
        if self._destructor is not None:
            self._destructor()


# =============================================================================
# >> TypeManager
# =============================================================================
class TypeManager(dict):
    '''
    The TypeManager is able to reconstruct almost every possible data type.
    '''

    def __call__(self, name, bases, cls_dict):
        '''
        Creates and registers a new class.
        '''

        # Set the manager attribute. This is required, so CustomType.__init__
        # can verify that we have registered the class
        cls_dict['_manager'] = self

        # Create the class object
        cls = type(name, bases, cls_dict)

        # Check if it's a subclass of CustomType
        if not issubclass(cls, CustomType):
            raise ValueError(
                'Custom type "{0}" has to '.format(name) +
                'be a subclass of "CustomType".')

        self[name] = cls
        return cls

    def convert(self, name, ptr):
        '''
        Converts a pointer to the given class.
        '''

        # Try to use a CustomType at first
        if name in self:
            return self[name](ptr)

        # If that fails, try to use an exposed class
        if name in EXPOSED_CLASSES:
            return make_object(EXPOSED_CLASSES[name], ptr)

        raise NameError('Unable to make an object of "{0}"'.format(name))

    def get_class(self, name):
        '''
        Tries to return a custom type that matches the given name. If no
        custom type was found, it tries to return a class that was exposed on
        the C++ side. If that fails too, an error will be raises.
        '''

        if name in self:
            return self[name]

        if name in EXPOSED_CLASSES:
            return EXPOSED_CLASSES[name]

        raise NameError('Unknown class "{0}"'.format(name))

    def create_converter(self, name):
        '''
        Creates a new converter for the given name.
        '''

        return lambda ptr: self.convert(name, ptr)

    def create_type(self, name, cls_dict, bases=(CustomType,)):
        '''
        Creates and registers a new class.
        '''

        # This is just a wrapper for __call__
        return self(name, bases, cls_dict)

    def create_pipe(self, cls_dict):
        '''
        Creates a new pipe class that acts like a collection of functions.
        '''

        # Just create a container for all the functions
        return type('Pipe', (object,), cls_dict)

    def create_pipe_from_file(self, f):
        '''
        Creates a pipe from a file or URL.
        '''

        # Read the data
        raw_data = ConfigObj(f)

        # Try to close the file. Maybe it was an url or a file object
        try:
            f.close()
        except AttributeError:
            pass

        # Prepare functions
        funcs = parse_data(
            raw_data,
            (
                (Key.BINARY, str, NO_DEFAULT),
                (Key.IDENTIFIER, Key.as_identifier, NO_DEFAULT),
                (Key.ARGS, Key.as_args_tuple, ()),
                (Key.RETURN_TYPE, Key.as_return_type, Return.VOID),
                (Key.CONVENTION, Key.as_convention, Convention.CDECL),
                (Key.SRV_CHECK, Key.as_bool, True),
                (Key.DOC, str, None)
            )
        )

        # Create the functions
        cls_dict = {}
        for name, data in funcs:
            cls_dict[name] = self.pipe_function(*data)

        return self.create_pipe(cls_dict)

    def pipe_function(
            self, binary, identifier, args=(), return_type=Return.VOID,
            convention=Convention.CDECL, srv_check=True, doc=None):
        '''
        Creates a simple pipe function.
        '''

        # Create a converter, if it's not a native type
        if return_type not in Return.values:
            return_type = self.create_converter(return_type)

        # Find the binary
        bin = find_binary(binary, srv_check)

        # Find the address and make it to a function
        func = bin[identifier].make_function(convention, args, return_type)

        # Add documentation
        func.__doc__ = doc
        return func

    def create_type_from_file(self, type_name, f, bases=(CustomType,)):
        '''
        Creates and registers a new type from a file or URL.
        '''

        # Read the data
        raw_data = ConfigObj(f)

        # Try to close the file. Maybe it was an url or a file object
        try:
            f.close()
        except AttributeError:
            pass

        # Prepare general type information
        data = tuple(parse_data(
            # Discard all subkeys and add the new dict to a another dict to
            # make it work with parse_data(). Okay, this can be improved...
            {0: dict((k, v) for k, v in raw_data.items() if not isinstance(v, dict))},
            (
                (Key.BINARY, str, CustomType._binary),
                (Key.SRV_CHECK, Key.as_bool, CustomType._srv_check),
                (Key.SIZE, int, CustomType._size)
            )
        ))[0][1]

        cls_dict = dict(zip(('_binary', '_src_check', '_size'), data))

        # Prepare pointer and instance attributes
        for method in (self.instance_attribute, self.pointer_attribute):
            attributes = parse_data(
                raw_data.get(method.__name__, {}),
                (
                    (Key.TYPE_NAME, Key.as_attribute_type, NO_DEFAULT),
                    (Key.OFFSET, int, NO_DEFAULT),
                    (Key.DOC, str, None)
                )
            )

            # Create the attributes
            for name, data in attributes:
                cls_dict[name] = method(*data)

        # Prepare arrays
        for method in (
                self.static_instance_array,
                self.dynamic_instance_array,
                self.static_pointer_array,
                self.dynamic_pointer_array):
            arrays = parse_data(
                raw_data.get(method.__name__, {}),
                (
                    (Key.TYPE_NAME, Key.as_attribute_type, NO_DEFAULT),
                    (Key.OFFSET, int, NO_DEFAULT),
                    (Key.LENGTH, int, None),
                    (Key.DOC, str, None)
                )
            )

            # Create the arrays
            for name, data in arrays:
                cls_dict[name] = method(*data)

        # Prepare virtual functions
        vfuncs = parse_data(
            raw_data.get('virtual_function', {}),
            (
                (Key.INDEX, int, NO_DEFAULT),
                (Key.ARGS, Key.as_args_tuple, ()),
                (Key.RETURN_TYPE, Key.as_return_type, Return.VOID),
                (Key.CONVENTION, Key.as_convention, Convention.THISCALL),
                (Key.DOC, str, None)
            )
        )

        # Create the virtual functions
        for name, data in vfuncs:
            cls_dict[name] = virtual_function(*data)

        # Prepare functions
        funcs = parse_data(
            raw_data.get('function', {}),
            (
                (Key.IDENTIFIER, Key.as_identifier, NO_DEFAULT),
                (Key.ARGS, Key.as_args_tuple, ()),
                (Key.RETURN_TYPE, Key.as_return_type, Return.VOID),
                (Key.CONVENTION, Key.as_convention, Convention.THISCALL),
                (Key.DOC, str, None)
            )
        )

        # Create the functions
        for name, data in funcs:
            cls_dict[name] = function(*data)

        # Now create and register the type
        return self(type_name, bases, cls_dict)

    def instance_attribute(self, type_name, offset, doc=None):
        '''
        Creates a wrapper for an instance attribute.

        Examples:
            Vector vecVal;
            bool bVal;
        '''

        native_type = Type.is_native(type_name)

        def fget(ptr):
            # Handle custom type
            if not native_type:
                return self.convert(type_name, ptr + offset)

            # Handle native type
            return getattr(ptr, 'get_' + type_name)(offset)

        def fset(ptr, value):
            # Handle custom type
            if not native_type:
                if not isinstance(value, Pointer):
                    raise ValueError(
                        'The value must be an instance of the Pointer class')

                value.copy(ptr + offset, self.get_class(type_name)._size)

            # Handle native type
            else:
                getattr(ptr, 'set_' + type_name)(value, offset)

        return property(fget, fset, None, doc)

    def pointer_attribute(self, type_name, offset, doc=None):
        '''
        Creates a wrapper for a pointer attribute.

        Examples:
            Vector* pVec;
            bool* pBool;
        '''

        native_type = Type.is_native(type_name)

        def fget(ptr):
            # Get the base address of the pointer. We are now on
            # "instance level"
            ptr = ptr.get_pointer(offset)

            # Handle custom type
            if not native_type:
                return self.convert(type_name, ptr)

            # Handle native type
            return getattr(ptr, 'get_' + type_name)()

        def fset(ptr, value):
            # Get the base address of the pointer. We are now on
            # "instance level"
            ptr = ptr.get_pointer(offset)

            # Handle custom type
            if not native_type:
                if not isinstance(value, Pointer):
                    raise ValueError(
                        'The value must be an instance of the Pointer class')

                # Q: Why do we use copy instead of set_pointer?
                # A: Maybe it's a shared pointer which means that other
                #    classes might also have the address of it. So, changing
                #    address in this particular class wouldn't affect the
                #    other classes.
                # TODO: Is that what we want? Maybe we could add a "copy"
                #       parameter to let the user decide.
                value.copy(ptr, self.get_class(type_name)._size)

            # Handle native type
            else:
                getattr(ptr, 'set_' + type_name)(value)

        return property(fget, fset, None, doc)

    def static_instance_array(self, type_name, offset, length=None, doc=None):
        '''
        Creates a wrapper for a static instance array.

        Examples:
            Vector vecArray[10];
            bool boolArray[10];
        '''

        def fget(ptr):
            return Array(self, False, type_name, ptr + offset, length)

        def fset(ptr, value):
            array = fget(ptr)
            for index, val in enumerate(value):
                array[index] = val

        return property(fget, fset, None, doc)

    def dynamic_instance_array(self, type_name, offset, length=None, doc=None):
        '''
        Creates a wrapper for a dynamic instance array.

        Examples:
            Vector* pVecArray;
            bool* pBoolArray;

        Those arrrays are mostly created by the "new" statement.
        '''

        def fget(ptr):
            return Array(
                self, False, type_name, ptr.get_pointer(offset), length)

        def fset(ptr, value):
            array = fget(ptr)
            for index, val in enumerate(value):
                array[index] = val

        return property(fget, fset, None, doc)

    def static_pointer_array(self, type_name, offset, length=None, doc=None):
        '''
        Creates a wrapper for a static pointer array.

        Examples:
            Vector* pVecArray[10];
            bool* pBoolArray[10];
        '''

        def fget(ptr):
            return Array(self, True, type_name, ptr + offset, length)

        def fset(ptr, value):
            array = fget(ptr)
            for index, val in enumerate(value):
                array[index] = val

        return property(fget, fset, None, doc)

    def dynamic_pointer_array(self, type_name, offset, length=None, doc=None):
        '''
        Creates a wrapper for a dynamic pointer array.

        Examples:
            Vector** pVecArray;
            bool** pBoolArray;

        Those arrays are mostly created by the "new" statement.
        '''

        def fget(ptr):
            return Array(self, True, type_name, ptr.get_pointer(offset), length)

        def fset(ptr, value):
            array = fget(ptr)
            for index, val in enumerate(value):
                array[index] = val

        return property(fget, fset, None, doc)

    def virtual_function(
            self, index, args=(), return_type=Return.VOID,
            convention=Convention.THISCALL, doc=None):
        '''
        Creates a wrapper for a virtual function.
        '''

        # Automatically add the this pointer argument
        args = (Argument.POINTER,) + args

        # Create a converter, if it's not a native type
        if return_type not in Return.values:
            return_type = self.create_converter(return_type)

        def fget(ptr):
            # Create the virtual function
            func = ptr.make_virtual_function(
                index,
                convention,
                args,
                return_type
            )

            # Wrap it using MemberFunction, so we don't have to pass the this
            # pointer anymore
            return MemberFunction(self, return_type, func, ptr)

        return property(fget, None, None, doc)

    def function(
            self, identifier, args=(), return_type=Return.VOID,
            convention=Convention.THISCALL, doc=None):
        '''
        Creates a wrapper for a function.
        '''

        # Automatically add the this pointer argument
        args = (Argument.POINTER,) + args

        # Create a converter, if it's not a native type
        if return_type not in Return.values:
            return_type = self.create_converter(return_type)

        class fget(object):
            def __get__(self, obj, cls):
                if cls._binary is None:
                    raise ValueError('_binary was not specified.')

                # Create a binary object
                binary = find_binary(cls._binary, cls._srv_check)

                # Create the function object
                func = binary[identifier].make_function(
                    convention,
                    args,
                    return_type
                )

                # Called with a this pointer?
                if obj is not None:
                    # Wrap the function using MemberFunction, so we don't have
                    # to pass the this pointer anymore
                    func = MemberFunction(self, return_type, func, ptr)

                func.__doc__ = doc
                return func

        return fget()

    def function_typedef(
            self, name, args=(), return_type=Return.VOID,
            convention=Convention.CDECL, doc=None):
        '''
        Creates a new function typedef. So, when a class has an attribute that
        contains a pointer of a function. The attribute will return a Function
        object that will be created by this method.
        '''

        # Create a converter, if it's not a native type
        if return_type not in Return.values:
            return_type = self.create_converter(return_type)

        def make_function(ptr):
            func = ptr.make_function(convention, args, return_type)
            func.__doc__ = doc
            return func

        return make_function

# Create a shared manager instance
manager = TypeManager()