from ..Utilities.SettingsManager import SettingsManager
from ..Utilities.SingletonBase import Singleton
from .ImportSurface import ImportSurface
from ..Utilities.MegascansScatter import MegascansScatter
from ..Utilities.USDVariant import *
import os


import hou

class ImportPlantUSD:
    __metaclass__ = Singleton

    def __init__(self):
        pass
    def importPlantUSD(self, assetData, importOptions, importParams):
        fileextension = os.path.splitext(assetData["meshList"][0]["path"])[1]
        plantVariations = None
        if fileextension != ".abc":
            plantVariations = self.setupGeometry(assetData, importOptions, importParams)
        usdVariantSetup(plantVariations, assetData, importOptions, importParams)

        
    def setupGeometry(self, assetData, importOptions, importParams):
        allVariations = []
        geometryContainer = hou.node(importParams["assetPath"]).createNode("geo", "Variations")

        for variationData in assetData["meshList"]:
            fileImportNode = geometryContainer.createNode("file")
            fileImportNode.parm("file").set(variationData["path"])
            transformNode = fileImportNode.createOutputNode("xform")
            transformNode.parm("scale").set("0.01")
            attribDelete = transformNode.createOutputNode("attribdelete")
            attribDelete.parm("ptdel").set("fbx_*")
            attribDelete.parm("vtxdel").set("Cd")
            packNode = attribDelete.createOutputNode("pack")

            outputNullNode = packNode.createOutputNode("null", variationData["name"].split(".")[0])
            allVariations.append(outputNullNode)
            outputNullNode.setDisplayFlag(True)

        # fileImportNode.setRenderFlag(False)
        geometryContainer.layoutChildren()

        return allVariations
        
    

class ImportPlant:
    __metaclass__ = Singleton

    def __init__(self):
        pass

    def importAsset(self, assetData, importOptions, importParams ):

        if importOptions["UI"]["ImportOptions"]["EnableUSD"]:
            ImportPlantUSD().importPlantUSD(assetData, importOptions, importParams)
            return        

        plantsActiveOutput = []
        plantsSelectorOutput = []
        materialContainer = hou.node(importParams["assetPath"]).createNode("matnet", "Asset_Material")
        importParams["materialPath"] = materialContainer.path()
        assetMaterial = ImportSurface().importAsset(assetData, importOptions, importParams)
        assetMaterialPath = ""
        if assetMaterial is not None: assetMaterialPath = assetMaterial.path()
        selectedLod = None

        for plantVar in assetData["meshList"]:
            outputNullName = importParams["assetName"] +  "_" + plantVar["name"].split(".")[0]
            geometryContainer = hou.node(importParams["assetPath"]).createNode("geo", plantVar["name"].split(".")[0])
            geometryContainer.setSelected(True)
            if importOptions["UI"]["ImportOptions"]["Renderer"] == "Redshift":
                geometryContainer.parm("RS_objprop_displace_enable").set(1)
                geometryContainer.parm("RS_objprop_displace_scale").set(0.01)

            elif importOptions["UI"]["ImportOptions"]["Renderer"] == "Arnold":
                geometryContainer.parm("ar_disp_height").set(0.008)

            elif importOptions["UI"]["ImportOptions"]["Renderer"] == "3Delight":
                geometryContainer.parm("shop_materialpath").set(assetMaterialPath)
            
            varActiveLod = self.createGeometrySetup(plantVar["path"],assetMaterialPath, geometryContainer.path(), importOptions, outputNullName, importOptions["UI"]["ImportOptions"]["ApplyMotion"])
            plantsActiveOutput.append(varActiveLod)
            if importOptions["UI"]["ImportOptions"]["EnableLods"] :
                lodList = self.getPlantLodList(assetData, plantVar["name"].split("_")[0])
                if len(lodList) > 0:
                    selectedOutName = plantVar["name"].split(".")[0].split("_")[0]
                    switchNode = hou.node(geometryContainer.path()).createNode("switch", "LOD_Switch")
                    selectedLod = switchNode.createOutputNode("null", selectedOutName)
                    switchNode.setNextInput(varActiveLod)
                    plantsSelectorOutput.append(selectedLod)
                    selectedLod.setDisplayFlag(True)
                    selectedLod.setRenderFlag(True)
                              
                for lodData in lodList:
                    if assetData["meshList"][0]["name"].split(".")[-1] != lodData["name"].split(".")[-1]:
                        continue
                    
                    lodOutputName = importParams["assetName"] + "_" + lodData["name"].split(".")[0]
                    
                    lodOutput = self.createGeometrySetup(lodData["path"], assetMaterialPath, geometryContainer.path(), importOptions, lodOutputName)
                    if switchNode is not None: switchNode.setNextInput(lodOutput)

                if selectedLod is not None:
                    selectedLod.setDisplayFlag(True)
                    selectedLod.setRenderFlag(True)

        


        hou.node(importParams["assetPath"]).layoutChildren()
        if importOptions["UI"]["ImportOptions"]["UseScattering"]:
            if importOptions["UI"]["ImportOptions"]["EnableLods"] :
                assetPaths = [asset.path() for asset in plantsSelectorOutput ]
            else :
                assetPaths = [asset.path() for asset in plantsActiveOutput ]

            MegascansScatter().createScatter(assetPaths,None, importParams["assetPath"], importOptions)


    def createGeometrySetup(self, meshSourcePath, materialPath, targetPath, importOptions, outputName= "Out", applyMotion = False):
        uniformScale = 0.01
        fileextension = os.path.splitext(meshSourcePath)[1]

        if fileextension == ".abc":
            fileImportNode = hou.node(targetPath).createNode("alembic")
            fileImportNode.parm("fileName").set(meshSourcePath.replace("\\", "/"))
        else :
            fileImportNode = hou.node(targetPath).createNode("file")
            fileImportNode.parm("file").set(meshSourcePath.replace("\\", "/"))


        transformNode = fileImportNode.createOutputNode("xform")
        transformNode.parm("scale").set(uniformScale)

        # attribDelete = transformNode

        if fileextension == ".fbx":
            attribDelete = transformNode.createOutputNode("attribdelete")
            attribDelete.parm("ptdel").set("fbx_*")
            attribDelete.parm("vtxdel").set("Cd")
            packNode = attribDelete.createOutputNode("pack")
            if importOptions["UI"]["ImportOptions"]["Renderer"] == "3Delight":
                materialNode = packNode
            else :
                materialNode = packNode.createOutputNode("material")
        else :
            if importOptions["UI"]["ImportOptions"]["Renderer"] == "3Delight":
                materialNode = transformNode
            else :
                materialNode = transformNode.createOutputNode("material")
                materialNode.parm("shop_materialpath1").set(materialPath)

        if applyMotion == True:
            materialNode = materialNode.createOutputNode("quixel_simple_motion")
        outputNullNode = materialNode.createOutputNode("null", outputName)

        outputNullNode.setDisplayFlag(True)
        outputNullNode.setRenderFlag(True)
        # fileImportNode.setRenderFlag(False)
        hou.node(targetPath).layoutChildren()
        # outputNullNode.setRenderFlag(False)
        return outputNullNode

    def getPlantLodList (self, assetData, currentVar):
        lodList = []
        for lodData in assetData["lodList"]:
            lodVar = lodData["name"].split("_")[0]
            if currentVar == lodVar and lodData["lod"] > assetData["activeLOD"]:
                lodList.append(lodData)

        return lodList
