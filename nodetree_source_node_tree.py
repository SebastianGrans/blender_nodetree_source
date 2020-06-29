# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/blender_nodetree_source

from .nodetree_source_node import Node


class NodeTree:

    @classmethod
    def to_source(cls, owner, node_tree, parent_expr='', deep=0):
        print(node_tree, node_tree.type)
        # get node tree source
        source = ''
        # inputs
        if node_tree.inputs:
            source += ('    ' * deep) + '# INPUTS' + '\n'
            for c_input in owner.inputs:
                # source += ('    ' * deep) + c_input.bl_idname + '\n'  # NodeSocketInterfaceXXX
                source += ('    ' * deep) + parent_expr + str(deep) + '.inputs.new(\'' + c_input.bl_idname + '\', \'' + c_input.name + '\')' + '\n'
        # outputs
        if node_tree.outputs:
            source += ('    ' * deep) + '# OUTPUTS' + '\n'
            for c_output in owner.outputs:
                # source += ('    ' * deep) + c_output.rna_type.identifier + '\n'  # NodeSocketInterfaceXXX
                source += ('    ' * deep) + parent_expr + str(deep) + '.outputs.new(\'' + c_output.bl_idname + '\', \'' + c_output.name + '\')' + '\n'
        # nodes
        if node_tree.nodes:
            source += '    ' * deep + '# NODES' + '\n'
            for node in node_tree.nodes:
                if node.type == 'GROUP':
                    # node group
                    source += ('    ' * deep) + parent_expr + str(deep + 1) + ' = bpy.data.node_groups.get(\'' + node.node_tree.name + '\')' + '\n'
                    source += ('    ' * deep) + 'if not ' + parent_expr + str(deep + 1) + ':' + '\n'
                    source += ('    ' * (deep + 1)) + 'node_tree' + str(deep + 1) + ' = bpy.data.node_groups.new(\'' + node.node_tree.name + '\', \'' + node_tree.bl_idname + '\')' + '\n'
                    source += cls.to_source(owner=node, node_tree=node.node_tree, parent_expr=parent_expr, deep=deep + 1) + '\n'
                    source += Node.to_source(node=node, parent_expr='node_tree' + str(deep), deep=deep) + '\n'
                else:
                    # simple node
                    source += Node.to_source(node=node, parent_expr='node_tree' + str(deep), deep=deep) + '\n'
        # links
        if node_tree.links:
            source += ('    ' * deep) + '# LINKS' + '\n'
            for link in node_tree.links:
                from_node_alias = Node.node_alias(node=link.from_node, deep=deep)
                to_node_alias = Node.node_alias(node=link.to_node, deep=deep)
                source += ('    ' * deep) + parent_expr + str(deep) + '.links.new(' \
                          + from_node_alias + '.outputs[' + str(list(link.from_node.outputs).index(link.from_socket)) + ']' + \
                          ', ' + to_node_alias + '.inputs[' + str(list(link.to_node.inputs).index(link.to_socket)) + ']' + \
                          ')' + '\n'
        return source

    @staticmethod
    def clear_source(parent_expr=''):
        # source for clear node tree
        source = 'for node in ' + parent_expr + '.nodes:' + '\n'
        source += '    ' + parent_expr + '.nodes.remove(node)' + '\n'
        return source

    # @staticmethod
    # def has_node_groups(node_tree):
    #     # return True if node_tree has NodeGroup nodes
    #     return any(node.type == 'GROUP' for node in node_tree.nodes)
    #
    # @classmethod
    # def external_items(cls, node_tree):
    #     # returns external items (textures,... etc) list
    #     rez = []
    #     for node in node_tree.nodes:
    #         if node.type == 'GROUP':
    #             rez.extend(cls.external_items(node_tree=node.node_tree))
    #         elif node.type == 'TEX_IMAGE' and node.image:
    #             rez.append({
    #                 'path': FileManager.abs_path(node.image.filepath),
    #                 'name': node.image.name
    #             })
    #         elif node.type == 'SCRIPT' and node.mode == 'EXTERNAL' and node.filepath:
    #             rez.append({
    #                 'path': FileManager.abs_path(node.filepath)
    #             })
    #     return rez
