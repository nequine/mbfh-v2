from ..Utilities.SingletonBase import Singleton
from .MaterialsCreator import MaterialsCreator
from ..Utilities.AssetData import *
from ..Utilities.OcioSetupManager import OcioSetupManager

import hou
import os

class DelightPrincipledMaterialFactory:
    __metaclass__ = Singleton
    def __init_(self):
        pass
    
    def createMaterial(self, assetData, importParams, importOptions):
        gammaEnabled = ["roughness", "normal", "bump", "displacement", "metalness"]

        self.ocioSetupManager = OcioSetupManager()
        self.ocioSetup = self.ocioSetupManager.getOcioSetup()

        self.ocio_settings = {
            "ocio" : {
                "texture" : ["albedo","diffuse","specular","translucency"],
                "texture_lin" : [],
                "texture_raw" : ["roughness","normal","displacement","metalness","opacity","bump"],
            },
            "ocio_param" : "textureFile_meta_colorspace"

        }
        
        self.delightMaterialSettings = {
            "mapConnections" :{
                "albedo" : {
                    "input" : "i_color",
                    "output" : "outColor"
                },
                "diffuse" : {
                    "input" : "i_color",
                    "output" : "outColor"
                },
                "roughness" : {
                    "input" : "roughness",
                    "output" : "outColorR"
                },

                "specular" : {
                    "input" : "specular_level",
                    "output" : "outColorR"
                },
                "normal" : {
                    "input" : "disp_normal_bump_value",
                    "output" : "outColor"
                },
                "bump" : {
                    "input" : "disp_normal_bump_value",
                    "output" : "outColor"
                },
                "opacity" : {
                    "input" : "opacity",
                    "output" : "outColorR"
                },
                "translucency": {
                    "input": "translucency",
                    "output": "outColor"
                },
                "displacement" :{
                    "input" : "Displacement",
                    "output" : "outDisplacement"
                },
                "metalness" : {
                    "input" : "metalness",
                    "output" : "outColorR"
                }
            }

        }


        materialPath = importParams["materialPath"]
        materialContainer = hou.node(materialPath)


        thinCategories=["plant","plants","3dplant","leaf"]
        assetCategories=[]
        for i in assetData["categories"]:  
            assetCategories.append(i)
        intersectionCategories = frozenset(thinCategories).intersection(assetCategories)

        if intersectionCategories != frozenset([]) :   
            shaderNodeName = "3Delight::dlThin"
        else : 
            shaderNodeName = "3Delight::dlPrincipled"

        shaderNode = materialContainer.createNode(shaderNodeName)
        shaderNode.parm("roughness").set(0.3)
        


        materialNode = materialContainer.createNode("dlTerminal", importParams["assetName"])
        materialNode.setNamedInput("Surface", shaderNode, "outColor")

        bumpPriority = False
        normalPriority = False

        ocioUiSelection = importOptions["UI"]["ImportOptions"]["OCIO"]

        if ocioUiSelection in self.ocioSetup["OCIO"]:
            ocioSelection = ocioUiSelection
            ocioSetupDict = self.ocioSetup["OCIO"][ocioSelection]
        else : 
            ocioSelection = None
                
        if ocioSelection == None :
            print("WARNING : Ocio selection doesn't match the OcioSetup.json config.")

        ocio_param = self.ocio_settings["ocio_param"]
        

        for textureData in assetData["components"]:

            if textureData["type"] not in self.delightMaterialSettings["mapConnections"].keys(): continue
            textureParams = self.delightMaterialSettings["mapConnections"][textureData["type"]]

            textureNode = materialContainer.createNode("3Delight::dlTexture", textureData["type"])
            textureNode.parm("textureFile").set(textureData["path"].replace("\\", "/"))
            
            if ocioSelection != None :
                if textureData["type"] in self.ocio_settings["ocio"]["texture"] :
                    filename, file_extension = os.path.splitext(textureData["path"])
                    if file_extension == ".exr" :
                        ocio_param_value = ocioSetupDict["texture_lin"]
                    else : 
                        ocio_param_value = ocioSetupDict["texture"]
                elif textureData["type"] in self.ocio_settings["ocio"]["texture_lin"] :
                    ocio_param_value = ocioSetupDict["texture_lin"]
                elif textureData["type"] in self.ocio_settings["ocio"]["texture_raw"] :
                    ocio_param_value = ocioSetupDict["texture_raw"]
            
            textureNode.parm(ocio_param).set(ocio_param_value)

            if textureData["type"] == "translucency":
                shaderNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])
                shaderNode.setNamedInput("color_back", textureNode, textureParams["output"])


            elif textureData["type"] == "normal":
                shaderNode.parm("disp_normal_bump_type").set("1")
                normalPriority = True


            elif textureData["type"] == "bump":
                # bumpNode = materialContainer.createNode("3Delight::dlTexture")
                if normalPriority != True:
                    shaderNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])
                #     materialNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])
                # bumpNode.setNamedInput("input", textureNode, "outColor")


            if textureData["type"] == "displacement":

                exrPath = getExrDisplacement(textureData["path"])
                textureNode.parm("textureFile").set(exrPath.replace("\\", "/"))
                dispNode = materialContainer.createNode("3Delight::dlDisplacement")
                materialNode.setNamedInput(textureParams["input"], dispNode, textureParams["output"])
                dispNode.parm("scalarCenter").set("0.5")
                textureNode.parm("colorOffsetr").set("-0.25")
                textureNode.parm("colorOffsetg").set("-0.25")
                textureNode.parm("colorOffsetb").set("-0.25")
                dispNode.setNamedInput("scalarDisplacement", textureNode, "outColorR")
                dispValue = "0.1"
                if assetData["type"] == "surface" or assetData["type"] == "atlas":

                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]
                    dispNode.parm("scalarScale").set(dispValue)
                else : dispNode.parm("scalarScale").set(dispValue)


            elif textureData["type"] == "albedo" or textureData["type"] == "diffuse":
                ccNode = materialContainer.createNode("3Delight::dlColorCorrection")
                ccNode.setNamedInput("input", textureNode, "outColor")
                shaderNode.setNamedInput("i_color", ccNode, "outColor")


            else:
                shaderNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])


        return materialNode




class DelightTriplanarMaterialFactory:
    __metaclass__ = Singleton
    def __init_(self):
        pass
    
    def  createMaterial(self, assetData, importParams, importOptions):

        self.ocioSetupManager = OcioSetupManager()
        self.ocioSetup = self.ocioSetupManager.getOcioSetup()
        
        gammaEnabled = ["roughness", "normal", "bump", "displacement", "metalness", "opacity", "specular"]

        self.ocio_settings = {
            "ocio" : {
                "texture" : ["albedo","diffuse","specular","translucency"],
                "texture_lin" : [],
                "texture_raw" : ["roughness","normal","displacement","metalness","opacity","bump"],
            },
            "ocio_param" :  { 
                "color" : "color_texture_meta_colorspace",
                "float" : "float_texture_meta_colorspace"
                } 
            }


        self.delightTriplanarSettings = {
            "mapConnections": {
                "albedo": {
                    "input": "i_color",
                    "output": "outColor"
                },
                "diffuse": {
                    "input": "i_color",
                    "output": "outColor"
                },
                "roughness": {
                    "input": "roughness",
                    "output": "outFloat"
                },

                "specular": {
                    "input": "specular_level",
                    "output": "outFloat"
                },
                "normal": {
                    "input": "disp_normal_bump_value",
                    "output": "outColor"
                },
                "bump": {
                    "input": "disp_normal_bump_value",
                    "output": "outFloat"
                },
                "opacity": {
                    "input": "opacity",
                    "output": "outFloat"
                },
                "displacement": {
                    "input": "Displacement",
                    "output": "outDisplacement"
                },
                "metalness": {
                    "input": "metalness",
                    "output": "outFloat"
                }
            }
        }


        materialContainer = hou.node(importParams["materialPath"])
        
        shaderNode = materialContainer.createNode("3Delight::dlPrincipled")
        shaderNode.parm("specular_level").set(0)
        shaderNode.parm("roughness").set(1)
        
        materialNode = materialContainer.createNode("dlTerminal", importParams["assetName"])
        
        materialNode.setNamedInput("Surface", shaderNode, "outColor")


        ### TRIPLANAR WITH WORKAROUND SETUP FROM HERE

        inputTexture = ""

        ocioUiSelection = importOptions["UI"]["ImportOptions"]["OCIO"]

        if ocioUiSelection in self.ocioSetup["OCIO"]:
            ocioSelection = ocioUiSelection
            ocioSetupDict = self.ocioSetup["OCIO"][ocioSelection]
        else : 
            ocioSelection = None
                
        if ocioSelection == None :
            print("WARNING : Ocio selection doesn't match the OcioSetup.json config.")

        


        for textureData in assetData["components"]:

            if textureData["type"] not in self.delightTriplanarSettings["mapConnections"].keys(): continue
            textureParams = self.delightTriplanarSettings["mapConnections"][textureData["type"]]
            triplanarNode = materialContainer.createNode("3Delight::dlTriplanar", textureData["type"])

            if ocioSelection != None :
                if textureData["type"] in self.ocio_settings["ocio"]["texture"] :
                    inputTexture = "color_texture"
                    # ocio_param_value = ocioSetupDict["texture"]
                    ocio_param = self.ocio_settings["ocio_param"]["color"]
                    filename, file_extension = os.path.splitext(textureData["path"])
                    if file_extension == ".exr" :
                        ocio_param_value = ocioSetupDict["texture_lin"]
                    else : 
                        ocio_param_value = ocioSetupDict["texture"]
                elif textureData["type"] in self.ocio_settings["ocio"]["texture_lin"] :
                    inputTexture = "float_texture"
                    ocio_param_value = ocioSetupDict["texture_lin"]
                    ocio_param = self.ocio_settings["ocio_param"]["float"]
                elif textureData["type"] == "normal":
                    inputTexture = "color_texture"
                    ocio_param = self.ocio_settings["ocio_param"]["color"]
                    shaderNode.parm("disp_normal_bump_type").set("1")
                    normalPriority = True
                elif textureData["type"] in self.ocio_settings["ocio"]["texture_raw"] :
                    inputTexture = "float_texture"
                    ocio_param_value = ocioSetupDict["texture_raw"]
                    ocio_param = self.ocio_settings["ocio_param"]["float"]
            
            triplanarNode.parm(ocio_param).set(ocio_param_value)
                    
            triplanarNode.parm(inputTexture).set(textureData["path"].replace("\\", "/"))
            triplanarNode.parm("space").set("1")
            #triplanarNode.parm("tile_removal").set("1")



            if textureData["type"] == "displacement":

                exrPath = getExrDisplacement(textureData["path"])
                # triplanarNode.parm("float_texture").set(exrPath.replace("\\", "/"))
                dispNode = materialContainer.createNode("3Delight::dlDisplacement")
                dispNode.parm("scalarCenter").set("0.5")
                ccNode = materialContainer.createNode("3Delight::dlColorCorrection")
                ccNode.setNamedInput("input", triplanarNode, "outFloat")
                dispNode.setNamedInput("scalarDisplacement", ccNode, "outColorR")
                materialNode.setNamedInput(textureParams["input"], dispNode, textureParams["output"])
                ccNode.parm("offsetr").set("-0.25")
                ccNode.parm("offsetg").set("-0.25")
                ccNode.parm("offsetb").set("-0.25")

                if assetData["type"] == "surface" or assetData["type"] == "atlas":

                    dispValue = "1"
                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]
                    dispNode.parm("scalarScale").set(dispValue)
                else : dispNode.parm("scalarScale").set(dispValue)

            elif textureData["type"] == "albedo" or textureData["type"] == "diffuse":
                ccNode = materialContainer.createNode("3Delight::dlColorCorrection")
                ccNode.setNamedInput("input", triplanarNode, "outColor")
                shaderNode.setNamedInput("i_color", ccNode, "outColor")


            else:
                shaderNode.setNamedInput(textureParams["input"], triplanarNode, textureParams["output"])


        nodes = materialContainer.allSubChildren()
        for n in nodes:
            if n.type().name() == "makexform" :
                n.destroy()

        nodes = materialContainer.allSubChildren()
        xform = materialContainer.createNode("makexform", "xform")
        for n in nodes :
            if n.type().name() == "3Delight::dlTriplanar":
                dltriplanar = n
                dltriplanar.setNamedInput("placementMatrix", xform, "xform")



        return materialNode





                ### TRIPLANAR WITH HDA SETUP FROM HERE
        # triplanarNode = materialContainer.createNode("quixel_delight_triplanar::1.1")
    #     self.setMaterialParameters(triplanarNode, materialNode,shaderNode, assetData, materialContainer)
    #     return materialNode

    def setMaterialParameters(self,triplanarNode, materialNode, shaderNode, assetData, materialContainer):
        bumpPriority = False
        normalBumpCombo = False
        maptypes = [texture["type"] for texture in assetData["components"] ]
        if "bump" in maptypes and "normal" in maptypes:
            normalBumpCombo = True


        for textureData in assetData["components"]:
            if triplanarNode.parm(textureData["type"]) is not None:
                triplanarNode.parm(textureData["type"]).set(textureData["path"].replace("\\", "/"))
                if textureData["type"] not in self.DelightTriplanarSettings["mapConnections"].keys(): continue

                if textureData["type"] == "displacement":
                    materialNode.setNamedInput(self.DelightTriplanarSettings["mapConnections"][textureData["type"]], triplanarNode, textureData["type"])

                elif textureData["type"] == "normal":
                    normalNode = materialContainer.createNode("arnold::normal_map")
                    normalNode.setNamedInput("input", triplanarNode, "normal")
                    normalNode.parm("color_to_signed").set(0)
                    if bumpPriority == False:
                        shaderNode.setNamedInput("normal", normalNode, "vector")

                elif textureData["type"] == "bump":
                    bumpNode = materialContainer.createNode("arnold::bump2d")
                    bumpNode.parm("bump_height").set(0.5)
                    shaderNode.setNamedInput("normal", bumpNode, "vector")
                    bumpNode.setNamedInput("bump_map", triplanarNode, "normal")
                    bumpPriority = True

                else:
                    shaderNode.setNamedInput(self.DelightTriplanarSettings["mapConnections"][textureData["type"]], triplanarNode, textureData["type"])

        if normalBumpCombo == True:
            shaderNode.setNamedInput("normal", bumpNode, "vector")
            bumpNode.setNamedInput("normal", normalNode, "vector")
                




def registerMaterials():    
    
    DelightPrincipledFactory = DelightPrincipledMaterialFactory()
    DelightTriplanarFactory = DelightTriplanarMaterialFactory()
    materialsCreator = MaterialsCreator()
    materialsCreator.registerMaterial("3Delight", "Triplanar", DelightTriplanarFactory.createMaterial)
    materialsCreator.registerMaterial("3Delight", "Principled", DelightPrincipledFactory.createMaterial)
    
    

registerMaterials()