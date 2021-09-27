
from ..Utilities.SingletonBase import Singleton
from .MaterialsCreator import MaterialsCreator
from ..Utilities.OcioSetupManager import OcioSetupManager

import os
import platform
import subprocess
import hou

# Albedo -> PxrSurface.diffuseColour
# Bump -> PxrSurface.bumpNormal
# Displacement -> PxrDisplace
# Fuzz -> PxrSurface.fuzzGain
# Normal -> PxrNormalMap
# Roughness -> PxrSurface.specularRoughness
# Specular -> PxrSurface.specularEdgeColour

def convertToTex(inputPath):
    rendermanPath = os.getenv("RMANTREE")
    if platform.system().lower() == "windows":
        texConverter = "txmake.exe"
    elif platform.system().lower() == "darwin":
        texConverter = "txmake"
    elif platform.system().lower() == "linux":
        texConverter = "txmake"

    converterPath = os.path.join(rendermanPath, "bin", texConverter)    
    if not os.path.isfile(converterPath):
        return ""

    try :
        filepath, fileextension = os.path.splitext(inputPath)
        texFile = filepath + ".tex"        
        if os.path.isfile(texFile):
            return texFile
        conversionArgs = converterPath+ " " + '"'+inputPath+'"'+ " " +'"'+texFile+'"'        
        converting = subprocess.Popen(conversionArgs, stdout=subprocess.PIPE)
        out, err = converting.communicate()
        if err:            
            return ""
        return texFile

    except:
        return ""



class RendermanPixarSurface:
    def __init_(self):
        self.nonLinearMaps = ["albedo", "specular", "translucency"]
    
    def createMaterial(self, assetData, importParams, importOptions):
        rendermanPath = os.getenv("RMANTREE")
        if rendermanPath is None:            
            return None


        self.nonLinearMaps = ["albedo", "specular", "translucency"]

        self.ocioSetupManager = OcioSetupManager()
        self.ocioSetup = self.ocioSetupManager.getOcioSetup()

        self.ocio_settings = {
            "ocio" : {
                "texture" : ["albedo","diffuse","specular","translucency"],
                "texture_lin" : [],
                "texture_raw" : ["roughness","normal","displacement","metalness","opacity","bump"],
            },
            "ocio_param" : "filename_colorspace"

        }

        self.paramMapping ={
            "defaultParams" :{
                "diffuseColorr" : 1,
                "diffuseColorg" : 1,
                "diffuseColorb" : 1,
                "specularFaceColorr" : 1,
                "specularFaceColorg" : 1,
                "specularFaceColorb" : 1,
                "specularEdgeColorr" : 1,
                "specularEdgeColorg" : 1,
                "specularEdgeColorb" : 1,
                "specularRoughness" : 0,
                "specularModelType" : 1,
                "specularFresnelMode" :1
            },
            "mapConnections" : {
                "albedo" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "diffuse" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "roughness" : {
                    "input" : "specularRoughness",
                    "output" : "resultF"
                },
                "specular" : {
                    "input" : "specularEdgeColor",
                    "output" : "resultRGB"
                },
                "fuzz" :{
                    "input" : "fuzzGain",
                    "output" : "resultR"
                },
                "normal" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "bump" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "displacement" :{
                    "input" : "shader1",
                    "output" : "displace"
                },
                "opacity" : {
                    "input" : "presence",
                    "output" : "resultR"
                }
            }

        } #parameter mapping from texture type, output name and input name
        materialNode = hou.node(importParams["materialPath"]).createNode("pxrsurface::3.0", importParams["assetName"])

        for defaultParam in self.paramMapping["defaultParams"].keys():
            materialNode.parm(defaultParam).set(self.paramMapping["defaultParams"][defaultParam])

        #OCIO setup 
        ocioUiSelection = importOptions["UI"]["ImportOptions"]["OCIO"]

        if ocioUiSelection in self.ocioSetup["OCIO"]:
            ocioSelection = ocioUiSelection
            ocioSetupDict = self.ocioSetup["OCIO"][ocioSelection]
        else : 
            ocioSelection = None
                
        if ocioSelection == None :
            print("WARNING : Ocio selection doesn't match the OcioSetup.json config.")

        ocio_param = self.ocio_settings["ocio_param"]



        outputNode = materialNode
        if assetData["type"] == "surface" :
            manifoldNode = hou.node(importParams["materialPath"]).createNode("pxrmanifold2d::24")

        for textureData in assetData["components"]:
            if textureData["type"] == "metalness":
                materialNode.parm("specularExtinctionCoeffr").set(3)
                materialNode.parm("specularExtinctionCoeffg").set(3)
                materialNode.parm("specularExtinctionCoeffb").set(3)

            if textureData["type"] not in self.paramMapping["mapConnections"].keys(): continue
            textureNode = hou.node(importParams["materialPath"]).createNode("pxrtexture::3.0", assetData["id"] + "_" + textureData["type"])
            if textureData["type"] in self.nonLinearMaps: textureNode.parm("linearize").set(1)


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

            texFile = textureData["path"]
            # texFile = convertToTex(textureData["path"])
            texFile = texFile.replace("\\", "/")
            textureNode.parm("filename").set(texFile)
            textureParams = self.paramMapping["mapConnections"][textureData["type"]]
            if textureData["type"] == "normal":                
                normalNode = hou.node(importParams["materialPath"]).createNode("pxrnormalmap::3.0", assetData["id"] + "_pxrNormal")
                normalNode.setNamedInput("inputRGB", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], normalNode, textureParams["output"])

            elif textureData["type"] == "bump":
                bumpNode = hou.node(importParams["materialPath"]).createNode("pxrbump::3.0", assetData["id"] + "_pxrBump")
                bumpNode.setNamedInput("inputBump", textureNode, "resultR")
                materialNode.setNamedInput(textureParams["input"], bumpNode, textureParams["output"])

                
            elif textureData["type"] == "displacement":
                collectionNode = hou.node(importParams["materialPath"]).createNode("collect", importParams["assetName"] + "_displacement")
                dispNode = hou.node(importParams["materialPath"]).createNode("pxrdisplace::3.0", assetData["id"]+ "_pxrDisplace")
                dispNode.setNamedInput("dispAmount", textureNode, "resultR")                
                # True value to be determined from the meta json

                if assetData["type"] == "surface" or assetData["type"] == "atlas":
                    dispValue = "0.15"
                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]                
                    dispNode.parm("dispScalar").set(dispValue)
                else : dispNode.parm("dispScalar").set("0.01")

                # if importOptions["UI"]["ImportOptions"]["EnableUSD"] :
                #     dispNode.parm("dispScalar").set("0")
                collectionNode.setInput(0, materialNode)
                collectionNode.setInput(1, dispNode)
                # collectionNode.setNamedInput("shader1", dispNode, "displace")
                # collectionNode.setNamedInput("shader2", materialNode, "bxdf_out")
                outputNode = collectionNode

                    
            elif textureData["type"] == "roughness":
                roughnessConverter = hou.node(importParams["materialPath"]).createNode("pxrtofloat::3.0")
                roughnessConverter.setNamedInput("input", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], roughnessConverter, textureParams["output"])

            else:
                materialNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])

            if assetData["type"] == "surface" :                
                # pxrmanifold2d::22
                # pxrbumpmanifold2d::22
                textureNode.setNamedInput("manifold", manifoldNode, "result")              
                

            


        return outputNode    



class RendermanTriplanarSurface:
    def __init_(self):
        self.nonLinearMaps = ["albedo", "specular", "translucency"]
    
    def createMaterial(self, assetData, importParams, importOptions):
        rendermanPath = os.getenv("RMANTREE")
        if rendermanPath is None:            
            return None

        self.ocioSetupManager = OcioSetupManager()
        self.ocioSetup = self.ocioSetupManager.getOcioSetup()
        self.ocio_settings = {
            "ocio" : {
                "texture" : ["albedo","diffuse","specular","translucency"],
                "texture_lin" : [],
                "texture_raw" : ["roughness","normal","displacement","metalness","opacity","bump"],
            },
            "ocio_param" : "filename0_colorspace"

        }


        self.nonLinearMaps = ["albedo", "specular", "translucency"]
        self.paramMapping ={
            "defaultParams" :{
                "diffuseColorr" : 1,
                "diffuseColorg" : 1,
                "diffuseColorb" : 1,
                "specularFaceColorr" : 1,
                "specularFaceColorg" : 1,
                "specularFaceColorb" : 1,
                "specularEdgeColorr" : 1,
                "specularEdgeColorg" : 1,
                "specularEdgeColorb" : 1,
                "specularRoughness" : 0,
                "specularModelType" : 1,
                "specularFresnelMode" :1
            },
            "mapConnections" : {
                "albedo" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "diffuse" : {
                    "input" : "diffuseColor",
                    "output" : "resultRGB"
                },
                "roughness" : {
                    "input" : "specularRoughness",
                    "output" : "resultF"
                },
                "specular" : {
                    "input" : "specularEdgeColor",
                    "output" : "resultRGB"
                },
                "fuzz" :{
                    "input" : "fuzzGain",
                    "output" : "resultR"
                },
                "normal" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "bump" : {
                    "input" : "bumpNormal",
                    "output" : "resultN"
                },
                "displacement" :{
                    "input" : "shader1",
                    "output" : "displace"
                },
                "opacity" : {
                    "input" : "presence",
                    "output" : "resultR"
                }
            }

        } #parameter mapping from texture type, output name and input name
        materialNode = hou.node(importParams["materialPath"]).createNode("pxrsurface::3.0", importParams["assetName"])


        #OCIO setup 
        ocioUiSelection = importOptions["UI"]["ImportOptions"]["OCIO"]

        if ocioUiSelection in self.ocioSetup["OCIO"]:
            ocioSelection = ocioUiSelection
            ocioSetupDict = self.ocioSetup["OCIO"][ocioSelection]
        else : 
            ocioSelection = None
                
        if ocioSelection == None :
            print("WARNING : Ocio selection doesn't match the OcioSetup.json config.")

        ocio_param = self.ocio_settings["ocio_param"]
        #OCIO setup END

        for defaultParam in self.paramMapping["defaultParams"].keys():
            materialNode.parm(defaultParam).set(self.paramMapping["defaultParams"][defaultParam])

        outputNode = materialNode
        
        roundCubeNode = hou.node(importParams["materialPath"]).createNode("pxrroundcube::3.0")

        for textureData in assetData["components"]:
            if textureData["type"] == "metalness":
                materialNode.parm("specularExtinctionCoeffr").set(3)
                materialNode.parm("specularExtinctionCoeffg").set(3)
                materialNode.parm("specularExtinctionCoeffb").set(3)

            
            textureNode = hou.node(importParams["materialPath"]).createNode("pxrmultitexture::3.0", assetData["id"] + "_" + textureData["type"])

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

            texFile = textureData["path"]

            # if textureData["type"] in self.nonLinearMaps: textureNode.parm("linearize").set(1)
            # texFile = convertToTex(textureData["path"])
            texFile = texFile.replace("\\", "/")
            textureNode.parm("filename0").set(texFile)

            if textureData["type"] not in self.paramMapping["mapConnections"].keys(): continue

            textureParams = self.paramMapping["mapConnections"][textureData["type"]]
            if textureData["type"] == "normal":                
                normalNode = hou.node(importParams["materialPath"]).createNode("pxrnormalmap::3.0", assetData["id"] + "_pxrNormal")
                normalNode.setNamedInput("inputRGB", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], normalNode, textureParams["output"])

            elif textureData["type"] == "bump":
                bumpNode = hou.node(importParams["materialPath"]).createNode("pxrbump::3.0", assetData["id"] + "_pxrBump")
                bumpNode.setNamedInput("inputBump", textureNode, "resultR")
                materialNode.setNamedInput(textureParams["input"], bumpNode, textureParams["output"])

            elif textureData["type"] == "displacement":
                collectionNode = hou.node(importParams["materialPath"]).createNode("collect", importParams["assetName"] + "_displacement")
                dispNode = hou.node(importParams["materialPath"]).createNode("pxrdisplace::3.0", assetData["id"]+ "_pxrDisplace")
                dispNode.setNamedInput("dispAmount", textureNode, "resultR")                
                # True value to be determined from the meta json

                if assetData["type"] == "surface" or assetData["type"] == "atlas":
                    dispValue = "0.15"
                    for assetMeta in assetData["meta"]:
                        if assetMeta["key"] == "height":
                            dispValue = assetMeta["value"].split(" ")[0]                
                    dispNode.parm("dispScalar").set(dispValue)
                else : dispNode.parm("dispScalar").set("0.01")

                # if importOptions["UI"]["ImportOptions"]["EnableUSD"] :
                #     dispNode.parm("dispScalar").set("0")
                collectionNode.setInput(0, materialNode)
                collectionNode.setInput(1, dispNode)
                # collectionNode.setNamedInput(textureParams["input"], dispNode, textureParams["output"])
                # collectionNode.setNamedInput("shader2", materialNode, "bxdf_out")
                outputNode = collectionNode

                    
            elif textureData["type"] == "roughness":
                roughnessConverter = hou.node(importParams["materialPath"]).createNode("pxrtofloat::3.0")
                roughnessConverter.setNamedInput("input", textureNode, "resultRGB")
                materialNode.setNamedInput(textureParams["input"], roughnessConverter, textureParams["output"])

            else:
                materialNode.setNamedInput(textureParams["input"], textureNode, textureParams["output"])                    
                
            textureNode.setNamedInput("manifoldMulti", roundCubeNode, "resultMulti")              
                

            
        

        return outputNode    



def registerRendermanMaterials():    
    # materialTypes = ["Principled", "Triplanar"]
    pixarSurfaceFactory = RendermanPixarSurface()
    rendermanTriplanar = RendermanTriplanarSurface()

    materialsCreator = MaterialsCreator()
    materialsCreator.registerMaterial("Renderman", "Pixar Surface", pixarSurfaceFactory.createMaterial)
    materialsCreator.registerMaterial("Renderman", "Pixar Triplanar", rendermanTriplanar.createMaterial)
    
    # materialsCreator.registerMaterial("Renderman", "PixarSurface_USD", pixarSurfaceFactory.createMaterial)
    

registerRendermanMaterials()

