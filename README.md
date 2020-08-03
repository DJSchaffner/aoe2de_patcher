# AoE2PatchReverter - WIP

Patches AoE2 DE to any officially released version (Steam version only!)  
Currently downloads the whole update instead of just patching the necessary files, an improved mechanism is planned though!

# Requirements

- Requires a steam account that owns the game
- Requires [.Net Core](https://dotnet.microsoft.com/download/dotnet-core/current/runtime) to run

# Usage
- Select desired game version & language
- Select the game directory
- Enter your steam login credentials
- Click \<Patch>
- If prompted, enter the 2FA code (Might occur multiple times)
- To restore the previous game version hit \<Restore> after patching

This whole process takes a while to finish!

# Notes
This project is not done yet. There may be bugs and issues and it's possible not everything is working as intended. If you encounter any bugs please open a Ticket with the bug you encountered and a short desceription how it occured.

Your login creedentials will not be stored for later use

The downloaded files are from steam directly and not hosted by me

**Future features**
- Grab Update list directly from steam
- Grab manifest ids directly from steam
- Improve the update process (Only update the files that need updating)
- Cancel an active download / Add \<Cancel> button (When you close the app while downloading right now, the download will still finish)
- Add toggle for Enhanced graphics pack (Warn people because thats a lot of data)
