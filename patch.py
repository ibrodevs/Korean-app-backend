import re

file_path = "products/admin.py"
with open(file_path, "r") as f:
    content = f.read()

# Replace get_fields to return all fields when obj is None
original_get_fields = """    def get_fields(self, request, obj=None):
        if obj:
            if obj.value_type == 'text':
                return ['text_value']
            elif obj.value_type == 'int':
                return ['int_value']
            elif obj.value_type == 'float':
                return ['float_value']
            elif obj.value_type == 'boolean':
                return ['boolean_value']
            elif obj.value_type == 'color':
                return ['color_value', 'color_preview']
        return []"""

new_get_fields = """    def get_fields(self, request, obj=None):
        if obj:
            if obj.value_type == 'text':
                return ['text_value']
            elif obj.value_type == 'int':
                return ['int_value']
            elif obj.value_type == 'float':
                return ['float_value']
            elif obj.value_type == 'boolean':
                return ['boolean_value']
            elif obj.value_type == 'color':
                return ['color_value', 'color_preview']
        return ['text_value', 'int_value', 'float_value', 'boolean_value', 'color_value']"""

content = content.replace(original_get_fields, new_get_fields)

# Let's also do something for AttributeValueAdmin get_fieldsets to allow adding new from standalone form
original_get_fieldsets = """    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj and obj.attribute:
            value_type = obj.attribute.value_type
            if value_type == 'text':
                extra_fields = [('Значение', {'fields': ['text_value']})]
            elif value_type == 'int':
                extra_fields = [('Значение', {'fields': ['int_value']})]
            elif value_type == 'float':
                extra_fields = [('Значение', {'fields': ['float_value']})]
            elif value_type == 'boolean':
                extra_fields = [('Значение', {'fields': ['boolean_value']})]
            elif value_type == 'color':
                extra_fields = [('Значение', {'fields': ['color_value', 'color_preview']})]
            else:
                extra_fields = []
            
            fieldsets = list(fieldsets) + extra_fields
        
        return fieldsets"""

new_get_fieldsets = """    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj and obj.attribute:
            value_type = obj.attribute.value_type
            if value_type == 'text':
                extra_fields = [('Значение', {'fields': ['text_value']})]
            elif value_type == 'int':
                extra_fields = [('Значение', {'fields': ['int_value']})]
            elif value_type == 'float':
                extra_fields = [('Значение', {'fields': ['float_value']})]
            elif value_type == 'boolean':
                extra_fields = [('Значение', {'fields': ['boolean_value']})]
            elif value_type == 'color':
                extra_fields = [('Значение', {'fields': ['color_value', 'color_preview']})]
            else:
                extra_fields = []
            
            fieldsets = list(fieldsets) + extra_fields
        else:
            # When creating a new AttributeValue directly, show all possible fields
            extra_fields = [('Значение', {'fields': ['text_value', 'int_value', 'float_value', 'boolean_value', 'color_value']})]
            fieldsets = list(fieldsets) + extra_fields
        
        return fieldsets"""

content = content.replace(original_get_fieldsets, new_get_fieldsets)

with open(file_path, "w") as f:
    f.write(content)

print("Patched admin.py")
