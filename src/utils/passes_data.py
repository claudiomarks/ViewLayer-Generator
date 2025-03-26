# ==========================
# Categorias de Passes (para UI)
# ==========================

# Passes de dados (geometria, coordenadas, etc.)
DATA_PASSES = [
    "use_pass_combined",
    "use_pass_z",
    "use_pass_position", 
    "use_pass_normal",
    "use_pass_vector",
    "use_pass_uv",
    "use_pass_mist",
    "use_pass_object_index",
    "use_pass_material_index",
    "use_pass_alpha"
]

# Passes relacionados à iluminação e sombreamento
LIGHT_PASSES = [
    "use_pass_diffuse_direct", 
    "use_pass_diffuse_indirect", 
    "use_pass_diffuse_color",
    "use_pass_glossy_direct", 
    "use_pass_glossy_indirect", 
    "use_pass_glossy_color",
    "use_pass_transmission_direct", 
    "use_pass_transmission_indirect", 
    "use_pass_transmission_color",
    "use_pass_volume_direct", 
    "use_pass_emit", 
    "use_pass_environment",
    "use_pass_shadow", 
    "use_pass_ambient_occlusion",
    "use_pass_transparent"
]

# Passes de Cryptomatte
CRYPTO_PASSES = [
    "use_pass_cryptomatte_object", 
    "use_pass_cryptomatte_material", 
    "use_pass_cryptomatte_asset"
]

# Outros passes
OTHER_PASSES = [
    "use_denoising_data"
]

# ==========================
# Listas Completas por Renderizador
# ==========================

# Todos os passes disponíveis no Cycles
CYCLES_PASSES = [
    # Data passes
    "use_pass_combined",
    "use_pass_z",
    "use_pass_position", 
    "use_pass_normal",
    "use_pass_vector",
    "use_pass_uv",
    "use_pass_mist",
    "use_pass_object_index",
    "use_pass_material_index",
    "use_pass_alpha",
    
    # Light passes
    "use_pass_diffuse_direct", 
    "use_pass_diffuse_indirect", 
    "use_pass_diffuse_color",
    "use_pass_glossy_direct", 
    "use_pass_glossy_indirect", 
    "use_pass_glossy_color",
    "use_pass_transmission_direct", 
    "use_pass_transmission_indirect", 
    "use_pass_transmission_color",
    "use_pass_volume_direct", 
    "use_pass_emit", 
    "use_pass_environment",
    "use_pass_shadow", 
    "use_pass_ambient_occlusion",
    "use_pass_transparent",
    
    # Crypto passes
    "use_pass_cryptomatte_object", 
    "use_pass_cryptomatte_material", 
    "use_pass_cryptomatte_asset",
    
    # Other
    "use_denoising_data"
]

# Todos os passes disponíveis no Eevee/Eevee Next
EEVEE_PASSES = [
    # Data passes
    "use_pass_combined",
    "use_pass_z",
    "use_pass_position", 
    "use_pass_normal",
    "use_pass_vector",
    "use_pass_uv",
    "use_pass_mist",
    "use_pass_object_index",
    "use_pass_material_index",
    "use_pass_alpha",
    
    # Light passes (subset disponível no Eevee)
    "use_pass_diffuse_direct", 
    "use_pass_diffuse_color",
    "use_pass_glossy_direct", 
    "use_pass_glossy_color",
    "use_pass_emit", 
    "use_pass_environment",
    "use_pass_shadow", 
    "use_pass_ambient_occlusion",
    "use_pass_volume_direct",  # Adicionado conforme solicitado
    "use_pass_transparent",    # Adicionado conforme solicitado

    # Crypto passes
    "use_pass_cryptomatte_object", 
    "use_pass_cryptomatte_material", 
    "use_pass_cryptomatte_asset"
]

# ==========================
# Funções Auxiliares
# ==========================

def get_passes_for_engine(engine_name):
    """Retorna a lista de passes para um determinado renderizador."""
    if engine_name == 'CYCLES':
        return CYCLES_PASSES
    elif engine_name in ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT']:
        return EEVEE_PASSES
    else:
        # Para outros renderizadores desconhecidos, retorne apenas passes básicos
        return DATA_PASSES

def get_pass_category(pass_name):
    """Retorna a categoria de um determinado passe."""
    if pass_name in CRYPTO_PASSES:
        return "Crypto Matte"
    elif pass_name in DATA_PASSES:
        return "Data"
    elif pass_name in LIGHT_PASSES:
        return "Light"
    else:
        return "Other"

def get_friendly_name(pass_name):
    """Retorna um nome amigável para exibição na UI."""
    
    # Mapeamento de nomes específicos
    friendly_names = {
        "use_pass_combined": "Combined",
        "use_pass_z": "Depth",
        "use_pass_position": "Position",
        "use_pass_cryptomatte_object": "Cryptomatte Object",
        "use_pass_cryptomatte_material": "Cryptomatte Material",
        "use_pass_cryptomatte_asset": "Cryptomatte Asset"
    }
    
    if pass_name in friendly_names:
        return friendly_names[pass_name]
    elif pass_name.startswith("use_pass_"):
        return pass_name[9:].replace("_", " ").title()
    else:
        return pass_name.replace("use_", "").replace("_", " ").title()