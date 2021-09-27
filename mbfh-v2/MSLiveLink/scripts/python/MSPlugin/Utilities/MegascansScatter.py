from .SingletonBase import Singleton
from .AssetData import *

import hou
class MegascansScatter:
    __metaclass__ = Singleton
    def __init__(self):
        pass

    def createScatter(self, sourceMeshes, targetMesh, scatterPath, importOptions):
        geometryContainer = hou.node(scatterPath).createNode("geo", "Scatter_Setup")
        if importOptions["UI"]["ImportOptions"]["Renderer"] == "Redshift":
            geometryContainer.parm("RS_objprop_displace_enable").set(1)
            geometryContainer.parm("RS_objprop_displace_scale").set(0.01)

        elif importOptions["UI"]["ImportOptions"]["Renderer"] == "Arnold":
            geometryContainer.parm("ar_disp_height").set(0.008)

        elif importOptions["UI"]["ImportOptions"]["Renderer"] == "3Delight":
            geometryContainer.parm("_3dl_render_poly_as_subd").set(1)
            geometryContainer.parm("_3dl_use_alembic_procedural").set(1)


        sourceMerge = geometryContainer.createNode("object_merge", "SourceObjects")
        # sourceMerge.parm("pack").set(1)
        sourceMerge.parm("numobj").set(len(sourceMeshes))
        for index, sourceMesh in enumerate(sourceMeshes):
            sourceMerge.parm("objpath"+str(index+1)).set(sourceMesh)


        if targetMesh == None:
            targetMerge = geometryContainer.createNode("grid")
        else:
            targetMerge = hou.node(geometryContainer.path()).createNode("object_merge", "TargetMesh")
            targetMerge.parm("objpath1").set(targetMesh)

        scatterNode = targetMerge.createOutputNode("quixel_simple_scattering::1.0")

        attWrangle = scatterNode.createOutputNode("attribwrangle")
        attWrangleVex = "int objectNumber = npoints(1);\n"
        attWrangleVex += "i@variant = int(fit01((rand(@ptnum)), 0, objectNumber));\n"
        attWrangle.parm("snippet").set(attWrangleVex)
        attWrangle.setInput(1, sourceMerge)


        if GetMajorVersion() == "18":
            copyPoints = sourceMerge.createOutputNode("copytopoints::2.0")

        else :
            copyPoints = sourceMerge.createOutputNode("copytopoints")
        copyPoints.setInput(1, attWrangle)
        copyPoints.parm("useidattrib").set(1)

        if importOptions["UI"]["ImportOptions"]["Renderer"] == "3Delight":
            copyPoints.parm("pack").set(1)

        nullScatterOut = copyPoints.createOutputNode("null", "OUT_scatter")
        
        nullScatterOut.setDisplayFlag(True)
        nullScatterOut.setRenderFlag(True)
        
        # sourceMerge.setRenderFlag(False)
        # blockBegin2.setRenderFlag(False)

        
        geometryContainer.layoutChildren()

        









        

