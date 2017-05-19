import maya.cmds as mc
import maya.OpenMaya as om
import struct
import os
import datetime
import time

progressBarControl = ""
winID = "NinjaRipperImporter"
ripSignature = 0xDEADC0DE
ripFileVersion = 4

filesToImport = []


def getFileNameWithoutExtension(path):
    return path.split('\\').pop().split('/').pop().rsplit('.', 1)[0]


def readString(inFile):
    chars = []
    while True:
        c = inFile.read(1)
        if c == chr(0):
            return "".join(chars)
        chars.append(c)


def readU32(inFile):
    return struct.unpack('I', inFile.read(4))[0]


def readI32(inFile):
    return struct.unpack('i', inFile.read(4))[0]


def readFloat(inFile):
    return struct.unpack('f', inFile.read(4))[0]


def importRipFile(filePath, textureIndex):
    ripDir = os.path.dirname(filePath)
    ripName = getFileNameWithoutExtension(filePath)

    # print ripDir
    # print ripName

    ripFile = open(filePath, "rb")
    signature = readU32(ripFile)
    version = readU32(ripFile)

    # print signature
    # print version
    # print ripSignature
    # print ripFileVersion

    if signature != ripSignature:
        print "Not RIP file"
        return

    if version != ripFileVersion:
        print "Invalid RIP file version"
        return

    facesCount = readU32(ripFile)
    vertexCount = readU32(ripFile)
    vertexSize = readU32(ripFile)
    texturesCount = readU32(ripFile)
    shadersCount = readU32(ripFile)
    vertexAttributesCount = readU32(ripFile)

    PosX_Idx = -1
    PosY_Idx = -1
    PosZ_Idx = -1
    NormX_Idx = -1
    NormY_Idx = -1
    NormZ_Idx = -1
    Tc0_U_Idx = -1
    Tc0_V_Idx = -1

    TempPosIdx = 0
    TempNormalIdx = 0
    TempTexCoordIdx = 0

    vertexAttribTypesArray = []
    textures = []
    faces = om.MIntArray()
    vertices = om.MPointArray()
    polyVerticesCount = om.MIntArray()
    vertexNormals = om.MVectorArray();
    uArray = om.MFloatArray();
    vArray = om.MFloatArray();

    # print "Faces : " + str(facesCount)
    # print "Vertices : " + str(vertexCount)

    for i in range(vertexAttributesCount):
        semantic = readString(ripFile)
        semanticIndex = readU32(ripFile)
        offset = readU32(ripFile)
        size = readU32(ripFile)
        typeMapElements = readU32(ripFile)

        for j in range(typeMapElements):
            typeElement = readU32(ripFile)
            vertexAttribTypesArray.append(typeElement)

        # print "------------"
        # print "Semantic=" + semantic
        # print "SemanticIndex=" + str(semanticIndex)
        # print "Offset=" + str(offset)
        # print "Size=" + str(size)
        # print "TypeMapElements=" + str(typeMapElements)

        if semantic == "POSITION" and TempPosIdx == 0:
            PosX_Idx = offset / 4
            PosY_Idx = PosX_Idx + 1
            PosZ_Idx = PosX_Idx + 2
            TempPosIdx += 1

        if semantic == "NORMAL" and TempNormalIdx == 0:
            NormX_Idx = offset / 4
            NormY_Idx = NormX_Idx + 1
            NormZ_Idx = NormX_Idx + 2
            TempNormalIdx += 1

        if semantic == "TEXCOORD" and TempTexCoordIdx == 0:
            Tc0_U_Idx = offset / 4
            Tc0_V_Idx = Tc0_U_Idx + 1
            TempTexCoordIdx += 1

    # print "-- textures --"
    for i in range(texturesCount):
        texFileName = readString(ripFile)
        textures.append(texFileName)
        # print texFileName

    # print "-- shaders --"
    for i in range(shadersCount):
        shaderName = readString(ripFile)
        textures.append(shaderName)
        # print shaderName

    for i in range(facesCount):
        i0 = readU32(ripFile)
        i1 = readU32(ripFile)
        i2 = readU32(ripFile)
        faces.append(i0)
        faces.append(i1)
        faces.append(i2)
        polyVerticesCount.append(3)

    # print "PosX idx:" + str(PosX_Idx)
    # print "PosY idx:" + str(PosY_Idx)
    # print "PosZ idx:" + str(PosZ_Idx)

    # print "NrmX idx:" + str(NormX_Idx)
    # print "NrmY idx:" + str(NormY_Idx)
    # print "NrmZ idx:" + str(NormZ_Idx)

    # print "U0 idx:" + str(Tc0_U_Idx)
    # print "V0 idx:" + str(Tc0_V_Idx)

    for k in range(vertexCount):

        vx = 0.0
        vy = 0.0
        vz = 0.0

        nx = 0.0
        ny = 0.0
        nz = 0.0

        tu = 0.0
        tv = 0.0

        for j in range(len(vertexAttribTypesArray)):
            elementType = vertexAttribTypesArray[j]

            if elementType == 0:
                tmp = readFloat(ripFile)
            elif elementType == 1:
                tmp = float(readU32(ripFile))
            elif elementType == 2:
                tmp = float(readI32(ripFile))
            else:
                tmp = float(readU32(ripFile))

            if j == PosX_Idx:
                vx = tmp
            elif j == PosY_Idx:
                vy = tmp
            elif j == PosZ_Idx:
                vz = tmp
            elif j == NormX_Idx:
                nx = tmp
            elif j == NormY_Idx:
                ny = tmp
            elif j == NormZ_Idx:
                nz = tmp
            elif j == Tc0_U_Idx:
                tu = tmp
            elif j == Tc0_V_Idx:
                tv = tmp

        vertices.append(om.MPoint(vx, vy, vz))
        vertexNormals.append(om.MVector(nx, ny, nz))
        uArray.append(tu)
        vArray.append(tv)

    # --- Create mesh ---

    # create new mesh
    mesh = om.MFnMesh()
    mesh.create(vertexCount, facesCount, vertices, polyVerticesCount, faces, uArray, vArray)

    print str(vertices.length())
    print str(uArray.length())
    print str(vArray.length())

    # assign uv
    try:
        if Tc0_U_Idx >= 0 and Tc0_V_Idx >= 0:
            mesh.assignUVs(polyVerticesCount, faces)
    except Exception as e:
        print "Can't assign UV to mesh " + ripName
        print type(e)
        print e.args

    # assign normals
    try:
        if NormX_Idx >= 0 and NormY_Idx >= 0 and NormZ_Idx >= 0:
            vertexToNormalIndex = om.MIntArray()
            for i in range(0, vertexCount):
                vertexToNormalIndex.append(i)
            mesh.setVertexNormals(vertexNormals, vertexToNormalIndex)
    except Exception as e:
        print "Can't assign Normals to mesh " + ripName
        print type(e)
        print e.args

    # set attributes
    mc.setAttr(mesh.name() + ".doubleSided", 0)

    # get dag path to new mesh
    selectionList = om.MSelectionList()
    selectionList.add(mesh.name())
    dagPathToMesh = om.MDagPath()
    selectionList.getDagPath(0, dagPathToMesh)
    dagPathToMesh.pop()
    # print dagPathToMesh.fullPathName()

    # rename new mesh
    meshName = mc.rename(dagPathToMesh.fullPathName(), ripName)

    # --- Create material ---

    textureFileName = "not_found.tga"
    if len(textures) > textureIndex and texturesCount > textureIndex:
        textureFileName = ripDir + "/" + textures[textureIndex]

    # print "Assign texture : " + textureFileName

    matName = ripName + "_mat"

    # create material
    shadingNode = mc.shadingNode("lambert", asShader=True, name=matName)
    # create texture file
    fileNode = mc.shadingNode("file", asTexture=True)

    # assign filename
    mc.setAttr(fileNode + ".fileTextureName", textureFileName, type="string")

    shadingGroup = mc.sets(renderable=True, noSurfaceShader=True, empty=True)
    # connect shader to sg surface shader
    mc.connectAttr('%s.outColor' % shadingNode, '%s.surfaceShader' % shadingGroup)
    # connect file texture node to shader's color
    mc.connectAttr('%s.outColor' % fileNode, '%s.color' % shadingNode)

    # --- Assign material to mesh ---

    mc.select(meshName)
    mc.hyperShade(a=shadingNode)

    return


def doImport(fieldID):
    textureIndex = mc.intField(fieldID, query=True, value=True)
    # print textureIndex

    timeStart = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))

    for i in range(0, len(filesToImport)):
        fileName = filesToImport[i]
        print fileName
        mc.progressBar(progressBarControl, edit=True, pr=i)
        importRipFile(fileName, textureIndex)

    timeEnd = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
    workTime = timeEnd - timeStart
    print str(len(filesToImport)) + " file(s) imported. Import time " + str(workTime.total_seconds()) + " sec"

    mc.select(clear=True)
    mc.deleteUI(winID, window=True)

    return


def showImportDialog(filesCount):

    windowSize = (200, 120)
    mc.window(winID, title="Ninja Ripper (options)", widthHeight=(windowSize[0], windowSize[1]), sizeable=False,
              minimizeButton=False, maximizeButton=False)

    mc.columnLayout("mainColumn", adjustableColumn=True)

    mc.separator(style="none", height=10)

    mc.gridLayout("gridLayout", numberOfRowsColumns=(1, 2), cellWidthHeight=(80, 20))
    mc.text(label="Texture index")
    textureIndex = mc.intField(minValue=0, maxValue=16, value=0)
    mc.setParent("..")

    mc.separator(style="none", height=15)

    buttonCommand = "doImport('" + textureIndex + "')"
    # print buttonCommand
    mc.button(label="Import " + str(filesCount) + " file(s)", command=buttonCommand, backgroundColor=(0.0, 0.6, 0.0))
    mc.separator(style="none", height=2)
    mc.button(label="Cancel", command=('mc.deleteUI(\"' + winID + '\", window=True)'), backgroundColor=(0.6, 0.0, 0.0))

    global progressBarControl
    progressBarControl = mc.progressBar(maxValue=filesCount)

    mc.showWindow()

    return


# Entry point
if mc.window(winID, exists=True):
    mc.deleteUI(winID)
basicFilter = "Ninja Ripper Files(*.rip)(*.rip)"
filesToImport = mc.fileDialog2(caption="Ninja Ripper - importer", fileFilter=basicFilter, dialogStyle=2, fileMode=4, okCaption="Import")
if filesToImport is not None:
    showImportDialog(len(filesToImport))
