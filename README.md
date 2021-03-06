# mbfh-v2
 **Fork of the Megascan Bridge for Houdini shipped by Quixel**


The creation of this fork has been motivated by two things :

- My curiosity to try out the new 3delight|NSI with megascan assets, as it is a promising renderer and is not supported by the plugin
- The current stance of Quixel regarding the Megascan Bridge plugins oriented for offline rendering. Indeed, they are on maintenance status only and it is not in their plan to bring any kind of new features or supporting new renderer.  


At the time I started to work on this fork, there were also multiple issues that were plagging the plugin for houdini and was very frustrating ( I believe they fixed most of them in the 4.5, kudos to them). I wanted to share with the community a plugin free of those issues and working as intended. 


This is **WIP**. I am working on this on my free time. Don't hesitate to post issues or feature requests and I will add them if I can find the time to do it.


#**Installation instructions :**

Once you downloaded and unzipped the plugin, you need to specify to houdini where to find it. 
Go to your houdini packages folder location, you should be able to find here :

`"C:\Users\YOUR USER NAME\Documents\houdiniXX.X\packages"`

If you already installed the megascan bridge plugin for houdini, you should already find a MegascanPlugin.json, you can open it and modify the path to point where mbfh-v2 is located, for exemple :

`"E:\\git\\mbfh-v2\\MSLiveLink"`

If you didn't install the megascan bridge plugin already, you have to create a text file first, then rename it "MegascanPlugin.json". Once you've renamed it, you can edit it and add :

`{
  "path": "C:\\path\\to\\your\\plugin"
}`



#**What's new ?**

What I added :
- support of 3delight|NSI,
- support of Renderman24, tested on Renderman24.1,
- basic support of OCIO for 3delight|NSI, Redshift and Renderman 24. You can find a small json file in the plugin folder called OcioSetup.json in which you can add your own config if you need to,
- reworked the scatter setup to be easier to use.


