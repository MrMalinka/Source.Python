# ../plugins/manager.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
#   Collections
from collections import OrderedDict
#   Sys
import sys

# Source.Python Imports
from core import AutoUnload
from excepthooks import ExceptHooks
#   Plugins
from plugins import PluginsLogger
from plugins import _plugin_strings
from plugins.errors import PluginFileNotFoundError


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
# Add all the global variables to __all__
__all__ = [
    'PluginManager',
]


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
# Get the sp.plugins.manager logger
PluginsManagerLogger = PluginsLogger.manager


# =============================================================================
# >> CLASSES
# =============================================================================
class PluginManager(OrderedDict):
    '''Stores plugins and their instances'''

    def __init__(self, base_import=''):
        '''Called when the class instance is initialized'''

        # Re-call OrderedDict's __init__ to properly setup the object
        super(PluginManager, self).__init__()

        # Store the base import path
        self.base_import = base_import

        # Does the object have a logger set?
        if not hasattr(self, 'logger'):

            # If not, set the default logger
            self.logger = PluginsManagerLogger

        # Does the object have a translations value set?
        if not hasattr(self, 'translations'):

            # If not, set the default translations
            self.translations = _plugin_strings

    def __missing__(self, plugin_name):
        '''Tries to load a plugin that is not loaded'''

        # Try to get the plugin's instance
        try:

            # Get the plugin's instance
            instance = self.instance(plugin_name, self.base_import)

            # Does the plugin have a load function?
            if 'load' in instance.globals:

                # Call the plugin's load function
                instance.globals['load']()

        # Was the file not found?
        # We use this check because we already printed the error to console
        except PluginFileNotFoundError:

            # Return None as the value to show the plugin was not loaded
            return None

        # Was a different error encountered?
        except:

            # Get the error
            error = sys.exc_info()

            # Is the error due to "No module named '<plugin>.<plugin>'"?
            if (len(error[1].args) and error[1].args[0] ==
                    "No module named '{0}.{0}'".format(plugin_name)):

                # Print a message about not using built-in module names
                # We already know the path exists, so the only way this error
                # could occur is if it shares its name with a built-in module
                self.logger.log_message(self.prefix + self.translations[
                    'Built-in'].get_string(plugin=plugin_name))

            # Otherwise
            else:

                # Print the exception to the console
                ExceptHooks.print_exception(*error)

                # Remove all modules from sys.modules
                self._remove_modules(plugin_name)

            # Return None as the value to show the addon was not loaded
            return None

        # Add the plugin to the dictionary with its instance
        self[plugin_name] = instance

        # Return the give instance
        return instance

    def __delitem__(self, plugin_name):
        '''Removes a plugin from the manager'''

        # Is the plugin in the dictionary?
        if not plugin_name in self:

            # Do nothing
            return

        # Print a message about the plugin being unloaded
        self.logger.log_message(self.prefix + self.translations[
            'Unloading'].get_string(plugin=plugin_name))

        # Does the plugin have an unload function?
        if 'unload' in self[plugin_name].globals:

            # Use a try/except here to still allow the plugin to be unloaded
            try:

                # Call the plugin's unload function
                self[plugin_name].globals['unload']()

            # Was an exception raised?
            except:

                # Print the error to console, but
                # allow the plugin to still be unloaded
                ExceptHooks.print_exception()

        # Remove all modules from sys.modules
        self._remove_modules(plugin_name)

        # Remove the plugin from the dictionary
        super(PluginManager, self).__delitem__(plugin_name)

    def is_loaded(self, plugin_name):
        '''Returns whether or not a plugin is loaded'''
        return plugin_name in self

    def get_plugin_instance(self, plugin_name):
        '''Returns a plugin's instance, if it is loaded'''

        # Is the plugin loaded?
        if plugin_name in self:

            # Return the plugin's instance
            return self[plugin_name]

        # Return None if the plugin is not loaded
        return None

    def _remove_modules(self, plugin_name):
        '''Removes all modules from the plugin'''

        # Get the plugins import path
        base_name = self.base_import + plugin_name

        # Loop through all loaded modules
        for module in list(sys.modules):

            # Is the current module within the plugin?
            if module.startswith(base_name):

                # Remove the module
                self._remove_module(module)

    def _remove_module(self, module):
        '''Removes a module and unloads any AutoUnload instances'''

        # Loop through all items in the module
        for y in iter(sys.modules[module].__dict__):

            # Get the item's object
            instance = sys.modules[module].__dict__[y]

            # Is the object an AutoUnload instance
            if not isinstance(instance, AutoUnload):

                # No need to do anything with this object
                continue

            # Is the instance native to the given module?
            if instance.__module__ == module:

                # Unload the object
                instance._unload_instance()

            # Is the instance's callback native to the given module?
            if (hasattr(instance, 'callback') and
                getattr(instance, 'callback').__module__ == module):

                # Unload the object
                instance._unload_instance()

        # Delete the module
        del sys.modules[module]
