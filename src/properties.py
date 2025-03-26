import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty


class CollectionItem(PropertyGroup):
    """Item representando uma collection na lista."""
    name: StringProperty()  # Nome da collection
    selected: BoolProperty(default=False)  # Se está selecionada


class PassItem(PropertyGroup):
    """Item representando um passe na lista."""
    name: StringProperty()  # Nome do passe
    selected: BoolProperty(default=False)  # Se está selecionado
    category: StringProperty(default="Data")  # Categoria do passe: "Data", "Light", "Crypto Matte"
    type: StringProperty(default="COLOR")  # Tipo de dado: "COLOR" ou "VALUE" (para AOVs)


class ViewLayerGeneratorProps(PropertyGroup):
    """Propriedades para o gerador de view layers."""
    selected_passes: CollectionProperty(type=PassItem)  # Passes selecionados
    active_pass_index: IntProperty(default=0)  # Índice do passe ativo na UI
    
    # Filtro de categoria
    show_data_passes: BoolProperty(default=True, name="Data") 
    show_light_passes: BoolProperty(default=True, name="Light")
    show_crypto_passes: BoolProperty(default=True, name="Crypto Matte")


# Classes para registro
classes = (
    CollectionItem,
    PassItem,
    ViewLayerGeneratorProps,
)


def register():
    """Registrar as classes de propriedades."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Registrar propriedades
    bpy.types.Scene.viewlayer_generator_props = bpy.props.PointerProperty(type=ViewLayerGeneratorProps)
    bpy.types.Scene.collection_selection = bpy.props.CollectionProperty(type=CollectionItem)
    bpy.types.Scene.active_collection_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.detected_aovs = bpy.props.CollectionProperty(type=CollectionItem)


def unregister():
    """Cancelar registro das classes de propriedades."""
    # Remover propriedades
    del bpy.types.Scene.viewlayer_generator_props
    del bpy.types.Scene.collection_selection
    del bpy.types.Scene.active_collection_index
    del bpy.types.Scene.detected_aovs
    
    # Cancelar registro das classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)