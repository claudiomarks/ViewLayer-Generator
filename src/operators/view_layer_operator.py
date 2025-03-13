class ViewLayerOperator(bpy.types.Operator):
    bl_idname = "view_layer.create"
    bl_label = "Create View Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Logic to create a new view layer
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)