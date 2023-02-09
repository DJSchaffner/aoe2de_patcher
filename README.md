![Github all releases downloads](https://img.shields.io/github/downloads/djschaffner/aoe2de_patcher/total)

# AoE2 DE Patcher - WIP

Patches AoE2 DE to any officially released version (Steam version only!)  

Currently only suited for downgrading. To upgrade, please use steam to get to the latest version and downgrade from there if necessary. If i find the time and it's requested by anyone i might add upgrading as supported function back in.

<a href="https://www.buymeacoffee.com/djschaffner" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Drink" style="height: 41px !important;width: 174px !important;" ></a>

# Requirements

- Requires a steam account that owns the game
- Requires [.Net Core](https://dotnet.microsoft.com/download/dotnet-core/current/runtime) to run (Console version is enough)

# Usage
- Start aoe2de_patcher.exe
- Select desired game version & language (Language setting only affects cutscenes / campaign voice overs)
- Select the game directory
- Enter your steam login credentials
- Click \<Patch>
- If prompted, enter the 2FA code
- To restore the previous game version hit \<Restore> after patching (Make sure the game is not open in steam anymore since it will show an error then)

This whole process might take a while to finish, please wait until it says - **DONE!**.

# Notes
**Your login creedentials will not be stored.** 

For now, try to avoid closing the program via task manager while it is downloading. Currently I have not found a way to guarantee that downloads will be stopped after doing so!

# FAQ

Q: *Where is the aoe2_updater.exe file?*  
A: Please check that you downloaded the compiled zip file from the [Releases](https://github.com/DJSchaffner/aoe2de_patcher/releases) tab and not the source code.

Q: *The patcher says "Could not patch" and "DOTNET core not found". What is wrong?*  
A: You need to install DOTNET core to use the patcher. Please check the reuqirements section above for a link.

Q: *What is the 2FA Code?*  
A: It's the code from your steam authenticator app if you have it enabled. Otherwise check your emails for a code.  

Q: *Where is the AoE directory?*  
A: Most likely it is this by default: *C:\Program Files (x86)\Steam\steamapps\common\AoE2DE* - It could be different for you though. 

Q: *Do I have to download a new version of the tool when a patch for AoE releases?*  
A: Usually not. If there is a new version available you will be informed when you start the tool.

Q: *Can I use it on Linux?*  
A: Yes, we provide a docker container. You need to build from source with `docker/build.sh`, then run the patcher with `docker/run.sh aoe2de_patcher.dist/aoe2de_patcher.bin`.

# Planned features
- Investigate options to re-add upgrading mechanism
- Get pre 35584 versions to work
- Maybe add a \<cancel> button
- Add a progress bar
- Add colored text to better identify important messages in log
- Make backups optional
- Investigate downloading without credentials (-beta)
- If you have any other suggestions, feel free to open a ticket and tag it with 'enhancement'

# Used third party libraries
- https://github.com/SteamRE/DepotDownloader

***

*The downloaded files are from steam directly and not hosted by me.*  

*This project is not done yet. There may be bugs and issues and it's possible not everything is working as intended. If you encounter any bugs please open a ticket with the bug you encountered and a short description on how it occured.*  
