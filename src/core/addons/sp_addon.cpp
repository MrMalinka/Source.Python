/**
* =============================================================================
* Source Python
* Copyright (C) 2012 Source Python Development Team.  All rights reserved.
* =============================================================================
*
* This program is free software; you can redistribute it and/or modify it under
* the terms of the GNU General Public License, version 3.0, as published by the
* Free Software Foundation.
*
* This program is distributed in the hope that it will be useful, but WITHOUT
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
* FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
* details.
*
* You should have received a copy of the GNU General Public License along with
* this program.  If not, see <http://www.gnu.org/licenses/>.
*
* As a special exception, the Source Python Team gives you permission
* to link the code of this program (as well as its derivative works) to
* "Half-Life 2," the "Source Engine," and any Game MODs that run on software
* by the Valve Corporation.  You must obey the GNU General Public License in
* all respects for all other code used.  Additionally, the Source.Python
* Development Team grants this exception to all derivative works.
*/

//---------------------------------------------------------------------------------
// Includes
//---------------------------------------------------------------------------------
#include "sp_addon.h"
#include "strtools.h"
#include "convar.h"
#include "filesystem.h"
#include "core/sp_gamedir.h"
#include "utility/wrap_macros.h"
#include "modules/listeners/listenermanager.h"
#include "modules/entities/entities_wrap.h"

//---------------------------------------------------------------------------------
// External variables
//---------------------------------------------------------------------------------
extern IFileSystem* filesystem;

//---------------------------------------------------------------------------------
// Static singleton.
//---------------------------------------------------------------------------------
CAddonManager g_AddonManager;

//---------------------------------------------------------------------------------
// Constructor
//---------------------------------------------------------------------------------
CAddonManager::CAddonManager( void )
{

}

//---------------------------------------------------------------------------------
// Destructor
//---------------------------------------------------------------------------------
CAddonManager::~CAddonManager( void )
{

}

//---------------------------------------------------------------------------------
// Calls tick listener.
//---------------------------------------------------------------------------------
void CAddonManager::GameFrame()
{
	CALL_LISTENERS(Tick);
}

//---------------------------------------------------------------------------------
// Calls network id validated listeners.
//---------------------------------------------------------------------------------
void CAddonManager::NetworkIDValidated( const char *pszUserName, const char *pszNetworkID )
{
	CALL_LISTENERS(NetworkidValidated, pszUserName, pszNetworkID);
}

//---------------------------------------------------------------------------------
// Calls level init listeners.
//---------------------------------------------------------------------------------
void CAddonManager::LevelInit( char const *pMapName )
{
	CALL_LISTENERS(LevelInit, pMapName);
}

//---------------------------------------------------------------------------------
// Calls server activate listeners.
//---------------------------------------------------------------------------------
// TODO: will not work if this is really a list
void CAddonManager::ServerActivate( edict_t *pEdictList, int edictCount, int clientMax )
{
	CEdict edict = CEdict(pEdictList);
	CALL_LISTENERS(ServerActivate, edict, edictCount, clientMax);
}

//---------------------------------------------------------------------------------
// Calls level shutdown listeners.
//---------------------------------------------------------------------------------
void CAddonManager::LevelShutdown( void )
{
	CALL_LISTENERS(LevelShutdown);
}

//---------------------------------------------------------------------------------
// Calls client active listeners.
//---------------------------------------------------------------------------------
void CAddonManager::ClientActive( edict_t *pEntity )
{
	CEdict edict = CEdict(pEntity);
	CALL_LISTENERS(ClientActive, edict);
}

//---------------------------------------------------------------------------------
// Calls client disconnect listeners.
//---------------------------------------------------------------------------------
void CAddonManager::ClientDisconnect( edict_t *pEntity )
{
	CEdict edict = CEdict(pEntity);
	CALL_LISTENERS(ClientDisconnect, edict);
}

//---------------------------------------------------------------------------------
// Calls client put in server listeners.
//---------------------------------------------------------------------------------
void CAddonManager::ClientPutInServer( edict_t *pEntity, char const *playername )
{
	CEdict edict = CEdict(pEntity);
	CALL_LISTENERS(ClientPutInServer, edict, playername);
}

//---------------------------------------------------------------------------------
// Calls client settings changed listeners.
//---------------------------------------------------------------------------------
void CAddonManager::ClientSettingsChanged( edict_t *pEdict )
{
	CEdict edict = CEdict(pEdict);
	CALL_LISTENERS(ClientSettingsChanged, edict);
}

//---------------------------------------------------------------------------------
// Calls client connect listeners.
//---------------------------------------------------------------------------------
void CAddonManager::ClientConnect( bool *bAllowConnect, edict_t *pEntity, 
	const char *pszName, const char *pszAddress, char *reject, int maxrejectlen )
{
	CEdict edict = CEdict(pEntity);
	CALL_LISTENERS(ClientConnect, *bAllowConnect, edict, pszName, pszAddress, reject, maxrejectlen);
}

//---------------------------------------------------------------------------------
// Calls on query cvar value finished listeners.
//---------------------------------------------------------------------------------
void CAddonManager::OnQueryCvarValueFinished( QueryCvarCookie_t iCookie, 
	edict_t *pPlayerEntity, EQueryCvarValueStatus eStatus, const char *pCvarName, 
	const char *pCvarValue )
{
	CEdict edict = CEdict(pPlayerEntity);
	CALL_LISTENERS(OnQueryCvarValueFinished, (int) iCookie, edict, eStatus, pCvarName, pCvarValue);
}
//
// 
//
#if(SOURCE_ENGINE >= 3)
void CAddonManager::ClientFullyConnect( edict_t *pEntity )
{
	CEdict edict = CEdict(pEntity);
	CALL_LISTENERS(ClientFullyConnect, edict);
}

void CAddonManager::OnEdictAllocated( edict_t *edict )
{
	CEdict the_edict = CEdict(edict);
	CALL_LISTENERS(OnEdictAllocated, the_edict);
}

void CAddonManager::OnEdictFreed( const edict_t *edict )
{
	CEdict the_edict = CEdict((edict_t* ) edict);
	CALL_LISTENERS(OnEdictFreed, the_edict);
}
#endif