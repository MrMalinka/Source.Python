# ../players/entity.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from conversions_c import playerinfo_from_index
from engine_c import EngineServer
#   Entities
from entities.entity import BaseEntity
#   Players
from players.helpers import address_from_playerinfo
from players.helpers import uniqueid_from_playerinfo
from players.weapons import _PlayerWeapons


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
# Add all the global variables to __all__
__all__ = [
    'PlayerEntity',
]


# =============================================================================
# >> CLASSES
# =============================================================================
class PlayerEntity(BaseEntity, _PlayerWeapons):
    '''Class used to interact directly with players'''

    def __new__(cls, index):
        '''Override the __new__ method to set the
            "entities" attribute and set the PlayerInfo'''

        # Get the "self" object using the super class' __new__
        self = super(PlayerEntity, cls).__new__(cls, index)

        # Set the player's info attribute
        self._info = playerinfo_from_index(self.index)

        # Is the IPlayerInfo instance valid?
        if self.info is None:

            raise ValueError(
                'Invalid IPlayerInfo instance for index "{0}"'.format(index))

        # Set the entities attribute
        self._entities = frozenset(['entity', 'player'])

        # Return the instance
        return self

    @property
    def info(self):
        '''Returns the player's IPlayerInfo instance'''
        return self._info

    @property
    def instances(self):
        '''Yields the player's IPlayerInfo and Edict instances'''
        yield self.info
        yield self.edict

    @property
    def userid(self):
        '''Returns the player's userid'''
        return self.info.get_userid()

    @property
    def steamid(self):
        '''Returns the player's SteamID'''
        return self.info.get_networkid_string()

    @property
    def name(self):
        '''Returns the player's name'''
        return self.info.get_name()

    @property
    def isdead(self):
        '''Returns if the player is dead or alive'''
        return self.info.is_dead()

    @property
    def language(self):
        '''Returns the player's language'''
        return EngineServer.get_client_convar_value(self.index, 'cl_language')

    @property
    def uniqueid(self):
        '''Returns the player's uniqueid'''
        return uniqueid_from_playerinfo(self.info)

    @property
    def address(self):
        '''Returns the player's IP address'''
        return address_from_playerinfo(self.info)

    def get_team(self):
        '''Returns the player's team'''
        return self.info.get_team_index()

    def set_team(self, value):
        '''Sets a players team'''
        self.info.change_team(value)

    # Set the "team" property methods
    team = property(get_team, set_team)
