
from SingletonBase import Singleton
import os
import json




class OcioSetupManager:
    __metaclass__ = Singleton

    def __init_(self):
        pass

    def getOcioSetupPath(self):
            ociosettingsPath = self.getOcioSettingsPath()
            if ociosettingsPath == None:
                ociosettingsFilename = "OcioSetup.json"
                ociosettingsPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))           
            
                if os.access(ociosettingsPath, os.W_OK):
                    ociosettingsFilePath = os.path.join(ociosettingsPath, ociosettingsFilename)
                    if os.path.isfile(ociosettingsFilePath):                    
                        if not os.access(ociosettingsFilePath, os.W_OK):                   
                            return None
                        else:
                            return ociosettingsFilePath

                    else :
                        try:
                            settingsFile = open(ociosettingsFilePath, "w+")
                            settingsFile.close()
                            return ociosettingsFilePath
                        except Exception as e:
                            return None
                    
                else :
                    return None
            else :
                return ociosettingsPath


    def getOcioSettingsPath(self):
            
            ocioFileName = "OcioSetup.json"
            savePath = os.getenv("MS_HOUDINI_PATH")
        
            if savePath != None :            
                ociosettingsPath =  os.path.join(savePath, ocioFileName)
                if os.path.exists(savePath):
                
                    if os.access(savePath, os.W_OK) == False :
                        return None


                if os.path.isfile(ociosettingsPath):
                    if os.access(ociosettingsPath, os.W_OK) == False:
                        return None
                    else :
                        return ociosettingsPath

                    try:
                        ociosettingsFile = open(ociosettingsPath, "w+")
                        ociosettingsFile.close()
                        return ociosettingsPath
                    except Exception as e:
                        return None                   

                else:

                    try:                    
                        os.makedirs(savePath)
                        ociosettingsFile = open(ociosettingsPath, "w+")
                        ociosettingsFile.close()
                        return ociosettingsPath
                    except Exception as e:
                        return None

            return None


    def getOcioSetup(self) :
        self.ocioSetupPath = self.getOcioSetupPath()
        try:
            with open(self.ocioSetupPath, 'r') as fl_:
                ocioSetup =  json.load(fl_)
                return ocioSetup


        except Exception as e:
            print("Error reading OCIO setup file")


        

