# mbfh-v2
 **Fork of the Megascan Bridge for Houdini shipped by Quixel**


The creation of this fork has been motivated by two things :

- My curiosity to try out the new 3delight|NSI with megascan assets, as it seems to be a promising renderer and is not supported by the plugin
- The current stance of Quixel regarding the Megascan Bridge plugins oriented for offline rendering. Indeed, they are on maintenance status only and it is not in their plan to bring any kind of new features or supporting new renderer.  


At the time I started to work on this fork, there were also multiple issues that were plagging the plugin for houdini and was very frustrating ( I believe they fixed most of them in the 4.5, kudos to them). I wanted to share with the community a plugin free of those issues and working as intended. 


**Installation instructions :**

Once you downloaded and unzipped the plugin, you need to specify to houdini where to find the plugin. 
Go to your houdini packages folder location, the path should looks like something like that :

`"C:\Users\YOUR USER NAME\Documents\houdiniXX.X\packages"`

If you already installed the megascans bridge plugin for houdini, you should already find a MegascanPlugin.json, you can open it and modify the path to point where mbfh-v2 is located, for exemple :

`"E:\\git\\mbfh-v2\\MSLiveLink"`

If you didn't install the megascan bridge plugin already, you have to create a text file first, then rename it "MegascanPlugin.json". Once you've renamed it, you can edit it and add :

`{
  "path": "C:\\path\\to\\your\\plugin"
}`

