import bpy
import os
from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, CollectionProperty, BoolProperty

# Importação das propriedades
from .properties import PassItem
from .utils import passes_data


class ViewLayerGeneratorPreferences(AddonPreferences):
    bl_idname = __package__  # Use package name directly
    
    # Cycles passes predefinidos
    cycles_passes: CollectionProperty(type=PassItem)
    
    # Eevee passes predefinidos
    eevee_passes: CollectionProperty(type=PassItem)
    
    # Preferências de exibição
    show_cycles_section: BoolProperty(
        name="Mostrar Configurações do Cycles",
        default=True,
        description="Expandir seção de configurações do Cycles"
    )
    
    show_eevee_section: BoolProperty(
        name="Mostrar Configurações do Eevee",
        default=True,
        description="Expandir seção de configurações do Eevee"
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Cabeçalho
        header = layout.box()
        header_row = header.row()
        header_row.label(text="Configurações de Passes Predefinidos", icon="PRESET")
        
        # Instruções simplificadas
        info = layout.box()
        info_col = info.column(align=True)
        info_col.label(text="Como usar:")
        info_col.label(text="1. Selecione os passes que deseja ativar por padrão")
        info_col.label(text="2. O addon salvará suas preferências automaticamente")
        info_col.label(text="3. Use o botão 'Resetar Passes' para voltar ao padrão")
        
        # Seção Cycles
        cycles_box = layout.box()
        cycles_header = cycles_box.row()
        cycles_header.prop(self, "show_cycles_section", 
                          icon="TRIA_DOWN" if self.show_cycles_section else "TRIA_RIGHT",
                          icon_only=True, emboss=False)
        cycles_header.label(text="Cycles", icon="OUTLINER_OB_LIGHT")
        
        # Botão de reset para Cycles
        action_row = cycles_header.row()
        action_row.alignment = 'RIGHT'
        action_row.operator("viewlayer.reset_passes_prefs", text="Resetar Passes", icon="FILE_REFRESH").engine = "cycles"
        
        if self.show_cycles_section:
            # Data passes
            data_box = cycles_box.box()
            data_box.label(text="Data Passes:", icon="MESH_DATA")
            col = data_box.column(align=True)
            for pass_item in self.cycles_passes:
                if pass_item.category == "Data":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))
            
            # Light passes
            light_box = cycles_box.box()
            light_box.label(text="Light Passes:", icon="LIGHT")
            col = light_box.column(align=True)
            for pass_item in self.cycles_passes:
                if pass_item.category == "Light":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))
            
            # Crypto passes
            crypto_box = cycles_box.box()
            crypto_box.label(text="Cryptomatte Passes:", icon="MATERIAL")
            col = crypto_box.column(align=True)
            for pass_item in self.cycles_passes:
                if pass_item.category == "Crypto Matte":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))
        
        # Espaçamento entre seções
        layout.separator()
        
        # Seção Eevee
        eevee_box = layout.box()
        eevee_header = eevee_box.row()
        eevee_header.prop(self, "show_eevee_section", 
                          icon="TRIA_DOWN" if self.show_eevee_section else "TRIA_RIGHT",
                          icon_only=True, emboss=False)
        eevee_header.label(text="Eevee", icon="SHADING_RENDERED")
        
        # Botão de reset para Eevee
        action_row = eevee_header.row()
        action_row.alignment = 'RIGHT'
        action_row.operator("viewlayer.reset_passes_prefs", text="Resetar Passes", icon="FILE_REFRESH").engine = "eevee"
        
        if self.show_eevee_section:
            # Data passes para Eevee
            data_box = eevee_box.box()
            data_box.label(text="Data Passes:", icon="MESH_DATA")
            col = data_box.column(align=True)
            for pass_item in self.eevee_passes:
                if pass_item.category == "Data":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))
            
            # Light passes para Eevee
            light_box = eevee_box.box()
            light_box.label(text="Light Passes:", icon="LIGHT")
            col = light_box.column(align=True)
            for pass_item in self.eevee_passes:
                if pass_item.category == "Light":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))
            
            # Crypto passes para Eevee
            crypto_box = eevee_box.box()
            crypto_box.label(text="Cryptomatte Passes:", icon="MATERIAL")
            col = crypto_box.column(align=True)
            for pass_item in self.eevee_passes:
                if pass_item.category == "Crypto Matte":
                    col.prop(pass_item, "selected", text=passes_data.get_friendly_name(pass_item.name))


# Novo operador para resetar as preferências
class VIEWLAYER_OT_reset_passes_prefs(Operator):
    """Reseta todos os passes para valores padrão"""
    bl_idname = "viewlayer.reset_passes_prefs"
    bl_label = "Resetar Passes"
    bl_options = {"REGISTER", "UNDO"}
    
    engine: StringProperty(default="cycles")
    
    def execute(self, context):
        try:
            # Obter as preferências do addon
            preferences = None
            
            # Método 1: Tentar usar a variável global
            if _addon_name and _addon_name in context.preferences.addons:
                preferences = context.preferences.addons[_addon_name].preferences
            
            # Método 2: Tentar percorrer todos os addons
            if not preferences:
                for addon_name in context.preferences.addons.keys():
                    if hasattr(context.preferences.addons[addon_name].preferences, "cycles_passes"):
                        preferences = context.preferences.addons[addon_name].preferences
                        break
            
            # Se ainda não encontrou, reportar erro
            if not preferences:
                self.report({"ERROR"}, "Não foi possível encontrar as preferências do addon")
                return {"CANCELLED"}
            
            # Resetar a coleção apropriada
            target_collection = preferences.cycles_passes if self.engine == "cycles" else preferences.eevee_passes
            
            # Redefinir todos os passes para o padrão (apenas combined e z selecionados)
            for pass_item in target_collection:
                pass_item.selected = pass_item.name in ["use_pass_combined", "use_pass_z"]
            
            # Atualizar os passes também na seleção atual se ela existir
            props = context.scene.viewlayer_generator_props
            if hasattr(props, "selected_passes"):
                for pass_item in props.selected_passes:
                    pass_item.selected = pass_item.name in ["use_pass_combined", "use_pass_z"]
            
            engine_name = "Cycles" if self.engine == "cycles" else "Eevee"
            self.report({"INFO"}, f"Passes de {engine_name} restaurados para configuração padrão")
            return {"FINISHED"}
            
        except Exception as e:
            self.report({"ERROR"}, f"Erro ao resetar passes: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"CANCELLED"}


class VIEWLAYER_OT_load_passes_prefs(Operator):
    """Carrega os passes predefinidos nas preferências do addon"""
    bl_idname = "viewlayer.load_passes_prefs"
    bl_label = "Usar Passes Predefinidos"
    bl_options = {"REGISTER", "UNDO"}
    
    engine: StringProperty(default="cycles", 
                          description="Motor de renderização para carregar os passes (cycles ou eevee)")
    
    def execute(self, context):
        try:
            # Obter as preferências do addon usando métodos robustos
            preferences = None
            
            # Método 1: Tentar usar a variável global
            if _addon_name and _addon_name in context.preferences.addons:
                preferences = context.preferences.addons[_addon_name].preferences
            
            # Método 2: Tentar percorrer todos os addons
            if not preferences:
                for addon_name in context.preferences.addons.keys():
                    if hasattr(context.preferences.addons[addon_name].preferences, "cycles_passes"):
                        preferences = context.preferences.addons[addon_name].preferences
                        break
            
            # Se ainda não encontrou, reportar erro
            if not preferences:
                self.report({"ERROR"}, "Não foi possível encontrar as preferências do addon")
                return {"CANCELLED"}
            
            props = context.scene.viewlayer_generator_props
            
            # Obter coleção de preferências
            source_collection = preferences.cycles_passes if self.engine == "cycles" else preferences.eevee_passes
            
            # Verificar se há passes definidos
            if len(source_collection) == 0:
                engine_name = "Cycles" if self.engine == "cycles" else "Eevee"
                self.report({"WARNING"}, f"Não há passes predefinidos para {engine_name}. Configure-os nas preferências do addon.")
                return {"CANCELLED"}
            
            # Aplicar preferências aos passes atuais
            count = 0
            for pass_item in props.selected_passes:
                for pref_item in source_collection:
                    if pass_item.name == pref_item.name:
                        pass_item.selected = pref_item.selected
                        if pref_item.selected:
                            count += 1
                        break
            
            engine_name = "Cycles" if self.engine == "cycles" else "Eevee"
            self.report({"INFO"}, f"Preset de {engine_name} aplicado com sucesso: {count} passes selecionados")
            return {"FINISHED"}
            
        except Exception as e:
            self.report({"ERROR"}, f"Erro ao carregar preferências: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"CANCELLED"}


# Lista de classes para registro (atualizada)
classes = (
    ViewLayerGeneratorPreferences,
    VIEWLAYER_OT_reset_passes_prefs,
    VIEWLAYER_OT_load_passes_prefs,
)


# Variável global para armazenar o nome correto do addon
_addon_name = ""

def register_preferences(bl_id):
    """Registrar as classes de preferências com o ID correto"""
    global classes, _addon_name
    
    # Extrair o nome base do addon, sem subpacotes
    _addon_name = bl_id.split('.')[0]
    print(f"Registrando preferências com nome de addon: {_addon_name}")
    
    # Atualizar o bl_idname dinamicamente
    ViewLayerGeneratorPreferences.bl_idname = _addon_name
    
    # Registrar classes
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Erro ao registrar {cls.__name__}: {str(e)}")


def unregister_preferences():
    """Cancelar registro das classes de preferências"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            # Ignorar erros se a classe já não estiver registrada
            pass


def initialize_default_passes(collection, engine_name):
    """Inicializa passes padrão para um motor de renderização"""
    try:
        available_passes = passes_data.get_passes_for_engine(engine_name)
        
        for pass_name in available_passes:
            item = collection.add()
            item.name = pass_name
            item.category = passes_data.get_pass_category(pass_name)
            # Por padrão, apenas Combined e Z são selecionados
            item.selected = pass_name in ["use_pass_combined", "use_pass_z"]
    except Exception as e:
        print(f"Erro ao inicializar passes padrão: {str(e)}")


# Simple helper function
def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences
    
# Simplified registration
def register():
    bpy.utils.register_class(ViewLayerGeneratorPreferences)
    # Initialize passes here if needed
    
def unregister():
    bpy.utils.unregister_class(ViewLayerGeneratorPreferences)