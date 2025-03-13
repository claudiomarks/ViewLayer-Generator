def create_view_layer(name):
    import bpy
    
    # Check if a view layer with the same name already exists
    if name in bpy.context.scene.view_layers:
        raise ValueError(f"View layer '{name}' already exists.")
    
    # Create a new view layer
    view_layer = bpy.context.scene.view_layers.new(name)
    return view_layer

def delete_view_layer(name):
    import bpy
    
    # Check if the view layer exists
    if name not in bpy.context.scene.view_layers:
        raise ValueError(f"View layer '{name}' does not exist.")
    
    # Delete the view layer
    bpy.context.scene.view_layers.remove(bpy.context.scene.view_layers[name])