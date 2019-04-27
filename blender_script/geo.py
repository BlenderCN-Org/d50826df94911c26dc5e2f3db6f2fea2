import bpy
import bmesh
import os
from collections.abc import Iterable
import numpy as np
from math import radians
import struct
import json
from mathutils import Matrix

"""
DEFINE CONSTANT
"""

"""
Basic
"""


def view_selected_index():
    """
    The index of selected vertices in 3D view
    :return: a list of verts
    """
    obj = bpy.context.object
    bm = bmesh.from_edit_mesh(obj.data)
    verts = [v.index for v in bm.verts if v.select]
    return verts


def select(name):
    """
    Select the Object and the object only by name in:
        3D view, context
    :param name: name of object (as in context)
    :return: the bpy data objects
    """
    try:
        obj = bpy.data.objects[name]
        bpy.context.scene.objects.active = obj
        for item in bpy.context.copy()['selected_editable_objects']:
            item.select = False
        obj.select = True
        return obj
    except Exception as e:
        return None


def get_scene():
    """
    API to get the Current Scene
    :return: Scene
    """

    return bpy.data.scenes['Scene']


def import_obj(file_loc, name):
    """
    Import .obj file
    :param file_loc:  file_path
    :param name: as name in context
    :return: the imported object
    """
    scene = bpy.context.scene
    scene.objects.active = None
    imported_object = bpy.ops.import_scene.obj(filepath=file_loc)
    bpy.context.selected_objects[0].name = name
    return select(name)


def to_abs_coord(v, mat):
    """
    Change the local vertices coordinate to absolute coordinate
    :param v:  vector or a list of vertices
    :param mat: matrix_world
    :return: the Absolute vertices
    """
    if isinstance(v, Iterable):
        list_verts = []
        for i in v:
            list_verts.append(mat * i)
        return type(v)(list_verts)
    else:
        return mat * v


def object_mode(obj):
    """
    Select the object and change to object mode
    :param obj: string, name of object
    :return: bpy data object
    """
    bpy.ops.object.mode_set(mode='OBJECT')
    o = select(obj)
    bpy.ops.object.mode_set(mode='OBJECT')
    return o


def edit_mode(obj):
    """
    Select the object and change to edit mode
    :param obj: string, name of object
    :return: bpy data object
    """
    bpy.ops.object.mode_set(mode='EDIT')
    o = select(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='EDIT')
    return o


"""
Transform
"""


def scale_x(ratio):
    bpy.ops.transform.resize(value=(ratio, 1, 1), constraint_axis=(True, False, False), constraint_orientation='GLOBAL',
                             mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                             proportional_size=1)


def scale(ratio_x, ratio_y=None, ratio_z=None):
    if ratio_y is None:
        ratio_y = ratio_x
    if ratio_z is None:
        ratio_z = ratio_x
    bpy.ops.transform.resize(value=(ratio_x, ratio_y, ratio_z), constraint_axis=(True, True, True),
                             constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                             proportional_edit_falloff='SMOOTH', proportional_size=1)


def move(x, y, z):
    bpy.ops.transform.translate(value=(x, y, z), constraint_axis=(False, False, False), constraint_orientation='GLOBAL',
                                mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                                proportional_size=1)


def rotate(deg, axis):
    a = [0, 0, 0]
    a[axis] = 1
    bpy.ops.transform.rotate(value=radians(deg), axis=a,
                             constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False,
                             proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    return


"""
Face
"""


def modify_face():
    object_mode('Face')
    # bpy.context.space_data.context = 'MODIFIER'
    bpy.ops.object.modifier_add(type='DECIMATE')
    bpy.context.object.modifiers["Decimate"].ratio = 0.3
    object_mode('Face')
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")
    bpy.ops.object.modifier_add(type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].iterations = 2
    bpy.context.object.modifiers["Smooth"].factor = 1.51
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")
    bpy.ops.object.shade_smooth()
    return


"""
Head
"""


def apply_head_sub():
    object_mode('Head')
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subsurf")
    return


def get_upper_head_abs(matrix_world):
    # matrix_world = head.matrix_world
    Y_REF = 987
    Z_REF = 987
    Z_REF2 = 940
    head = select('Head')
    bm = bmesh.new()
    bm.from_object(head, get_scene())
    bmv = list(bm.verts)
    vertlist = to_abs_coord([v.co.copy() for v in bmv], matrix_world)
    ref_point_z = to_abs_coord(bmv[Z_REF].co, matrix_world)  #
    ref_point_y = to_abs_coord(bmv[Y_REF].co, matrix_world)  # bmv[17869]
    ref_point_z2 = to_abs_coord(bmv[Z_REF2].co, matrix_world)  #

    upperHead = list(filter(lambda v: v.z >= ref_point_z.z and v.y >= ref_point_y.y, vertlist)).copy()
    return upperHead


def get_face_head_vert():
    face = select('Face')
    fbm = bmesh.new()
    fbm.from_object(face, get_scene())
    fbmv = fbm.verts
    fbmvl = list(fbmv)
    fbmvl = sorted(fbmvl, key=lambda v: (v.co.x, v.co.y, v.co.z))

    head = select('Head')
    hbm = bmesh.new()
    hbm.from_object(head, get_scene())
    hbmv = hbm.verts
    hbmvl = list(hbmv)
    hbmvl = sorted(hbmvl, key=lambda v: (v.co.x, v.co.y, v.co.z))

    f1, f2, h1, h2 = fbmvl[0].co.copy(), fbmvl[-1].co.copy(), hbmvl[0].co.copy(), hbmvl[-1].co.copy()
    fbm.free()
    hbm.free()

    return (f1, f2, h1, h2), (face.matrix_world, head.matrix_world)


def head_uv(file):
    # uv_unwrap
    # edit_mode('Head')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.uv.cylinder_project()
    select('Head')
    # create uv map
    if bpy.data.images.get('uv_map') is not None:
        bpy.data.images.remove(bpy.data.images['uv_map'])
    bpy.context.scene.objects.active = bpy.data.objects['Head']
    bpy.data.images.load(filepath=os.path.join(os.getcwd(), file))
    bpy.data.images[os.path.split(file)[-1]].name = "uv_map"
    img = bpy.data.images.get('uv_map')
    bpy.context.scene.objects.active = bpy.data.objects['Head']
    # Get material
    mat = bpy.data.materials.get("Material")
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Material")
    # Assign it to object
    if bpy.data.objects['Head'].data.materials:
        # assign to 1st material slot
        bpy.data.objects['Head'].data.materials[0] = mat
    else:
        # no slots
        bpy.data.objects['Head'].data.materials.append(mat)
    mat.use_nodes = True
    # bpy.ops.cycles.use_shading_nodes()
    matnodes = mat.node_tree.nodes
    texture = matnodes.new("ShaderNodeTexImage")
    texture.image = img
    disp = matnodes['Diffuse BSDF'].inputs[0]
    mat.node_tree.links.new(disp, texture.outputs[0])
    return


"""
Hair
"""


def decode_as_int(b):
    return struct.unpack("<L", b)[0]


def decode_as_3f(b):
    return [struct.unpack("<f", b[0:4])[0], struct.unpack("<f", b[4:8])[0], struct.unpack("<f", b[8:12])[0]]


def read_data(file_name):
    with open(file_name, 'rb') as f:
        num_strand = decode_as_int(f.read(4))
        strands = []
        for i in range(num_strand):
            num_vertices = decode_as_int(f.read(4))
            v = []
            for j in range(num_vertices):
                v.append(decode_as_3f(f.read(12)))
            if len(v) > 1:
                strands.append(v)
    return np.array(strands)


def gen_strand(S):
    mesh = bpy.data.meshes.new("mesh")
    obj = bpy.data.objects.new("Hair", mesh)
    # obj.parent = bpy.data.objects['Hair']
    # obj = bpy.data.objects['Hair']
    scene = bpy.context.scene
    scene.objects.link(obj)
    scene.objects.active = obj
    obj.select = True
    mesh = bpy.context.object.data
    bm = bmesh.new()
    for ns, verts in enumerate(S):
        bvp0 = None
        bvp1 = None
        for nv, v in enumerate(verts):
            bv = bm.verts.new(v)
            bv.index = ns * 100 + nv
            # bv1 = bm.verts.new(v)
            # bv.index = nv + ns * 100
            if bvp1 is not None:
                bf = bm.faces.new([bv, bvp0, bvp1])
                bf.index = nv + ns * 100
            bvp1 = bvp0
            bvp0 = bv
    bm.to_mesh(mesh)
    bm.free()


#
# def gen_strands(S):
#     for ns, s in enumerate(S):
#         gen_strand(s, ns)


def gen_hair(file_name):
    if os.path.exists(file_name):
        S = read_data(file_name)
        gen_strand(S)
        select('Hair')
        rotate(90, 0)
    else:
        raise Exception("file not found")
    return


def import_test_head(file_loc=None):
    scene = bpy.context.scene
    scene.objects.active = None
    if file_loc is None:
        file_loc = OBJ_HEAD_MODEL_HAIR
    imported_object = bpy.ops.import_scene.obj(filepath=file_loc)
    bpy.context.selected_objects[0].name = "Head"
    bpy.ops.transform.rotate(value=-1.5708, axis=(1, 0, 0), constraint_axis=(True, False, False),
                             constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                             proportional_edit_falloff='SMOOTH', proportional_size=1)
    return


def get_hair_root_abs(matrix_world):
    hair = select('Hair')
    bm = bmesh.new()
    bm.from_object(hair, get_scene())
    vl = list(bm.verts)
    roots = [v.co.copy() for v in vl if v.index % 100 == 0]
    roots = to_abs_coord(roots, matrix_world)
    return roots


"""
Integration
"""

"""
HEAD MASK

"""


class HeadMask_Align:
    def __init__(self, face_count=43866):
        self.FACE_COUNT = face_count

    def edge_fit(self, face, head, mesh, fore_ind, jaw_ind, ind_bound, kpt_ind):
        # fit forehead
        # mask forehead edge between indices [0,480]
        face_top_ind = [i for i in ind_bound if i < 480]  # get indices of forehead on mask
        face_top = face[face_top_ind]  # then obtian their coordinates, middle is no. 13

        neighbour_top = []  # index of nearneibour of forehead on top side of the mask

        for i in fore_ind:
            temp = head[i - self.FACE_COUNT]  # get one point on fore head (head)
            # get distance from each fore head vertex to mask boundary
            dist = np.square(face_top[:, 0] - temp[0]) + np.square(face_top[:, 1] - temp[1]) + np.square(
                face_top[:, 2] - temp[2])
            neighbour_top.append(face_top_ind[int(np.argmin(dist))])  # store index
        neigh = face[neighbour_top]  # obtain coordinate
        fore = head[fore_ind - self.FACE_COUNT]
        # top_y = np.mean(neigh[:,1],axis = 0) - np.mean(fore[:,1],axis = 0)
        top_z = np.mean(neigh[:, 2], axis=0) - np.mean(fore[:, 2], axis=0)

        face[:, 2] -= top_z  # align faace using forehead (working)
        mesh = self.update_mesh(face, head, mesh)
        # ! alignment done

        neigh = face[neighbour_top]
        top_y = neigh[12, 1] - head[fore_ind[12] - self.FACE_COUNT, 1]
        # top_z = neigh[12,2] - head[fore_ind[12] - self.FACE_COUNT,2]

        bpy.ops.mesh.select_all(action='DESELECT')
        self.sel_vert(fore_ind, mesh)
        bpy.ops.transform.translate(value=(0, 0, top_y), constraint_axis=(False, False, False),
                                    constraint_orientation='GLOBAL', mirror=False, proportional='CONNECTED',
                                    proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.mesh.select_all(action='DESELECT')
        # ! jaw part

        # jaw_ind = np.loadtxt(os.path.join(DIR_KPTS, 'jaw.txt').astype(np.int32)
        # bpy.ops.mesh.select_all(action='DESELECT')
        self.sel_vert(jaw_ind, mesh)
        jaw = head[jaw_ind - self.FACE_COUNT]
        temp2 = face[kpt_ind[8]]

        bottom_y = temp2[1] - np.mean(jaw[:, 1], axis=0)
        bottom_z = temp2[2] - np.mean(jaw[:, 2], axis=0)
        bpy.ops.transform.translate(value=(0, -bottom_y, -bottom_z), constraint_axis=(False, False, False),
                                    constraint_orientation='GLOBAL', mirror=False, proportional='CONNECTED',
                                    proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.mesh.select_all(action='DESELECT')

        return mesh

    def get_kpts(self):
        # ! load the vertex index correspond to facial landmarks
        # procedure refer to get_kpt_ind.py
        # global kpt_ind, left_ind, fore_ind, jaw_ind, ind_bound, neck_ind
        # DIR_KPTS = '.\\Data\\geometry'
        # DIR_KPTS = 'C:\\Users\\KTL\\Desktop\\FYP-code\\Data\\geometry'
        ind_bound = np.loadtxt(os.path.join(DIR_KPTS, 'bound.txt')).astype(np.int32)
        kpt_ind = np.loadtxt(os.path.join(DIR_KPTS, 'kpt_ind.txt')).astype(np.int32)  # ntri x 3
        left_ind = np.loadtxt(os.path.join(DIR_KPTS, 'left.txt')).astype(np.int32)
        fore_ind = np.loadtxt(os.path.join(DIR_KPTS, 'fore.txt')).astype(np.int32)
        jaw_ind = np.loadtxt(os.path.join(DIR_KPTS, 'jaw.txt')).astype(np.int32)
        ear_ind = np.loadtxt(os.path.join(DIR_KPTS, 'ear.txt')).astype(np.int32)

        left_ind += self.FACE_COUNT
        fore_ind += self.FACE_COUNT
        jaw_ind += self.FACE_COUNT

        return kpt_ind, left_ind, fore_ind, jaw_ind, ind_bound, ear_ind

    def get_scale(self, face, head):
        P1_REF = 4545 + self.FACE_COUNT  # 45450#52447
        P2_REF = 361 + self.FACE_COUNT  # 36100#44683
        P21_REF = 28003
        P22_REF = 27792
        p1 = head[P1_REF - self.FACE_COUNT]
        p2 = head[P2_REF - self.FACE_COUNT]
        dis1 = abs(p1[0] - p2[0])
        p21 = face[P21_REF]
        p22 = face[P22_REF]
        dis2 = abs(p21[0] - p22[0])
        scal = dis2 / dis1
        return scal

    def get_pos(self, face, head, left_ind, kpt_ind, jaw_ind):
        x = 0
        left = head[left_ind - self.FACE_COUNT]
        left_kpt = face[kpt_ind[14:17]]
        y = head[jaw_ind[8] - self.FACE_COUNT, 1] - face[kpt_ind[8], 1]
        z = np.mean(left[:, 2], axis=0) - np.mean(left_kpt[:, 2], axis=0)
        return x, y, z

    def get_meshes(self):
        """
        get
            the mesrged object,
            meshes of obejct
            Face vertices
            Head vertices
        :return: ob, mesh,f ace, head
        """
        # global ob, mesh, face, head
        ob = bpy.data.objects['Object']
        bpy.context.scene.objects.active = ob  # ! required to select correct context
        # bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(ob.data)
        mesh.verts.ensure_lookup_table()
        bpy.ops.mesh.select_all(action='DESELECT')
        coord = [x.co for x in mesh.verts]
        face = np.array(coord[:self.FACE_COUNT])  # coordinates of face
        head = np.array(coord[self.FACE_COUNT:])  # coordinates of face
        return ob, mesh, face, head

    def update_mesh(self, face_new, head_new, mesh):
        """
        WARNING: FACE_COUNT may vary
        :param face_new:
        :param head_new:
        :param mesh:
        :return:
        """
        for i in range(self.FACE_COUNT):
            mesh.verts[i].co = face_new[i, :]
        #
        # for ii in range(self.FACE_COUNT, 59393):
        #     mesh.verts[i].co = face_new[i, :]
        return mesh

    def import_face(self, file_loc):
        import_obj(file_loc, 'Object')
        bpy.context.scene.objects.active = None

    def face_join(self):
        """
        Join the objects into one mesh
        :return:
        """
        scene = bpy.context.scene
        obs = []
        for ob in scene.objects:
            # whatever objects you want to join...
            if ob.type == 'MESH':
                obs.append(ob)
        ctx = bpy.context.copy()
        # one of the objects to join
        ctx['active_object'] = obs[0]
        ctx['selected_objects'] = obs
        # we need the scene bases as well for joining
        ctx['selected_editable_bases'] = [scene.object_bases[ob.name] for ob in obs]
        bpy.ops.object.join(ctx)

    def sel_vert(self, ind, mesh):
        ob = bpy.data.objects['Object']
        bpy.context.scene.objects.active = ob  # select desired object first
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        mesh.verts.ensure_lookup_table()

        for i in ind:
            mesh.verts[i].select = True

        # bpy.context.scene.objects.active = ob # refresh the scene

    def align_face(self, MASK_DATA):
        """
        GET data from files
        """
        kpt_ind, left_ind, fore_ind, jaw_ind, ind_bound, ear_ind = self.get_kpts()
        object_mode('Head')
        import_obj(os.path.join(DIR_MASK, MASK_DATA), 'Object')
        bpy.context.scene.objects.active = None
        """
        Merge
        """
        self.face_join()
        ob, mesh, face, head = self.get_meshes()

        """
        Scale face
        """
        scal = self.get_scale(face, head)
        face = face / scal
        """
        Translate face
        """
        transx, transy, transz = self.get_pos(face, head, left_ind, kpt_ind, jaw_ind)
        face[:, 0] += 0
        face[:, 1] += transy
        face[:, 2] += transz
        mesh = self.update_mesh(face, head, mesh)

        """
        EDGE_FIT
        """
        self.edge_fit(face, head, mesh, fore_ind, jaw_ind, ind_bound, kpt_ind)

        bpy.ops.mesh.select_all(action='DESELECT')
        self.sel_vert(ear_ind, mesh)
        bpy.ops.mesh.delete(type='VERT')
        # sel_vert(ear_ind, mesh)
        # bpy.ops.mesh.delete(type='VERT')

        bpy.ops.mesh.separate(type='MATERIAL')

        bpy.data.objects['Object'].name = 'Head'
        bpy.data.meshes[INPUT_DATA[:-4]].name = 'Head-mesh'
        bpy.data.objects['Object.001'].name = 'Face'
        bpy.data.meshes['{}.001'.format(INPUT_DATA[:-4])].name = 'Face-mesh'
        return

    def make_face(self):
        edit_mode('Head')

        verts = [592, 593, 594, 608, 610, 1545, 1546, 1547, 1556, 1558, 1563, 1564, 1570, 4771, 4772, 4775, 4778, 5691,
                 5692, 5700, 5701, 5711, 5712, 5715, 8428, 8429, 8431, 8433, 8435, 8436, 8438, 8440, 8442, 8444, 8446,
                 8448, 8450, 8451, 8453, 8455, 8456, 8457, 8458, 8460, 8462, 8463, 8464, 8466, 8468, 8470, 8471, 8473,
                 8474, 8475, 8476, 8478, 8480, 8481, 8482, 8484, 8486, 8487, 8488, 8490, 8492, 8494, 8495, 8497, 8498,
                 8499, 8500, 8502, 8503, 8504, 8505, 8507, 8509, 8510, 8511, 8513, 8514, 8516, 8517, 8519, 8520, 8521,
                 8522, 8524, 8525, 8526, 8527, 8529, 8530, 8532, 8533, 8535, 8536, 8538, 8539, 8541, 8542, 8544, 8545,
                 8547, 8548, 8549, 8550, 8552, 8553, 8555, 8556, 8558, 8559, 8561, 8562, 8564, 8565, 8566, 8567, 8569,
                 8570, 8571, 8572, 8574, 8575, 8576, 8577, 8579, 8580, 8581, 8582, 8584, 8585, 8586, 8587, 8589, 8590,
                 8591, 8593, 8594, 8596, 8597, 8599, 8600, 8602, 8603, 8604, 8606, 8608, 8609, 8611, 8612, 8614, 8615,
                 8616, 8617, 8618, 8620, 8621, 8622, 8623, 8625, 8626, 8628, 8629, 8632, 8633, 8634, 8636, 8638, 8639,
                 8640, 8642, 8643, 8644, 8645, 8647, 8648, 8650, 8651, 8653, 8654, 8656, 8657, 8659, 8660, 8662, 8664,
                 8665, 8666, 8667]
        obj = bpy.context.object
        bm = bmesh.from_edit_mesh(obj.data)
        ob = bpy.data.objects['Head']
        bpy.context.scene.objects.active = ob  # select desired object first
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bm.verts.ensure_lookup_table()
        for i in verts:
            bm.verts[i].select = True
        bpy.ops.mesh.edge_face_add()
        return


def align_head_hair():
    hair = select('Hair')
    head = select('Head')
    root = get_hair_root_abs(hair.matrix_world)
    upper = get_upper_head_abs(head.matrix_world)
    root_x = sorted(root, key=lambda v: (v.x, v.y, v.z))
    upper_x = sorted(upper, key=lambda v: (v.x, v.y, v.z))
    root_y = sorted(root, key=lambda v: (v.y, v.x, v.z))
    upper_y = sorted(upper, key=lambda v: (v.y, v.x, v.z))

    # head / hair
    n1, n2 = upper_x[0], upper_x[-1]
    d1, d2 = root_x[0], root_x[-1]
    n3, n4 = upper_y[0], upper_y[-1]
    d3, d4 = root_y[0], root_y[-1]

    ratio_x = (n2.x - n1.x) / (d2.x - d1.x)
    ratio_y = (n4.y - n3.y) / (d4.y - d3.y)
    select('Hair')
    scale(ratio_x, ratio_y, ratio_x)

    hair = select('Hair')
    head = select('Head')
    root = get_hair_root_abs(hair.matrix_world)
    upper = get_upper_head_abs(head.matrix_world)
    # root = to_abs_coord(root, hair.matrix_world)
    # upper = to_abs_coord(upper, head.matrix_world)
    root_x = sorted(root, key=lambda v: (v.x, v.y, v.z))
    upper_x = sorted(upper, key=lambda v: (v.x, v.y, v.z))
    root_y = sorted(root, key=lambda v: (v.y, v.x, v.z))
    upper_y = sorted(upper, key=lambda v: (v.y, v.x, v.z))

    n1, n2 = upper_x[0], upper_x[-1]
    d1, d2 = root_x[0], root_x[-1]
    n3, n4 = upper_y[0], upper_y[-1]
    d3, d4 = root_y[0], root_y[-1]
    diff = ((n1 - d1) + (n2 - d2) + (n3 - d3) + (n4 - d4)) / 4
    object_mode('Hair')
    move(*list(diff))
    scale(1, 1.05, 1)
    move(0, 0.15, -0.13)
    return


def modify_hair():
    # select('Hair')
    edit_mode('Hair')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.remove_doubles()
    object_mode('Hair')

    # bpy.ops.object.modifier_add(type='DECIMATE')
    # bpy.context.object.modifiers["Decimate"].ratio = 0.6
    # bpy.context.object.modifiers["Decimate"].use_collapse_triangulate = True
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness_clamp = 1
    bpy.context.object.modifiers["Solidify"].offset = 0
    bpy.context.object.modifiers["Solidify"].thickness = 0.001  # 0.001-0.003
    bpy.context.object.modifiers["Solidify"].use_rim = True
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Solidify")

    # bpy.ops.object.modifier_add(type='DECIMATE')
    # bpy.context.object.modifiers["Decimate"].ratio = 0.5
    # bpy.context.object.modifiers["Decimate"].use_collapse_triangulate = True
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

    # bpy.ops.object.modifier_add(type='SOLIDIFY')
    # bpy.context.object.modifiers["Solidify"].thickness_clamp = 1
    # bpy.context.object.modifiers["Solidify"].offset = 0
    # bpy.context.object.modifiers["Solidify"].thickness = 0.0005  # 0.001-0.003
    # bpy.context.object.modifiers["Solidify"].use_rim = True
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Solidify")



    return


def color_hair(COLOR):
    select('Hair')
    bpy.context.scene.objects.active = bpy.data.objects['Hair']
    # Get material
    mat = bpy.data.materials.get("Material-hair")
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name="Material-hair")

    # Assign it to object
    if bpy.data.objects['Hair'].data.materials:
        # assign to 1st material slot
        bpy.data.objects['Hair'].data.materials[0] = mat
    else:
        # no slots
        bpy.data.objects['Hair'].data.materials.append(mat)
    # no node

    mat.use_nodes = False
    bpy.data.objects['Hair'].active_material.diffuse_color = COLOR

    #
    # mat.use_nodes = True
    # # bpy.ops.cycles.use_shading_nodes()
    # matnodes = mat.node_tree.nodes
    # matnodes.remove(matnodes['Diffuse BSDF'])
    #
    # texture = matnodes.new("ShaderNodeBsdfHair")
    # matnodes["Hair BSDF"].inputs[0].default_value = (0, 0, 0, 1)
    # mat.node_tree.links.new(matnodes["Material Output"].inputs[0], texture.outputs[0])
    # mat.node_tree.links.new(matnodes["Material Output"].inputs[1], texture.outputs[0])
    # mat.node_tree.links.new(matnodes["Material Output"].inputs[2], texture.outputs[0])
    return


def remove_hair():
    hair = select('Hair')
    if hair is not None:
        bpy.ops.object.delete()
    return


def import_hair(file):
    if os.path.exists(file):
        if select('Hair') is None:
            gen_hair(file)
            select('Hair')
            object_mode('Head')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    else:
        raise Exception('File not found')


def output(file_name):
    bpy.ops.export_scene.obj(filepath=file_name, check_existing=False, keep_vertex_order=True, global_scale=1)


if __name__ == '__main__':
    print("WS: ", os.getcwd())
    with open('.\config.ini', 'r') as json_file:
        json_data = json.load(json_file)
        OBJ_HEAD_MODEL_HAIR = json_data["OBJ_HEAD_MODEL_HAIR"]
        DIR_INPUT = json_data["DIR_INPUT"]
        DIR_TEXTURE = json_data["DIR_TEXTURE"]
        DIR_HAIR = json_data["DIR_HAIR"]
        DIR_MASK = json_data["DIR_MASK"]
        DIR_OUT = json_data["DIR_OUT"]
        DIR_KPTS = json_data["DIR_KPTS"]
        INPUT_DATA = json_data["INPUT_DATA"]
        TEXTURE_DATA = json_data["TEXTURE_DATA"]
        HAIR_DATA = json_data["HAIR_DATA"]
        MASK_DATA = json_data["MASK_DATA"]
        OUT_DATA = json_data["OUT_DATA"]
        HAIR = json_data["HAIR"]
        HAIR_COLOR = json_data.get('HAIR_COLOR', (0, 0, 0))
        del json_data

    HAIR_COLOR = (HAIR_COLOR[0] / 255, HAIR_COLOR[1] / 255, HAIR_COLOR[2] / 255)
    """
    Face
    """
    align = HeadMask_Align()
    align.align_face(MASK_DATA)
    modify_face()

    """
    Head
    """
    if bpy.data.images.get('uv_map') is None:
        head_uv(os.path.join(DIR_TEXTURE, TEXTURE_DATA))
        object_mode('Head')

    # hair
    if HAIR and select('Hair') is None:
        remove_hair()
        import_hair(os.path.join(DIR_HAIR, HAIR_DATA))
        align_head_hair()
        modify_hair()
        color_hair(HAIR_COLOR)
        object_mode('Hair')

    # join

    bpy.context.scene.objects.active = bpy.data.objects['Head']
    for item in bpy.context.copy()['selected_editable_objects']:
        item.select = False
    bpy.data.objects['Head'].select = True
    bpy.data.objects['Face'].select = True
    # if HAIR:
    # bpy.data.objects['Hair'].select = True
    bpy.ops.object.join()
    # align.make_face()

    # change viewpoint
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    space = next(space for space in area.spaces if space.type == 'VIEW_3D')
    space.viewport_shade = 'TEXTURED'  # set the viewport shading

    # output(os.path.join(DIR_OUT, OUT_DATA))
    for item in bpy.context.copy()['selected_editable_objects']:
        item.select = False
