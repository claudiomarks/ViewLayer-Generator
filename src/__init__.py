import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty
)

bl_info = {
    "name": "ViewLayer Generator",
    "author": "Claudin",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > View Layer Generator",
    "description": "Gera viewlayers a partir de collections e configura passes e AOVs",
    "category": "Render",
}

# Classe para armazenar a seleção de collections
class CollectionItem(PropertyGroup):
    selected: BoolProperty(default=False)

# Propriedades para armazenar configurações
class ViewLayerGeneratorProps(PropertyGroup):
    # Propriedade para filtrar collections
    collection_filter: StringProperty(
        name="Filtro de Collections",
        description="Filtrar collections por nome",
        default=""
    )
    
    # Opções de filtro
    filter_case_sensitive: BoolProperty(
        name="Case Sensitive",
        description="Filtro sensível a maiúsculas/minúsculas",
        default=False
    )
    
    # Propriedades para os passes
    use_z: BoolProperty(name="Z", default=False)
    use_mist: BoolProperty(name="Mist", default=False)
    use_normal: BoolProperty(name="Normal", default=False)
    use_vector: BoolProperty(name="Vector", default=False)
    use_diffuse_direct: BoolProperty(name="Diffuse Direct", default=False)
    use_diffuse_indirect: BoolProperty(name="Diffuse Indirect", default=False)
    use_diffuse_color: BoolProperty(name="Diffuse Color", default=False)
    use_glossy_direct: BoolProperty(name="Glossy Direct", default=False)
    use_glossy_indirect: BoolProperty(name="Glossy Indirect", default=False)
    use_glossy_color: BoolProperty(name="Glossy Color", default=False)
    use_transmission_direct: BoolProperty(name="Transmission Direct", default=False)
    use_transmission_indirect: BoolProperty(name="Transmission Indirect", default=False)
    use_transmission_color: BoolProperty(name="Transmission Color", default=False)
    use_emit: BoolProperty(name="Emit", default=False)
    use_environment: BoolProperty(name="Environment", default=False)
    use_shadow: BoolProperty(name="Shadow", default=False)
    use_ambient_occlusion: BoolProperty(name="Ambient Occlusion", default=False)
    
    # Propriedades para AOVs
    use_cryptomatte: BoolProperty(name="Cryptomatte", default=False)
    use_cryptomatte_accurate: BoolProperty(name="Cryptomatte Accurate", default=False)
    cryptomatte_levels: EnumProperty(
        name="Cryptomatte Levels",
        items=[
            ('2', "2 Levels", ""),
            ('3', "3 Levels", ""),
            ('4', "4 Levels", ""),
            ('5', "5 Levels", ""),
            ('6', "6 Levels", ""),
            ('7', "7 Levels", ""),
            ('8', "8 Levels", ""),
        ],
        default='2'
    )
    
    # Propriedades para verificar AOVs existentes nos materiais
    detect_shader_aovs: BoolProperty(
        name="Detectar AOVs dos Shaders",
        description="Detectar e usar AOVs já configurados nos shaders",
        default=False
    )
    
    # Propriedades para AOVs personalizados
    aov1_name: StringProperty(name="AOV 1 Nome", default="")
    aov1_type: EnumProperty(
        name="AOV 1 Tipo",
        items=[
            ('COLOR', "Color", ""),
            ('VALUE', "Value", ""),
        ],
        default='COLOR'
    )
    
    aov2_name: StringProperty(name="AOV 2 Nome", default="")
    aov2_type: EnumProperty(
        name="AOV 2 Tipo",
        items=[
            ('COLOR', "Color", ""),
            ('VALUE', "Value", ""),
        ],
        default='COLOR'
    )
    
    # Propriedade para o prefixo do nome do viewlayer (opcional)
    viewlayer_prefix: StringProperty(name="Prefixo", default="VL_")


# Operador para alternar a seleção de coleções
class VIEWLAYER_OT_toggle_collection(Operator):
    bl_idname = "viewlayer.toggle_collection"
    bl_label = "Alternar Collection"
    bl_description = "Alternar seleção da collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name: StringProperty()
    
    def execute(self, context):
        scene = context.scene
        if self.collection_name in scene.collection_selection:
            item = scene.collection_selection[self.collection_name]
            item.selected = not item.selected
        return {'FINISHED'}


# Operador para selecionar todas as collections visíveis (após filtro)
class VIEWLAYER_OT_select_all_collections(Operator):
    bl_idname = "viewlayer.select_all_collections"
    bl_label = "Selecionar Todas"
    bl_description = "Selecionar todas as collections visíveis"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Obter coleções filtradas
        filtered_collections = get_filtered_collections(scene, props)
        
        # Selecionar todas as coleções filtradas
        for collection_name in filtered_collections:
            if collection_name in scene.collection_selection:
                scene.collection_selection[collection_name].selected = True
        
        return {'FINISHED'}


# Operador para desselecionar todas as collections
class VIEWLAYER_OT_deselect_all_collections(Operator):
    bl_idname = "viewlayer.deselect_all_collections"
    bl_label = "Desselecionar Todas"
    bl_description = "Desselecionar todas as collections"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Desselecionar todas as coleções
        for item in scene.collection_selection:
            item.selected = False
        
        return {'FINISHED'}


# Operador para detectar AOVs nos shaders
class VIEWLAYER_OT_detect_shader_aovs(Operator):
    bl_idname = "viewlayer.detect_shader_aovs"
    bl_label = "Detectar AOVs nos Shaders"
    bl_description = "Detectar AOVs configurados nos shaders do projeto"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Detectar AOVs existentes nos materiais
        aov_names = set()
        
        # Percorrer todos os materiais
        for material in bpy.data.materials:
            if material.use_nodes:
                # Encontrar nós de saída AOV
                for node in material.node_tree.nodes:
                    if node.type == 'OUTPUT_AOV':
                        aov_name = node.name
                        if aov_name.startswith("AOV "):
                            aov_name = aov_name[4:]  # Remover o prefixo "AOV "
                        aov_names.add(aov_name)
        
        # Exibir informações sobre os AOVs encontrados
        if aov_names:
            self.report({'INFO'}, f"Encontrados {len(aov_names)} AOVs nos materiais: {', '.join(aov_names)}")
        else:
            self.report({'INFO'}, "Nenhum AOV encontrado nos materiais.")
            
        return {'FINISHED'}


# Função auxiliar para filtrar coleções
def get_filtered_collections(scene, props):
    filter_text = props.collection_filter
    case_sensitive = props.filter_case_sensitive
    
    if not filter_text:
        # Se não houver filtro, retornar todas as coleções
        return [item.name for item in scene.collection_selection]
    
    # Aplicar filtro
    if case_sensitive:
        return [item.name for item in scene.collection_selection 
                if filter_text in item.name]
    else:
        filter_text = filter_text.lower()
        return [item.name for item in scene.collection_selection 
                if filter_text in item.name.lower()]


# Operador para criar viewlayers
class VIEWLAYER_OT_generate(Operator):
    bl_idname = "viewlayer.generate"
    bl_label = "Gerar ViewLayers"
    bl_description = "Gerar viewlayers a partir das collections selecionadas"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Verificar se há collections selecionadas
        selected_collections = [item.name for item in scene.collection_selection if item.selected]
        if not selected_collections:
            self.report({'ERROR'}, "Nenhuma collection selecionada!")
            return {'CANCELLED'}
        
        # Detectar AOVs dos shaders se a opção estiver ativada
        detected_aovs = []
        if props.detect_shader_aovs:
            detected_aovs = self.get_shader_aovs()
        
        # Percorrer todas as collections selecionadas
        for collection_name in selected_collections:
            collection = bpy.data.collections.get(collection_name)
            if not collection:
                continue
            
            # Criar novo viewlayer
            viewlayer_name = props.viewlayer_prefix + collection_name
            
            # Verificar se o viewlayer já existe
            if viewlayer_name in context.scene.view_layers:
                # Se existir, podemos atualizar ou pular
                viewlayer = context.scene.view_layers[viewlayer_name]
            else:
                # Criar novo viewlayer
                viewlayer = context.scene.view_layers.new(viewlayer_name)
            
            # Configurar passes
            viewlayer.use_pass_z = props.use_z
            viewlayer.use_pass_mist = props.use_mist
            viewlayer.use_pass_normal = props.use_normal
            viewlayer.use_pass_vector = props.use_vector
            viewlayer.use_pass_diffuse_direct = props.use_diffuse_direct
            viewlayer.use_pass_diffuse_indirect = props.use_diffuse_indirect
            viewlayer.use_pass_diffuse_color = props.use_diffuse_color
            viewlayer.use_pass_glossy_direct = props.use_glossy_direct
            viewlayer.use_pass_glossy_indirect = props.use_glossy_indirect
            viewlayer.use_pass_glossy_color = props.use_glossy_color
            viewlayer.use_pass_transmission_direct = props.use_transmission_direct
            viewlayer.use_pass_transmission_indirect = props.use_transmission_indirect
            viewlayer.use_pass_transmission_color = props.use_transmission_color
            viewlayer.use_pass_emit = props.use_emit
            viewlayer.use_pass_environment = props.use_environment
            viewlayer.use_pass_shadow = props.use_shadow
            viewlayer.use_pass_ambient_occlusion = props.use_ambient_occlusion
            
            # Configurar Cryptomatte (usando as configurações nativas do Blender)
            if hasattr(viewlayer, "use_pass_cryptomatte"):
                viewlayer.use_pass_cryptomatte = props.use_cryptomatte
            
            if hasattr(viewlayer, "use_pass_cryptomatte_accurate"):
                viewlayer.use_pass_cryptomatte_accurate = props.use_cryptomatte_accurate
            
            if hasattr(viewlayer, "pass_cryptomatte_depth"):
                viewlayer.pass_cryptomatte_depth = int(props.cryptomatte_levels)
            
            # Adicionar AOVs personalizados
            self.add_custom_aovs(viewlayer, props, detected_aovs)
            
            # Configurar visibilidade das collections
            self.setup_collection_visibility(viewlayer, collection_name)
        
        self.report({'INFO'}, "ViewLayers gerados com sucesso!")
        return {'FINISHED'}
    
    def get_shader_aovs(self):
        # Detectar AOVs nos shaders dos materiais
        aov_info = []
        
        # Percorrer todos os materiais
        for material in bpy.data.materials:
            if material.use_nodes:
                # Encontrar nós de saída AOV
                for node in material.node_tree.nodes:
                    if node.type == 'OUTPUT_AOV':
                        # Obter nome do AOV
                        aov_name = node.name
                        if aov_name.startswith("AOV "):
                            aov_name = aov_name[4:]  # Remover o prefixo "AOV "
                        
                        # Determinar o tipo de AOV com base nas conexões
                        aov_type = 'COLOR'  # Padrão para color
                        if node.inputs and node.inputs[0].links:
                            socket_type = node.inputs[0].links[0].from_socket.type
                            if socket_type == 'VALUE':
                                aov_type = 'VALUE'
                        
                        # Adicionar à lista, evitando duplicatas
                        if not any(info['name'] == aov_name for info in aov_info):
                            aov_info.append({
                                'name': aov_name,
                                'type': aov_type
                            })
        
        return aov_info
    
    def add_custom_aovs(self, viewlayer, props, detected_aovs):
        # Adicionar AOVs detectados nos shaders
        if props.detect_shader_aovs and detected_aovs:
            for aov_info in detected_aovs:
                self.add_aov(viewlayer, aov_info['name'], aov_info['type'])
        
        # Adicionar AOV personalizado 1 e 2 (se preenchidos)
        if props.aov1_name:
            self.add_aov(viewlayer, props.aov1_name, props.aov1_type)
        
        if props.aov2_name:
            self.add_aov(viewlayer, props.aov2_name, props.aov2_type)
    
    def add_aov(self, viewlayer, name, aov_type):
        # Verificar se o viewlayer tem o atributo 'aovs'
        if not hasattr(viewlayer, "aovs"):
            return
        
        # Verificar se o AOV já existe
        for aov in viewlayer.aovs:
            if aov.name == name:
                aov.type = aov_type
                return
        
        # Adicionar novo AOV
        aov = viewlayer.aovs.add()
        aov.name = name
        aov.type = aov_type
    
    def setup_collection_visibility(self, viewlayer, target_collection_name):
        # Função para configurar a visibilidade da collection no viewlayer
        
        # Função recursiva para encontrar a camada de collection
        def find_layer_collection(layer_coll, collection_name):
            if layer_coll.name == collection_name:
                return layer_coll
            for child in layer_coll.children:
                result = find_layer_collection(child, collection_name)
                if result:
                    return result
            return None
        
        # Começar a partir da camada de collection raiz
        root = viewlayer.layer_collection
        
        # Ocultar todas as collections primeiro
        for child in root.children:
            child.exclude = True
        
        # Encontrar e mostrar a collection alvo
        target = find_layer_collection(root, target_collection_name)
        if target:
            target.exclude = False


# Operador para atualizar a lista de collections
class VIEWLAYER_OT_update_collections(Operator):
    bl_idname = "viewlayer.update_collections"
    bl_label = "Atualizar Collections"
    bl_description = "Atualizar a lista de collections disponíveis"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Limpar a lista de collections
        scene.collection_selection.clear()
        
        # Adicionar todas as collections disponíveis
        for collection in bpy.data.collections:
            if collection.name not in scene.collection_selection:
                item = scene.collection_selection.add()
                item.name = collection.name
                item.selected = False
        
        if len(scene.collection_selection) == 0:
            self.report({'WARNING'}, "Nenhuma collection encontrada!")
        else:
            self.report({'INFO'}, f"{len(scene.collection_selection)} collections encontradas!")
        
        return {'FINISHED'}


# Painel principal
class VIEWLAYER_PT_panel(Panel):
    bl_label = "Gerador de ViewLayers"
    bl_idname = "VIEWLAYER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View Layer Generator'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Botão para atualizar a lista de collections
        layout.operator("viewlayer.update_collections", icon='FILE_REFRESH')
        
        # Filtro de collections
        box = layout.box()
        box.label(text="Filtrar Collections:")
        row = box.row(align=True)
        row.prop(props, "collection_filter", text="")
        row.prop(props, "filter_case_sensitive", text="", icon='SMALLCAPS')
        
        # Botões para selecionar/desselecionar todas
        row = box.row(align=True)
        row.operator("viewlayer.select_all_collections", icon='CHECKBOX_HLT')
        row.operator("viewlayer.deselect_all_collections", icon='CHECKBOX_DEHLT')
        
        # Seção de seleção de collections
        box = layout.box()
        box.label(text="Selecione as Collections:")
        
        if len(scene.collection_selection) == 0:
            box.label(text="Nenhuma collection encontrada.")
            box.label(text="Clique em 'Atualizar Collections'.")
        else:
            # Filtrar collections
            filtered_collections = get_filtered_collections(scene, props)
            
            if filtered_collections:
                for item_name in filtered_collections:
                    item = scene.collection_selection[item_name]
                    row = box.row()
                    icon = 'CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT'
                    row.operator("viewlayer.toggle_collection", 
                                text=item.name, 
                                icon=icon).collection_name = item.name
            else:
                box.label(text="Nenhuma collection corresponde ao filtro.")
        
        # Prefixo para os nomes dos viewlayers
        layout.prop(props, "viewlayer_prefix")
        
        # Botão de geração
        layout.operator("viewlayer.generate", icon='RENDERLAYERS')


# Painel para configuração de passes
class VIEWLAYER_PT_passes(Panel):
    bl_label = "Passes"
    bl_idname = "VIEWLAYER_PT_passes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View Layer Generator'
    bl_parent_id = "VIEWLAYER_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.viewlayer_generator_props
        
        # Adicionar passes em colunas para melhor organização
        col = layout.column(align=True)
        row = col.row()
        row.prop(props, "use_z")
        row.prop(props, "use_mist")
        
        row = col.row()
        row.prop(props, "use_normal")
        row.prop(props, "use_vector")
        
        col.separator()
        col.label(text="Diffuse:")
        row = col.row()
        row.prop(props, "use_diffuse_direct")
        row.prop(props, "use_diffuse_indirect")
        row = col.row()
        row.prop(props, "use_diffuse_color")
        
        col.separator()
        col.label(text="Glossy:")
        row = col.row()
        row.prop(props, "use_glossy_direct")
        row.prop(props, "use_glossy_indirect")
        row = col.row()
        row.prop(props, "use_glossy_color")
        
        col.separator()
        col.label(text="Transmission:")
        row = col.row()
        row.prop(props, "use_transmission_direct")
        row.prop(props, "use_transmission_indirect")
        row = col.row()
        row.prop(props, "use_transmission_color")
        
        col.separator()
        row = col.row()
        row.prop(props, "use_emit")
        row.prop(props, "use_environment")
        
        row = col.row()
        row = col.row()
        row.prop(props, "use_shadow")
        row.prop(props, "use_ambient_occlusion")


# Painel para configuração de AOVs
class VIEWLAYER_PT_aovs(Panel):
    bl_label = "AOVs"
    bl_idname = "VIEWLAYER_PT_aovs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View Layer Generator'
    bl_parent_id = "VIEWLAYER_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.viewlayer_generator_props
        
        # Cryptomatte
        box = layout.box()
        box.label(text="Cryptomatte:")
        box.prop(props, "use_cryptomatte")
        
        # Mostrar opções adicionais apenas se Cryptomatte estiver ativado
        if props.use_cryptomatte:
            box.prop(props, "use_cryptomatte_accurate")
            box.prop(props, "cryptomatte_levels")
        
        # AOVs dos shaders
        box = layout.box()
        row = box.row()
        row.prop(props, "detect_shader_aovs")
        row.operator("viewlayer.detect_shader_aovs", text="", icon='VIEWZOOM')
        
        # AOVs personalizados
        box = layout.box()
        box.label(text="AOVs Personalizados:")
        
        # AOV 1
        row = box.row()
        row.prop(props, "aov1_name")
        row.prop(props, "aov1_type")
        
        # AOV 2
        row = box.row()
        row.prop(props, "aov2_name")
        row.prop(props, "aov2_type")


# Registro de classes
classes = (
    CollectionItem,
    ViewLayerGeneratorProps,
    VIEWLAYER_OT_toggle_collection,
    VIEWLAYER_OT_select_all_collections,
    VIEWLAYER_OT_deselect_all_collections,
    VIEWLAYER_OT_detect_shader_aovs,
    VIEWLAYER_OT_generate,
    VIEWLAYER_OT_update_collections,
    VIEWLAYER_PT_panel,
    VIEWLAYER_PT_passes,
    VIEWLAYER_PT_aovs,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.viewlayer_generator_props = PointerProperty(type=ViewLayerGeneratorProps)
    bpy.types.Scene.collection_selection = CollectionProperty(type=CollectionItem)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.viewlayer_generator_props
    del bpy.types.Scene.collection_selection

if __name__ == "__main__":
    register()
