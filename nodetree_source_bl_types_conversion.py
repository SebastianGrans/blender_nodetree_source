# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/blender_nodetree_source

# Blender types conversion
# Blender types with prefix BL

import sys
from mathutils import Vector, Color
import re


class BlTypesConversion:

    @staticmethod
    def source_by_type(item, value, parent_expr='', deep=0):
        # value as string by type
        if isinstance(value, Vector):
            return BLVector.to_source(value=value, parent_expr=parent_expr, deep=deep)
        elif isinstance(value, Color):
            return BLColor.to_source(value=value, parent_expr=parent_expr, deep=deep)
        elif isinstance(value, (int, float, bool, set)):
            return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + str(value)
        elif isinstance(value, str):
            value_escaped = value.translate(str.maketrans({'\'': r'\'', '\\': r'\\'}))  # escape some characters (', \)
            return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + '\'' + value_escaped + '\''
        elif hasattr(sys.modules[__name__], 'BL' + value.__class__.__name__):
            value_class = getattr(sys.modules[__name__], 'BL' + value.__class__.__name__)
            return value_class.to_source(value=value, parent_expr=parent_expr, deep=deep)
        else:
            print('ERR: Undefined type: item = ', item,
                  'value = ', value, ' (', type(value), ')',
                  'item_class = ', item.__class__.__name__,
                  'value_class = ', value.__class__.__name__,
                  'parent_expr = ', parent_expr
                  )
            return None

    @staticmethod
    def source_from_complex_type(value, excluded_attributes: list = None, preordered_attributes: list = None, complex_attributes: list = None, parent_expr='', deep=0):
        # excluded attributes - don't process them (ex: type, select)
        excluded_attributes = excluded_attributes if excluded_attributes is not None else []
        # preordered attributes - need to be processed first because when changed - change another attributes (ex: mode)
        preordered_attributes = preordered_attributes if preordered_attributes is not None else []
        preordered_attributes = [
            attr for attr in preordered_attributes if
            hasattr(value, attr)
            and getattr(value, attr) is not None  # don't add attributes == None
            and not (isinstance(getattr(value, attr), str) and not getattr(value, attr))  # don't add attributes == '' (empty string)
            and (not value.is_property_readonly(attr) or attr in complex_attributes)
        ]
        # complex attributes - can be readonly but must be processed inside themselves  (ex: mapping)
        complex_attributes = complex_attributes if complex_attributes is not None else []
        attributes = [
            attr for attr in dir(value) if
            hasattr(value, attr)
            and not attr.startswith('__')
            and (not attr.startswith('bl_') or attr == 'bl_idname')
            and attr not in excluded_attributes
            and attr not in preordered_attributes  # don't add preorderd attributes, added first manually
            and not callable(getattr(value, attr))
            and getattr(value, attr) is not None    # don't add attributes == None
            and not (isinstance(getattr(value, attr), str) and not getattr(value, attr))  # don't add attributes == '' (empty string)
            and (not value.is_property_readonly(attr) or attr in complex_attributes)
        ]
        source = ''
        # first - preordered attributes, next - all other attributes
        all_attributes = preordered_attributes + attributes
        for attribute in all_attributes:
            source_cond = ('    ' * deep) + 'if hasattr(' + parent_expr + ', \'' + attribute + '\'):' + '\n'
            source_expr = BlTypesConversion.source_by_type(
                item=attribute,
                value=getattr(value, attribute),
                parent_expr=parent_expr + '.' + attribute,
                deep=deep + 1
            )
            if source_expr is not None:
                source += source_cond + source_expr + ('' if source_expr[-1:] == '\n' else '\n')
        return source


class TupleType:
    # common class for tuple-type types

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + str(tuple(value))


class BLColor(TupleType):
    pass


class BLVector(TupleType):
    pass


class BLMatrix():

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ''
        for i in range(len(value)):
            source += (', ' if source else '') + str(tuple(value.row[i]))
        source = '(' + source + ')'
        return ('    ' * deep) + parent_expr + ' = ' + source


class BLbpy_prop_array(TupleType):
    pass


class BLEuler(TupleType):
    # maybe not right convert as tuple, Euler((x=0.0, y=0.0, z=0.0), order='XYZ') converts as (0.0, 0.0, 0.0)
    # at 2.83 - works
    pass


class BLbpy_prop_collection:
    # collection of properties
    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ''
        for item_index, item in enumerate(value):
            source_expr = BlTypesConversion.source_by_type(
                item=item,
                value=value[item_index],
                parent_expr=parent_expr + '[' + str(item_index) + ']',
                deep=deep
            )
            if source_expr is not None:
                source += source_expr
        return source


class BLScene:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.scenes.get(\'' + value.name + '\')'


class BLObject:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.objects.get(\'' + value.name + '\')'


class BLImage:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'if \'' + value.name + '\' not in bpy.data.images:' + '\n'
        source += ('    ' * (deep + 1)) + 'if os.path.exists(os.path.join(external_items_dir, \'' + value.name + '\')):' + '\n'
        source += ('    ' * (deep + 2)) + 'bpy.data.images.load(os.path.join(external_items_dir, \'' + value.name + '\'))' + '\n'
        source += ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.images.get(\'' + value.name + '\')'
        return source


class BLImageTexture:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'image_texture = bpy.data.textures.get(\'' + value.name + '\')' + '\n'
        source += ('    ' * deep) + 'if not image_texture:' + '\n'
        source += ('    ' * (deep + 1)) + 'image_texture = bpy.data.textures.new(name=\'' + value.name + '\', type=\'' + value.type + '\')' + '\n'
        source += BlTypesConversion.source_from_complex_type(
            value=value,
            preordered_attributes=['use_color_ramp'],
            complex_attributes=['color_ramp'],
            parent_expr='image_texture',
            deep=deep + 1
        )
        source += ('    ' * deep) + parent_expr + ' = image_texture' + '\n'
        return source


class BLBlendTexture(BLImageTexture):
    pass


class BLCloudsTexture(BLImageTexture):
    pass


class BLDistortedNoiseTexture(BLImageTexture):
    pass


class BLMagicTexture(BLImageTexture):
    pass


class BLMarbleTexture(BLImageTexture):
    pass


class BLMusgraveTexture(BLImageTexture):
    pass


class BLNoiseTexture(BLImageTexture):
    pass


class BLStucciTexture(BLImageTexture):
    pass


class BLVoronoiTexture(BLImageTexture):
    pass


class BLWoodTexture(BLImageTexture):
    pass


class BLCacheFile:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'if \'' + value.name + '\' not in bpy.data.cache_files:' + '\n'
        source += ('    ' * (deep + 1)) + 'if os.path.exists(os.path.join(external_items_dir, \'' + value.name + '\')):' + '\n'
        source += ('    ' * (deep + 2)) + 'bpy.ops.cachefile.open(os.path.join(external_items_dir, \'' + value.name + '\'))' + '\n'
        source += ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.cache_files.get(\'' + value.name + '\')'
        return source


class BLText:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.texts.get(\'' + value.name + '\')'


class BLParticleSystem:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.context.active_object.particle_systems.get(\'' + value.name + '\')'


class BLShaderNodeTree:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'bpy.data.node_groups.get(\'' + value.name + '\')'


class BLCompositorNodeTree(BLShaderNodeTree):
    pass


class BLImageFormatSettings:

    @classmethod 
    def to_source(cls, value, parent_expr='', deep=0):

        return BlTypesConversion.source_from_complex_type(
            value=value,
            preordered_attributes=['file_format'],
            parent_expr=parent_expr,
            deep=deep
        )

class BLNodeOutputFileSlotFile:
     
    @classmethod 
    def to_source(cls, value, parent_expr='', deep=0):
        idx_match = re.search('\[(\d+)\]', parent_expr)
        idx = idx_match.group(1)
        parent_expr_reduced = parent_expr[:-(len(idx)+2)]
        source = ''
        if idx_match and int(idx) > 0:
            source = ('    ' * deep) + parent_expr_reduced + '.new(\'NodeOutputFileSlotFile\')' + '\n'

        return source + BlTypesConversion.source_from_complex_type(
            value=value,
            complex_attributes=['format'],
            parent_expr=parent_expr,
            deep=deep
        )

class BLNodeOutputFileSlotLayer:
    @classmethod 
    def to_source(cls, value, parent_expr='', deep=0):
        return BlTypesConversion.source_from_complex_type(
            value=value,
            parent_expr=parent_expr,
            deep=deep
        )

class BLNodeFrame:

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return ('    ' * deep) + ((parent_expr + ' = ') if parent_expr else '') + 'node_tree' + str(deep - 1) + '.nodes.get(\'' + value.name + '\')'


class BLCurveMapping:
    # mapping and curves

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        # complex attributes - can be readonly but must be processed inside themselves
        return BlTypesConversion.source_from_complex_type(
            value=value,
            complex_attributes=['curves'],
            parent_expr=parent_expr,
            deep=deep
        )


class BLCurveMap:
    # curve and points

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        return BlTypesConversion.source_from_complex_type(
            value=value,
            complex_attributes=['points'],
            parent_expr=parent_expr,
            deep=deep
        )


class BLCurveMapPoint:
    # point

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'if ' + parent_expr.strip()[-2:][:1] + ' >= len(' + parent_expr.strip()[:-3] + '):' + '\n'
        source += ('    ' * (deep + 1)) + parent_expr.strip()[:-3] + '.new(' + str(value.location.x) + ', ' + str(value.location.y) + ')' + '\n'
        source += BlTypesConversion.source_from_complex_type(
            value=value,
            parent_expr=parent_expr,
            deep=deep
        )
        return source


class BLCurveProfile(BLCurveMap):
    # curve

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'for i in range(' + str(len(value.points) - 2) + '):' + '\n'
        source += ('    ' * (deep + 1)) + parent_expr + '.points.add(x=0.0, y=0.0)' + '\n'
        source += BlTypesConversion.source_from_complex_type(
            value=value,
            complex_attributes=['points'],
            parent_expr=parent_expr,
            deep=deep
        )
        return source


class BLCurveProfilePoint:
    # point

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = BlTypesConversion.source_from_complex_type(
            value=value,
            parent_expr=parent_expr,
            deep=deep
        )
        return source


class BLColorRamp:
    # color ramp

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        # complex attributes - can be readonly but must be processed inside themselves
        return BlTypesConversion.source_from_complex_type(
            value=value,
            complex_attributes=['elements'],
            parent_expr=parent_expr,
            deep=deep
        )


class BLColorRampElement:
    # color ramp element

    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        source = ('    ' * deep) + 'if ' + parent_expr.strip()[-2:][:1] + ' >= len(' + parent_expr.strip()[:-3] + '):' + '\n'
        source += ('    ' * (deep + 1)) + parent_expr.strip()[:-3] + '.new(' + str(value.position) + ')' + '\n'
        source += BlTypesConversion.source_from_complex_type(
            value=value,
            parent_expr=parent_expr,
            deep=deep
        )
        return source


class BLNodeSocket:


    @classmethod
    def to_source(cls, value, parent_expr='', deep=0):
        print("A socket.")
        return BlTypesConversion.source_from_complex_type(
            value=value,
            parent_expr=parent_expr,
            deep=deep
        )


class BLNodeSocketBool(BLNodeSocket):
    pass

class BLNodeSocketCollection(BLNodeSocket):
    pass

class BLNodeSocketColor(BLNodeSocket):
    pass

class BLNodeSocketFloat(BLNodeSocket):
    pass

class BLNodeSocketFloatAngle(BLNodeSocket):
    pass

class BLNodeSocketFloatFactor(BLNodeSocket):
    pass

class BLNodeSocketFloatPercentage(BLNodeSocket):
    pass

class BLNodeSocketFloatTime(BLNodeSocket):
    pass

class BLNodeSocketFloatUnsigned(BLNodeSocket):
    pass

class BLNodeSocketGeometry(BLNodeSocket):
    pass

class BLNodeSocketImage(BLNodeSocket):
    pass

class BLNodeSocketInt(BLNodeSocket):
    pass

class BLNodeSocketIntFactor(BLNodeSocket):
    pass

class BLNodeSocketIntPercentage(BLNodeSocket):
    pass

class BLNodeSocketIntUnsigned(BLNodeSocket):
    pass

class BLNodeSocketObject(BLNodeSocket):
    pass

class BLNodeSocketShader(BLNodeSocket):
    pass

class BLNodeSocketString(BLNodeSocket):
    pass

class BLNodeSocketVector(BLNodeSocket):
    pass

class BLNodeSocketVectorAcceleration(BLNodeSocket):
    pass

class BLNodeSocketVectorDirection(BLNodeSocket):
    pass

class BLNodeSocketVectorEuler(BLNodeSocket):
    pass

class BLNodeSocketVectorTranslation(BLNodeSocket):
    pass

class BLNodeSocketVectorVelocity(BLNodeSocket):
    pass

class BLNodeSocketVectorXYZ(BLNodeSocket):
    pass

class BLNodeSocketVirtual(BLNodeSocket):
    pass
