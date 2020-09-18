# AoE2PatchReverter - WIP

Patches AoE2 DE to any officially released version (Steam version only!)  
Currently downloads more files than necessary, an improved mechanism is planned!

# Requirements

- Requires a steam account that owns the game
- Requires [.Net Core](https://dotnet.microsoft.com/download/dotnet-core/current/runtime) to run

# Usage
- Select desired game version & language (Language setting only affects cutscenes / campaign voice overs for that language)
- Select the game directory
- Enter your steam login credentials
- Click \<Patch>
- If prompted, enter the 2FA code
- To restore the previous game version hit \<Restore> after patching

This whole process takes a while to finish!

# Notes
This project is not done yet. There may be bugs and issues and it's possible not everything is working as intended. If you encounter any bugs please open a Ticket with the bug you encountered and a short desceription how it occured.  

While it is possible to patch from an old version to the most recent one I do suggest to just use the steam "Verify integrity of game cache" functionality just to be extra safe.

Your login creedentials will not be stored for later use.

The downloaded files are from steam directly and not hosted by me.

**Future features**
- Further improve the update process (Only update the files that need updating)
- Add toggle for Enhanced graphics pack (Warn people because thats a lot of data)
- Maybe add a \<cancel> button
- Make backups optional
