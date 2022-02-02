![Github all releases downloads](https://img.shields.io/github/downloads/djschaffner/aoe2de_patcher/total)

# AoE2 DE Patcher - WIP

Patches AoE2 DE to any officially released version (Steam version only!)  

Currently only suited for downgrading. To upgrade, please use steam to get to the latest version and downgrade from there if necessary. If i find the time and it's requested by anyone i might add upgrading as supported function back in.

**I am not sure if patching with an installed DLC is working as of right now, since i do not own it myself. If you have tried, please let me know via the issue tracker.**

# Requirements

- Requires a steam account that owns the game
- Requires [.Net Core](https://dotnet.microsoft.com/download/dotnet-core/current/runtime) to run (Console version should be enough)

# Usage
- Start aoe2de_patcher.exe
- Select desired game version & language (Language setting only affects cutscenes / campaign voice overs)
- Select the game directory
- Enter your steam login credentials
- Click \<Patch>
- If prompted, enter the 2FA code
- To restore the previous game version hit \<Restore> after patching (Make sure the game is not open in steam anymore since it will show an error then)

This whole process might take a while to finish!

# Notes
**Your login creedentials will not be stored.** 

~~While it is possible to patch from an old version to the most recent one~~ As of now this is no longer possible - I do suggest to just use the steam "Verify integrity of game cache" functionality just to be extra safe. 

For now, try to avoid closing the program via task manager while it is downloading. Currently I have not found a way to guarantee that downloads will be stopped after doing so!

# FAQ

Q: *Where is the aoe2_updater.exe file?*  
A: Please check that you downloaded the zip file from the *releases* tab and not the source code.

Q: *The patcher says "Could not patch" and "DOTNET core not found". What is wrong?*  
A: You need to install DOTNET core to use the patcher. Please check the reuqirements section above for a link.

Q: *What is the 2FA Code?*  
A: It's the code from your steam authenticator app if you have it. If you don't use that, check your emails for a code.  

Q: *Where is the AoE directory?*  
A: Most likely it is this by default: 'C:\Program Files (x86)\Steam\steamapps\common\AoE2DE' It could be different for you though. 

Q: *Do I have to download a new version when a patch for AoE releases?*  
A: Usually not. When a new DLC is released, there is a high chance that the tool will have to be updated though. You will be informed when you start the tool and a new version is available.

# Future features
- Investigate options to improve upgrading mechanism
- Get pre 35584 versions to work
- Add toggle for Enhanced graphics pack (Warn people because thats a lot of data)
- Maybe add a \<cancel> button
- Make backups optional  
- If you have any other suggestions, feel free to open a ticket and tag it with 'enhancement'

<a href="https://www.buymeacoffee.com/djschaffner" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Drink" style="height: 41px !important;width: 174px !important;" ></a>

*The downloaded files are from steam directly and not hosted by me.*  

*This project is not done yet. There may be bugs and issues and it's possible not everything is working as intended. If you encounter any bugs please open a Ticket with the bug you encountered and a short desceription how it occured.*  
