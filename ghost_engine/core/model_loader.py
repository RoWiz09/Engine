from ..mesh_builder import MeshBuilder
from .packer import Pack

class ModelLoader:
    @staticmethod
    def load_obj(file_path: str):
        meshes: list[MeshBuilder.Mesh] = []

        positions = []
        normals = []
        tex_coords = []

        vertices = []
        indices = []

        vertex_map = {}

        pos_offset = 0
        nor_offset = 0
        tex_offset = 0

        lines = []
        pack = Pack()
        lines = pack.get_contents(file_path).splitlines()
        
        mesh_builder = MeshBuilder()
        def add_mesh(vertices, indices):
            mesh_builder.bulk_load(vertices, indices)
            meshes.append(mesh_builder.build_mesh())

        for line in lines:
            if line.startswith("o "):
                if not vertices is []:
                    add_mesh(vertices, indices)

                pos_offset = len(positions)
                nor_offset = len(normals)
                tex_offset = len(tex_coords)

                positions.clear()
                normals.clear()
                tex_coords.clear()

                vertices.clear()
                indices.clear()

                vertex_map.clear()

            elif line.startswith("v "):
                positions.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vn "):
                normals.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("vt "):
                tex_coords.append(tuple(map(float, line.split()[1:3])))

            elif line.startswith("f "):
                face = line.split()[1:]

                # triangulate face (fan method)
                for i in range(1, len(face) - 1):
                    for vert in (face[0], face[i], face[i + 1]):

                        parts = vert.split("/")
                        v = int(parts[0]) - 1 - pos_offset
                        vt = int(parts[1]) - 1 - tex_offset if len(parts) > 1 and parts[1] else None
                        vn = int(parts[2]) - 1 - nor_offset if len(parts) > 2 and parts[2] else None

                        key = (v, vt, vn)
                        if key not in vertex_map:
                            px, py, pz = positions[v]

                            if vt is not None:
                                u, v_ = tex_coords[vt]
                            else:
                                u, v_ = 0.0, 0.0

                            if vn is not None:
                                nx, ny, nz = normals[vn]
                            else:
                                nx, ny, nz = 0.0, 0.0, 0.0

                            vertex_map[key] = len(vertices)
                            vertices.append([
                                px, py, pz,
                                u, v_,
                                nx, ny, nz
                            ])

                        indices.append(vertex_map[key])

        add_mesh(vertices, indices)
        print(meshes)
        return meshes