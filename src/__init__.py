import bpy
import json
import os
import sys  # Para listar os módulos carregados
from bpy.types import Panel, Operator, UIList
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

# Importar módulos do addon (caminhos atualizados)
from .utils import passes_data
from .properties import CollectionItem, PassItem, ViewLayerGeneratorProps, register as register_properties, unregister as unregister_properties
from .preferences import initialize_default_passes, register_preferences, unregister_preferences

bl_info = {
    "name": "viewlayer_generator",
    "author": "histeria",
    "version": (2, 2, 2),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > View Layer Generator",
    "description": "Gera viewlayers a partir de collections e configura passes e AOVs",
    "category": "Render",
}

# ==========================
# Funções Auxiliares
# ==========================
def get_filtered_collections(scene, filter_text, case_sensitive):
    """Filtrar collections com base no texto fornecido."""
    if not filter_text:
        return [item.name for item in scene.collection_selection]
    filter_text = filter_text if case_sensitive else filter_text.lower()
    return [
        item.name
        for item in scene.collection_selection
        if (filter_text in item.name if case_sensitive else filter_text in item.name.lower())
    ]


def toggle_selection(items, select_all=True):
    """Alternar seleção de uma lista de items."""
    for item in items:
        item.selected = select_all


def detect_material_aovs():
    """Detectar AOVs configurados nos shaders do projeto."""
    aov_info = []
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "OUTPUT_AOV":
                    # Usar o valor do campo name ao invés do nome do nó
                    # O campo name do nó OUTPUT_AOV contém o nome real do AOV
                    aov_name = node.name
                    if hasattr(node, "inputs") and len(node.inputs) > 0:
                        aov_type = "VALUE" if node.inputs[0].links and node.inputs[0].links[0].from_socket.type == "VALUE" else "COLOR"
                        
                        # Verificar se este AOV já foi detectado antes
                        if not any(info["name"] == aov_name for info in aov_info):
                            aov_info.append({"name": aov_name, "type": aov_type})
    return aov_info


def apply_aovs_to_viewlayer(viewlayer, aov_info):
    """Adicionar AOVs a um viewlayer."""
    if not hasattr(viewlayer, "aovs"):
        return
    for aov_data in aov_info:
        existing_aov = next((aov for aov in viewlayer.aovs if aov.name == aov_data["name"]), None)
        if existing_aov:
            existing_aov.type = aov_data["type"]
        else:
            new_aov = viewlayer.aovs.add()
            new_aov.name = aov_data["name"]
            new_aov.type = aov_data["type"]

def is_gp_collection(collection_name):
    """Verificar se uma collection é para Grease Pencil."""
    return collection_name.endswith(".GP") or collection_name.endswith(".GP.vl")

# ==========================
# UIList para Collections
# ==========================
class VIEWLAYER_UL_collections(UIList):
    """Lista de collections para seleção."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "selected", text="")
            row.label(text=item.name, icon="OUTLINER_COLLECTION")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="OUTLINER_COLLECTION")


# ==========================
# UIList para Passes
# ==========================
class VIEWLAYER_UL_passes(UIList):
    """Lista de passes de renderização disponíveis."""
    
    def filter_items(self, context, data, propname):
        passes = getattr(data, propname)
        props = context.scene.viewlayer_generator_props
        
        # Filtrar com base nas categorias selecionadas
        flt_flags = []
        for item in passes:
            # Verificar a categoria do passe e o filtro correspondente
            if (item.category == "Data" and props.show_data_passes) or \
               (item.category == "Light" and props.show_light_passes) or \
               (item.category == "Crypto Matte" and props.show_crypto_passes) or \
               (item.category == "Other"):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)
                
        # Agrupar por categoria
        flt_neworder = []
        
        return flt_flags, flt_neworder
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "selected", text="")
            
            # Usar a função auxiliar para obter o nome amigável
            display_name = passes_data.get_friendly_name(item.name)
                
            row.label(text=display_name, icon="NODE_MATERIAL")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="NODE_MATERIAL")


# UIList para AOVs
class VIEWLAYER_UL_aovs(UIList):
    """Lista de AOVs detectados no projeto."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "selected", text="")
            row.label(text=item.name, icon="MATERIAL")
            
            # Mostrar o tipo de AOV (COLOR ou VALUE)
            row.label(text=getattr(item, "type", "COLOR"))
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="MATERIAL")


# ==========================
# Operadores
# ==========================
class VIEWLAYER_OT_toggle_selection(Operator):
    """Alternar seleção de items (collections ou AOVs)."""
    bl_idname = "viewlayer.toggle_selection"
    bl_label = "Alternar Seleção"
    bl_options = {"REGISTER", "UNDO"}

    select_all: BoolProperty(default=True)
    target: StringProperty(default="collections")  # "collections" ou "aovs"

    def execute(self, context):
        scene = context.scene
        items = scene.collection_selection if self.target == "collections" else scene.detected_aovs
        toggle_selection(items, self.select_all)
        return {"FINISHED"}


class VIEWLAYER_OT_detect_aovs(Operator):
    """Detectar AOVs nos materiais do projeto."""
    bl_idname = "viewlayer.detect_aovs"
    bl_label = "Detectar AOVs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        scene.detected_aovs.clear()
        aov_info = detect_material_aovs()
        
        if len(aov_info) == 0:
            self.report({"INFO"}, "Nenhum AOV encontrado nos materiais do projeto.")
            return {"FINISHED"}
            
        # Adicionar AOVs encontrados à lista
        for info in aov_info:
            item = scene.detected_aovs.add()
            item.name = info["name"]
            item.type = info["type"]
            item.selected = True  # Por padrão, todos vêm marcados
            
        # Essa linha estava causando o erro - removemos porque a propriedade agora está registrada corretamente
        # scene.active_aov_index = bpy.props.IntProperty(default=0)
            
        self.report({"INFO"}, f"{len(aov_info)} AOVs detectados e listados.")
        return {"FINISHED"}


class VIEWLAYER_OT_generate(Operator):
    """Gerar viewlayers a partir das collections selecionadas."""
    bl_idname = "viewlayer.generate"
    bl_label = "Gerar ViewLayers"
    bl_options = {"REGISTER", "UNDO"}
    
    def get_parent_collection(self, collection_name):
        """Obter a collection pai de uma collection."""
        # Percorrer todas as collections para encontrar a pai da collection atual
        for parent in bpy.data.collections:
            for child in parent.children:
                if child.name == collection_name:
                    return parent.name
        return None

    def process_layer_collection(self, layer_collection, collection_name, lighting_collections, always_active_collections, holdout_collections, holdout_parents, parent_active=False):
        """Processar recursivamente uma layer collection e suas filhas."""
        should_activate = False
        is_holdout = False
        
        # Verificar tratamento especial para viewlayers com sufixo .GP
        is_gp_viewlayer = collection_name.endswith(".GP")
        
        # Verificar se esta collection deve ser ativada
        if parent_active:
            # Se o pai está ativo, esta collection também deve ser ativada (herança hierárquica)
            should_activate = True
        elif layer_collection.name == collection_name:
            # É a collection principal que origina a view layer
            should_activate = True
        elif layer_collection.name in always_active_collections or layer_collection.name.endswith(".all"):
            # É uma collection com sufixo .all
            should_activate = True
        elif layer_collection.name == "lgt.all" and not is_gp_viewlayer:
            # É a collection lgt.all (desativar para GP)
            should_activate = True
        elif layer_collection.name.startswith("lgt."):
            # É uma collection lgt. com especificação
            if is_gp_viewlayer:
                # Para viewlayers GP, nunca ativar collections lgt.*
                should_activate = False
            else:
                # Extrair o prefixo após "lgt."
                lgt_prefix = layer_collection.name.split(".")[1] if "." in layer_collection.name else ""
                
                # Se não tem prefixo específico, ativar em todas as view layers
                if not lgt_prefix:
                    should_activate = True
                # Se tem prefixo específico, verificar se a view layer começa com esse prefixo
                elif collection_name.startswith(lgt_prefix + "."):
                    should_activate = True
        elif layer_collection.name.endswith(".hdt"):
            # É uma collection de holdout
            parent_name = holdout_parents.get(layer_collection.name)
            if parent_name == collection_name:
                # Esta collection .hdt pertence à collection que estamos processando
                should_activate = True
                is_holdout = True
                
        # Verificação especial para collections de holdout
        if layer_collection.name.endswith(".hdt"):
            # Garantir que o holdout seja aplicado independentemente
            is_holdout = True
        
        # Aplicar as configurações
        if should_activate:
            layer_collection.exclude = False
            if is_holdout:
                # Aplicar o holdout de forma explícita
                layer_collection.holdout = True
        else:
            layer_collection.exclude = True
            # Resetar a propriedade holdout quando a collection não está ativa
            layer_collection.holdout = False
            
        # Processar collections filhas recursivamente, passando o status de ativação do pai
        for child in layer_collection.children:
            self.process_layer_collection(
                child, 
                collection_name, 
                lighting_collections, 
                always_active_collections, 
                holdout_collections, 
                holdout_parents, 
                parent_active=should_activate  # Passa se o pai (esta collection) está ativo
            )

    def execute(self, context):
        scene = context.scene
        selected_collections = [item.name for item in scene.collection_selection if item.selected]
        if not selected_collections:
            self.report({"ERROR"}, "Nenhuma collection selecionada!")
            return {"CANCELLED"}

        # Identificar collections lgt. e collections com sufixos .all e .hdt
        lighting_collections = [col.name for col in bpy.data.collections if col.name.startswith("lgt.")]
        always_active_collections = [col.name for col in bpy.data.collections if col.name.endswith(".all")]
        holdout_collections = [col.name for col in bpy.data.collections if col.name.endswith(".hdt")]
        
        # Criar um dicionário que mapeia cada collection .hdt para sua collection pai
        holdout_parents = {}
        for hdt_name in holdout_collections:
            parent_name = self.get_parent_collection(hdt_name)
            if parent_name:
                holdout_parents[hdt_name] = parent_name
        
        # Obter passes selecionados
        passes = [pass_item.name for pass_item in scene.viewlayer_generator_props.selected_passes if pass_item.selected]

        for collection_name in selected_collections:
            # Cria a view layer com o nome da collection
            viewlayer_name = collection_name
            viewlayer = scene.view_layers.get(viewlayer_name) or scene.view_layers.new(viewlayer_name)

            # Configurar visibilidade das collections recursivamente
            self.process_layer_collection(
                viewlayer.layer_collection, 
                collection_name, 
                lighting_collections, 
                always_active_collections, 
                holdout_collections,
                holdout_parents,
                parent_active=False  # Inicia com parent_active=False para a raiz
            )

            # Configurar passes na view layer
            # Tratamento especial para viewlayers com sufixo .GP
            if is_gp_collection(collection_name):
                # Desativar todos os passes primeiro
                for attr in dir(viewlayer):
                    if attr.startswith("use_pass_") and isinstance(getattr(viewlayer, attr), bool):
                        setattr(viewlayer, attr, False)
                
                # Ativar apenas o passe combined
                if hasattr(viewlayer, "use_pass_combined"):
                    setattr(viewlayer, "use_pass_combined", True)
            else:
                # Para outros viewlayers, aplicar passes normalmente
                for pass_name in passes:
                    if hasattr(viewlayer, pass_name):
                        setattr(viewlayer, pass_name, True)

        # Relatório final
        if any(col.endswith(".GP") for col in selected_collections):
            self.report({"INFO"}, f"{len(selected_collections)} ViewLayers gerados (ViewLayers com .GP usam apenas passe combined e sem luzes).")
        else:
            self.report({"INFO"}, f"{len(selected_collections)} ViewLayers gerados com passes: {', '.join(passes)}.")
        
        return {"FINISHED"}


class VIEWLAYER_OT_refresh_collections(Operator):
    """Atualizar a lista de collections disponíveis."""
    bl_idname = "viewlayer.refresh_collections"
    bl_label = "Atualizar Collections"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        existing_selection = {item.name for item in scene.collection_selection if item.selected}
        scene.collection_selection.clear()  # Limpar a lista existente

        # Preencher com as collections do projeto
        for collection in bpy.data.collections:
            item = scene.collection_selection.add()
            # Manter seleção existente ou pré-selecionar collections com sufixo .vl
            item.name = collection.name
            item.selected = collection.name in existing_selection or collection.name.endswith(".vl")

        self.report({"INFO"}, f"{len(scene.collection_selection)} collections carregadas.")
        return {"FINISHED"}


class VIEWLAYER_OT_activate_lighting(Operator):
    """Ativar collections de lighting (lgt)."""
    bl_idname = "viewlayer.activate_lighting"
    bl_label = "Ativar Lighting"
    bl_options = {"REGISTER", "UNDO"}

    collection_name: StringProperty()

    def execute(self, context):
        scene = context.scene
        for item in scene.collection_selection:
            if item.name.startswith("lgt.") and item.name == self.collection_name:
                item.selected = True
        self.report({"INFO"}, f"Lighting ativado para {self.collection_name}.")
        return {"FINISHED"}


class VIEWLAYER_OT_activate_holdout(Operator):
    """Ativar collections de holdout (.hdt)."""
    bl_idname = "viewlayer.activate_holdout"
    bl_label = "Ativar Holdout"
    bl_options = {"REGISTER", "UNDO"}

    collection_name: StringProperty()

    def execute(self, context):
        scene = context.scene
        for item in scene.collection_selection:
            if item.name.endswith(".hdt") and item.name == self.collection_name:
                item.selected = True
        self.report({"INFO"}, f"Holdout ativado para {self.collection_name}.")
        return {"FINISHED"}


class VIEWLAYER_OT_toggle_passes(Operator):
    """Alternar seleção de todos os passes."""
    bl_idname = "viewlayer.toggle_passes"
    bl_label = "Alternar Passes"
    bl_options = {"REGISTER", "UNDO"}

    select_all: BoolProperty(default=True)

    def execute(self, context):
        props = context.scene.viewlayer_generator_props
        for pass_item in props.selected_passes:
            pass_item.selected = self.select_all
        return {"FINISHED"}


# ==========================
# Operador para Refresh de Passes
# ==========================
class VIEWLAYER_OT_refresh_passes(Operator):
    """Atualizar lista de passes de renderização disponíveis."""
    bl_idname = "viewlayer.refresh_passes"
    bl_label = "Atualizar Passes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Salvar seleção atual
        existing_passes = {pass_item.name: pass_item.selected 
                          for pass_item in props.selected_passes}
        
        # Limpar lista de passes
        props.selected_passes.clear()
        
        # Obter passes disponíveis para o renderizador atual
        available_passes = passes_data.get_passes_for_engine(scene.render.engine)
        
        # Adicionar passes à lista
        for pass_name in available_passes:
            # Verificar se a propriedade existe no view layer
            if hasattr(context.view_layer, pass_name):
                item = props.selected_passes.add()
                item.name = pass_name
                item.category = passes_data.get_pass_category(pass_name)
                
                # Manter seleção anterior se existir
                item.selected = existing_passes.get(pass_name, False)
        
        self.report({"INFO"}, f"{len(props.selected_passes)} passes disponíveis para o renderizador {scene.render.engine}.")
        return {"FINISHED"}


class VIEWLAYER_OT_save_passes_prefs(Operator):
    """Salvar configuração atual de passes como preferência"""
    bl_idname = "viewlayer.save_passes_prefs"
    bl_label = "Salvar Preferências de Passes"
    bl_options = {"REGISTER", "UNDO"}
    
    engine: StringProperty(default="cycles")
    
    def execute(self, context):
        props = context.scene.viewlayer_generator_props
        preferences = context.preferences.addons[__name__].preferences
        
        # Limpar preferências existentes
        target_collection = preferences.cycles_passes if self.engine == "cycles" else preferences.eevee_passes
        target_collection.clear()
        
        # Copiar seleção atual para as preferências
        for pass_item in props.selected_passes:
            new_item = target_collection.add()
            new_item.name = pass_item.name
            new_item.selected = pass_item.selected
            new_item.category = pass_item.category
        
        self.report({"INFO"}, f"Preferências de passes para {self.engine} salvas")
        return {"FINISHED"}

class VIEWLAYER_OT_load_passes_prefs(Operator):
    """Carregar preferências de passes"""
    bl_idname = "viewlayer.load_passes_prefs"
    bl_label = "Carregar Preferências de Passes"
    bl_options = {"REGISTER", "UNDO"}
    
    engine: StringProperty(default="cycles")
    
    def execute(self, context):
        props = context.scene.viewlayer_generator_props
        preferences = context.preferences.addons[__name__].preferences
        
        # Obter coleção de preferências
        source_collection = preferences.cycles_passes if self.engine == "cycles" else preferences.eevee_passes
        
        # Aplicar preferências aos passes atuais
        for pass_item in props.selected_passes:
            for pref_item in source_collection:
                if pass_item.name == pref_item.name:
                    pass_item.selected = pref_item.selected
                    break
        
        self.report({"INFO"}, f"Preferências de passes para {self.engine} aplicadas")
        return {"FINISHED"}


# Operador para executar todas as etapas
class VIEWLAYER_OT_generate_all(Operator):
    """Gerar ViewLayers completos (todas as etapas)"""
    bl_idname = "viewlayer.generate_all"
    bl_label = "Gerar ViewLayers Completos"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        # Etapa 1: Gerar ViewLayers
        bpy.ops.viewlayer.generate_layers()
        
        # Etapa 2: Aplicar Passes
        bpy.ops.viewlayer.apply_passes()
        
        # Etapa 3: Aplicar AOVs
        bpy.ops.viewlayer.apply_aovs()
        
        self.report({"INFO"}, "Processo completo finalizado com sucesso")
        return {"FINISHED"}


# Operador para Etapa 1: Gerar apenas as ViewLayers
class VIEWLAYER_OT_generate_layers(Operator):
    """Gerar apenas as ViewLayers a partir das collections selecionadas"""
    bl_idname = "viewlayer.generate_layers"
    bl_label = "Gerar ViewLayers"
    bl_options = {"REGISTER", "UNDO"}
    
    def get_parent_collection(self, collection_name):
        """Obter a collection pai de uma collection."""
        for parent in bpy.data.collections:
            for child in parent.children:
                if child.name == collection_name:
                    return parent.name
        return None

    def process_layer_collection(self, layer_collection, collection_name, lighting_collections, always_active_collections, holdout_collections, holdout_parents, parent_active=False):
        """Processar recursivamente uma layer collection e suas filhas."""
        should_activate = False
        is_holdout = False
        
        # Verificar tratamento especial para viewlayers com sufixo .GP
        is_gp_viewlayer = collection_name.endswith(".GP.vl")
        
        # Verificações para determinar se a collection deve ser ativada
        if parent_active:
            should_activate = True
        elif layer_collection.name == collection_name:
            should_activate = True
        elif layer_collection.name in always_active_collections or layer_collection.name.endswith(".all"):
            should_activate = True
        elif layer_collection.name == "lgt.all" and not is_gp_viewlayer:
            # Para viewlayers GP, não ativar lgt.all
            should_activate = True
        elif layer_collection.name.startswith("lgt."):
            # Para viewlayers GP, nunca ativar collections lgt.*
            if is_gp_viewlayer:
                should_activate = False
            else:
                # Lógica normal para outros viewlayers
                lgt_prefix = layer_collection.name.split(".")[1] if "." in layer_collection.name else ""
                if not lgt_prefix:
                    should_activate = True
                elif collection_name.startswith(lgt_prefix + "."):
                    should_activate = True
        elif layer_collection.name.endswith(".hdt"):
            parent_name = holdout_parents.get(layer_collection.name)
            if parent_name == collection_name:
                should_activate = True
                is_holdout = True
                
        if layer_collection.name.endswith(".hdt"):
            is_holdout = True
        
        # Aplicar as configurações
        if should_activate:
            layer_collection.exclude = False
            if is_holdout:
                layer_collection.holdout = True
        else:
            layer_collection.exclude = True
            layer_collection.holdout = False
            
        # Processar collections filhas recursivamente
        for child in layer_collection.children:
            self.process_layer_collection(
                child, 
                collection_name, 
                lighting_collections, 
                always_active_collections, 
                holdout_collections, 
                holdout_parents, 
                parent_active=should_activate
            )

    def execute(self, context):
        scene = context.scene
        selected_collections = [item.name for item in scene.collection_selection if item.selected]
        
        if not selected_collections:
            self.report({"ERROR"}, "Nenhuma collection selecionada!")
            return {"CANCELLED"}

        # Identificar collections lgt. e collections com sufixos .all e .hdt
        lighting_collections = [col.name for col in bpy.data.collections if col.name.startswith("lgt.")]
        always_active_collections = [col.name for col in bpy.data.collections if col.name.endswith(".all")]
        holdout_collections = [col.name for col in bpy.data.collections if col.name.endswith(".hdt")]
        
        # Criar um dicionário que mapeia cada collection .hdt para sua collection pai
        holdout_parents = {}
        for hdt_name in holdout_collections:
            parent_name = self.get_parent_collection(hdt_name)
            if parent_name:
                holdout_parents[hdt_name] = parent_name
        
        # Criar viewlayers
        for collection_name in selected_collections:
            # Cria a view layer com o nome da collection
            viewlayer_name = collection_name
            viewlayer = scene.view_layers.get(viewlayer_name) or scene.view_layers.new(viewlayer_name)

            # Configurar visibilidade das collections recursivamente
            self.process_layer_collection(
                viewlayer.layer_collection, 
                collection_name, 
                lighting_collections, 
                always_active_collections, 
                holdout_collections,
                holdout_parents,
                parent_active=False
            )
            
            # Verificar se é um viewlayer GP para aplicar apenas o passe combined
            if is_gp_collection(collection_name):
                # Desativar todos os passes primeiro
                for attr in dir(viewlayer):
                    if attr.startswith("use_pass_") and isinstance(getattr(viewlayer, attr), bool):
                        setattr(viewlayer, attr, False)
                
                # Ativar apenas o passe combined
                if hasattr(viewlayer, "use_pass_combined"):
                    setattr(viewlayer, "use_pass_combined", True)

        self.report({"INFO"}, f"{len(selected_collections)} ViewLayers gerados com sucesso!")
        return {"FINISHED"}


# Operador para Etapa 2: Aplicar apenas os Passes
class VIEWLAYER_OT_apply_passes(Operator):
    """Aplicar passes selecionados às ViewLayers existentes"""
    bl_idname = "viewlayer.apply_passes"
    bl_label = "Aplicar Passes"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Obter passes selecionados
        passes = [pass_item.name for pass_item in props.selected_passes if pass_item.selected]
        
        if not passes:
            self.report({"WARNING"}, "Nenhum passe selecionado!")
            return {"CANCELLED"}
        
        # Aplicar passes a todas as view layers
        count = 0
        gp_count = 0
        
        for viewlayer in scene.view_layers:
            # Verificar se é uma viewlayer GP (pelo nome)
            if is_gp_collection(viewlayer.name):
                # Para ViewLayers GP, aplicar apenas o passe combined
                gp_count += 1
                
                # Desativar todos os passes primeiro
                for attr in dir(viewlayer):
                    if attr.startswith("use_pass_") and isinstance(getattr(viewlayer, attr), bool):
                        setattr(viewlayer, attr, False)
                
                # Ativar apenas o passe combined
                if hasattr(viewlayer, "use_pass_combined"):
                    setattr(viewlayer, "use_pass_combined", True)
            else:
                # Para outras ViewLayers, aplicar os passes selecionados normalmente
                for pass_name in passes:
                    if hasattr(viewlayer, pass_name):
                        setattr(viewlayer, pass_name, True)
            
            count += 1
        
        # Mensagem de feedback
        if gp_count > 0:
            self.report({"INFO"}, f"Passes aplicados a {count} ViewLayers ({gp_count} ViewLayers GP receberam apenas o passe combined)")
        else:
            self.report({"INFO"}, f"Passes aplicados com sucesso a {count} ViewLayers: {', '.join(passes)}")
            
        return {"FINISHED"}


# Operador para Etapa 3: Aplicar apenas os AOVs
class VIEWLAYER_OT_apply_aovs(Operator):
    """Aplicar AOVs detectados às ViewLayers existentes"""
    bl_idname = "viewlayer.apply_aovs"
    bl_label = "Aplicar AOVs"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        scene = context.scene
        
        bpy.ops.viewlayer.detect_aovs()
        
        # Obter AOVs selecionados
        selected_aovs = [{"name": item.name, "type": getattr(item, "type", "COLOR")} 
                         for item in scene.detected_aovs if getattr(item, "selected", True)]
        
        if not selected_aovs:
            self.report({"WARNING"}, "Nenhum AOV selecionado!")
            return {"CANCELLED"}
        
        # Aplicar AOVs a todas as view layers
        count = 0
        for viewlayer in scene.view_layers:
            apply_aovs_to_viewlayer(viewlayer, selected_aovs)
            count += 1
        
        aov_names = ", ".join(aov["name"] for aov in selected_aovs)
        self.report({"INFO"}, f"AOVs aplicados com sucesso a {count} ViewLayers: {aov_names}")
        return {"FINISHED"}


# ==========================
# Painéis
# ==========================

# Painel principal
class VIEWLAYER_PT_panel(Panel):
    bl_label = "Gerador de ViewLayers"
    bl_idname = "VIEWLAYER_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View Layer Generator"
    
    def draw(self, context):
        layout = self.layout
        
        # Botão principal (executa todas as etapas)
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Executar todas as etapas:", icon="PLAY")
        col.operator("viewlayer.generate_all", text="Gerar ViewLayers Completos", icon="RENDERLAYERS")


# Subpainel de Collections (Etapa 1)
class VIEWLAYER_PT_collections_panel(Panel):
    bl_label = "Gerar ViewLayers"
    bl_idname = "VIEWLAYER_PT_collections_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View Layer Generator"
    bl_parent_id = "VIEWLAYER_PT_panel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Botão de execução e atualizar como ícone pequeno
        row = layout.row(align=True)
        row.operator("viewlayer.generate_layers", text="Gerar ViewLayers", icon="OUTLINER_OB_GROUP_INSTANCE")
        row.operator("viewlayer.refresh_collections", text="", icon="FILE_REFRESH")
        
        # Lista de collections
        layout.template_list(
            "VIEWLAYER_UL_collections", "", 
            scene, "collection_selection",
            scene, "active_collection_index", rows=5
        )


# Subpainel de Passes (Etapa 2)
class VIEWLAYER_PT_passes_panel(Panel):
    bl_label = "Configurar Passes"
    bl_idname = "VIEWLAYER_PT_passes_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View Layer Generator"
    bl_parent_id = "VIEWLAYER_PT_panel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.viewlayer_generator_props
        
        # Botão de execução desta etapa
        box = layout.box()
        box.operator("viewlayer.apply_passes", text="Aplicar Passes Selecionados", icon="RENDERLAYERS")
        
        # Categorias
        row = layout.row()
        row.label(text="Categorias:")
        row = layout.row(align=True)
        row.prop(props, "show_data_passes", toggle=True)
        row.prop(props, "show_light_passes", toggle=True)
        row.prop(props, "show_crypto_passes", toggle=True)
        
        # Lista de passes
        if len(props.selected_passes) > 0:
            layout.template_list(
                "VIEWLAYER_UL_passes", "",
                props, "selected_passes",
                props, "active_pass_index", rows=5
            )
        else:
            # O botão de atualizar passou a ser automático
            layout.label(text="Nenhum passe disponível")
        
        # Box para usar presets (movido para depois da lista)
        engine = scene.render.engine.lower().replace('blender_', '')
        engine_name = "Cycles" if engine == "cycles" else "Eevee"
        
        # Botão para aplicar o preset do renderizador atual
        op = layout.operator(
            "viewlayer.load_passes_prefs", 
            text=f"Aplicar Preset {engine_name}", 
            icon="PRESET"
        )
        op.engine = engine


# Novo Subpainel de AOVs (Etapa 3)
class VIEWLAYER_PT_aovs_panel(Panel):
    bl_label = "Configurar AOVs"
    bl_idname = "VIEWLAYER_PT_aovs_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View Layer Generator"
    bl_parent_id = "VIEWLAYER_PT_panel"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Botão de detecção e aplicação de AOVs
        row = layout.row()
        row.operator("viewlayer.detect_aovs", text="Detectar AOVs", icon="VIEWZOOM")
        row.operator("viewlayer.apply_aovs", text="Aplicar AOVs", icon="MATERIAL")
        
        # Removi a seção de presets que estava aqui, pois já existe na seção de passes
        
        # Lista de AOVs detectados
        if len(scene.detected_aovs) > 0:
            box = layout.box()
            box.label(text="AOVs Detectados:", icon="MATERIAL")
            
            # Exibir tipo e nome
            for idx, item in enumerate(scene.detected_aovs):
                row = box.row()
                row.prop(item, "selected", text="")
                row.label(text=item.name)
                row.label(text=f"Tipo: {getattr(item, 'type', 'COLOR')}")
        else:
            layout.label(text="Nenhum AOV detectado. Clique em 'Detectar AOVs' para buscar")


# ==========================
# Registro
# ==========================
# Atualização das classes para registro - CORRIGIDO
# ==========================
classes = (
    # UIs
    VIEWLAYER_UL_collections,
    VIEWLAYER_UL_passes,
    VIEWLAYER_UL_aovs,
    
    # Operadores principais
    VIEWLAYER_OT_generate_all,
    VIEWLAYER_OT_generate_layers,
    VIEWLAYER_OT_apply_passes,
    VIEWLAYER_OT_apply_aovs,
    
    # Operadores auxiliares
    VIEWLAYER_OT_refresh_collections,
    VIEWLAYER_OT_refresh_passes,
    VIEWLAYER_OT_detect_aovs,
    VIEWLAYER_OT_activate_lighting,
    VIEWLAYER_OT_activate_holdout,
    
    # Adicionar os operadores de preferências aqui
    VIEWLAYER_OT_load_passes_prefs,
    VIEWLAYER_OT_save_passes_prefs,
    
    # Painéis
    VIEWLAYER_PT_panel,
    VIEWLAYER_PT_collections_panel,
    VIEWLAYER_PT_passes_panel,
    VIEWLAYER_PT_aovs_panel,
)

def register():
    # Imprimir informações de diagnóstico
    print(f"Registrando addon: {__name__}")
    print(f"Módulos carregados: {list(sys.modules.keys())}")
    
    # Registrar propriedades primeiro
    register_properties()
    
    # Adicionar propriedade para index ativo de AOV
    bpy.types.Scene.active_aov_index = bpy.props.IntProperty(default=0)
    
    # Registrar classes deste arquivo
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Registrar preferências por último
    register_preferences(__name__)
    
    # Inicializar preferências com tratamento de erro
    try:
        # Listar todos os addons disponíveis para diagnóstico
        print("Addons disponíveis:")
        for addon_name in bpy.context.preferences.addons.keys():
            print(f"  - {addon_name}")
            
        # Inicializar preferências usando o método alternativo
        for addon_name in bpy.context.preferences.addons.keys():
            preferences = bpy.context.preferences.addons[addon_name].preferences
            if hasattr(preferences, "cycles_passes"):
                print(f"Inicializando preferências para addon: {addon_name}")
                
                # Inicializar passes predefinidos
                if len(preferences.cycles_passes) == 0:
                    initialize_default_passes(preferences.cycles_passes, "CYCLES")
                
                if len(preferences.eevee_passes) == 0:
                    initialize_default_passes(preferences.eevee_passes, "BLENDER_EEVEE")
                    
                break
    except Exception as e:
        print(f"Erro ao inicializar preferências: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Registrar manipulador de eventos
    bpy.app.handlers.depsgraph_update_post.append(update_passes_on_render_change)
    
    # Aplicar automaticamente o preset de passes
    def apply_preset_callback():
        try:
            # Executar apenas uma vez após o carregamento completo da UI
            bpy.ops.viewlayer.refresh_passes()
            engine = bpy.context.scene.render.engine.lower().replace('blender_', '')
            bpy.ops.viewlayer.load_passes_prefs(engine=engine)
            print("Preset de passes aplicado automaticamente")
        except Exception as e:
            print(f"Erro ao aplicar preset automático: {str(e)}")
        return None  # Não repetir o timer
    
    # Registrar o timer para executar em 0.5 segundos
    bpy.app.timers.register(apply_preset_callback, first_interval=0.5)


# Manipulador de eventos para atualizar passes quando o motor de renderização muda
last_render_engine = None
def update_passes_on_render_change(scene):
    global last_render_engine
    if scene.render.engine != last_render_engine:
        last_render_engine = scene.render.engine
        # Atualizar passes disponíveis baseados no novo motor
        bpy.ops.viewlayer.refresh_passes()
        
        # Aplicar automaticamente o preset do novo motor
        try:
            engine = scene.render.engine.lower().replace('blender_', '')
            bpy.ops.viewlayer.load_passes_prefs(engine=engine)
            print(f"Preset de {engine} aplicado após mudança de renderizador")
        except Exception as e:
            print(f"Erro ao aplicar preset após mudança: {str(e)}")

# No método unregister(), assegure que todas as classes são desregistradas
def unregister():
    # Primeiro tentar remover manipuladores de eventos (pode falhar se não estiverem registrados)
    try:
        bpy.app.handlers.depsgraph_update_post.remove(update_passes_on_render_change)
    except ValueError:
        print("Manipulador de eventos não encontrado ou já removido")
    
    # Limpar propriedades da cena
    try:
        del bpy.types.Scene.active_aov_index
    except AttributeError:
        pass
    
    # Cancelar registro das classes deste arquivo - com proteção contra erros
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            print(f"Aviso: Classe {cls.__name__} já estava desregistrada")
    
    # Cancelar registro de preferências
    unregister_preferences()
    
    # Cancelar registro de propriedades
    unregister_properties()


if __name__ == "__main__":
    register()
