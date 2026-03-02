from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import TextInput, Textarea
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import (
    Category, CategoryTranslation, Brand, BrandTranslation,
    Product, ProductTranslation, ProductVariant, ProductImage,
    Attribute, AttributeTranslation, AttributeValue, AttributeValueTranslation,
    AttributeTextValue, AttributeIntValue, AttributeFloatValue,
    AttributeBooleanValue, AttributeColorValue,
    ProductVariantAttribute, ProductVariantMultiAttribute
)


class BaseTranslationInline(admin.TabularInline):
    """Базовый класс для инлайн переводов"""
    extra = 1
    max_num = 10
    classes = ['collapse']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 40})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }


class CategoryTranslationInline(BaseTranslationInline):
    model = CategoryTranslation


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """Админка для категорий с древовидной структурой"""
    list_display = ['tree_actions', 'indented_title', 'slug', 'order', 'products_count']
    list_display_links = ['indented_title']
    list_editable = ['order']
    search_fields = ['slug', 'translations__name']
    prepopulated_fields = {'slug': ('translations__name',)}
    inlines = [CategoryTranslationInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations', 'products')
    
    def products_count(self, obj):
        count = obj.products.count()
        return format_html('<b>{}</b>', count)
    products_count.short_description = 'Товаров'


class BrandTranslationInline(BaseTranslationInline):
    model = BrandTranslation


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Админка для брендов"""
    list_display = ['name', 'slug', 'products_count']
    search_fields = ['slug', 'translations__name']
    prepopulated_fields = {'slug': ('translations__name',)}
    inlines = [BrandTranslationInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations', 'products')
    
    def name(self, obj):
        translation = obj.translations.first()
        return translation.name if translation else '-'
    name.short_description = 'Название'
    
    def products_count(self, obj):
        count = obj.products.count()
        return format_html('<b>{}</b>', count)
    products_count.short_description = 'Товаров'


class ProductImageInline(admin.TabularInline):
    """Инлайн для изображений товара"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt', 'is_main', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Превью'


class ProductVariantInline(admin.StackedInline):
    """Инлайн для вариантов товара"""
    model = ProductVariant
    extra = 1
    fieldsets = [
        (None, {
            'fields': ['sku', 'price', 'old_price', 'stock', 'is_active', 'is_default']
        }),
    ]
    classes = ['collapse']


class ProductTranslationInline(BaseTranslationInline):
    model = ProductTranslation
    fields = ['language', 'name', 'description', 'meta_title', 'meta_description', 'meta_keywords']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    list_display = ['name', 'category', 'brand', 'is_active', 'min_price', 'variants_count', 'created_at']
    list_filter = ['is_active', 'category', 'brand', 'created_at']
    search_fields = ['slug', 'translations__name', 'translations__description']
    prepopulated_fields = {'slug': ('translations__name',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['category', 'brand', 'slug', 'is_active']
        }),
        ('Цены', {
            'fields': ['min_price'],
            'classes': ['collapse']
        }),
        ('Даты', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [ProductTranslationInline, ProductVariantInline, ProductImageInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'brand'
        ).prefetch_related(
            'translations', 'variants'
        )
    
    def name(self, obj):
        translation = obj.translations.first()
        return translation.name if translation else '-'
    name.short_description = 'Название'
    name.admin_order_field = 'translations__name'
    
    def variants_count(self, obj):
        count = obj.variants.count()
        return format_html('<b>{}</b>', count)
    variants_count.short_description = 'Вариантов'


class ProductVariantAttributeInline(admin.TabularInline):
    """Инлайн для атрибутов варианта"""
    model = ProductVariantAttribute
    extra = 1
    autocomplete_fields = ['attribute', 'value']
    classes = ['collapse']
    verbose_name = 'Одиночный атрибут'
    verbose_name_plural = 'Одиночные атрибуты'


class ProductVariantMultiAttributeInline(admin.TabularInline):
    """Инлайн для множественных атрибутов варианта"""
    model = ProductVariantMultiAttribute
    extra = 1
    autocomplete_fields = ['attribute', 'value']
    classes = ['collapse']
    verbose_name = 'Множественный атрибут'
    verbose_name_plural = 'Множественные атрибуты'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Админка для вариантов товаров"""
    list_display = ['sku', 'product_name', 'price', 'old_price', 'stock', 'is_active', 'is_default']
    list_filter = ['is_active', 'is_default', 'product__category']
    search_fields = ['sku', 'product__translations__name']
    list_editable = ['price', 'stock', 'is_active']
    autocomplete_fields = ['product']
    
    fieldsets = [
        (None, {
            'fields': ['product', 'sku', 'is_active', 'is_default']
        }),
        ('Цены и наличие', {
            'fields': ['price', 'old_price', 'stock']
        }),
    ]
    
    inlines = [ProductVariantAttributeInline, ProductVariantMultiAttributeInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product').prefetch_related(
            'product__translations'
        )
    
    def product_name(self, obj):
        translation = obj.product.translations.first()
        return translation.name if translation else '-'
    product_name.short_description = 'Товар'
    product_name.admin_order_field = 'product__translations__name'


class AttributeValueInline(admin.TabularInline):
    """Инлайн для значений атрибута"""
    model = AttributeValue
    extra = 1
    show_change_link = True
    
    def get_fields(self, request, obj=None):
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
        return []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.value_type == 'color':
            return ['color_preview']
        return []
    
    def color_preview(self, obj):
        if hasattr(obj, 'color') and obj.color:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px;"></div>',
                obj.color.value
            )
        return '-'
    color_preview.short_description = 'Превью'


class AttributeTranslationInline(BaseTranslationInline):
    model = AttributeTranslation


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    """Админка для атрибутов"""
    list_display = ['name', 'slug', 'value_type', 'is_multiple', 'values_count']
    list_filter = ['value_type', 'is_multiple']
    search_fields = ['slug', 'translations__name']
    prepopulated_fields = {'slug': ('translations__name',)}
    inlines = [AttributeTranslationInline, AttributeValueInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations', 'values')
    
    def name(self, obj):
        translation = obj.translations.first()
        return translation.name if translation else '-'
    name.short_description = 'Название'
    
    def values_count(self, obj):
        count = obj.values.count()
        return format_html('<b>{}</b>', count)
    values_count.short_description = 'Значений'


class AttributeValueTranslationInline(BaseTranslationInline):
    model = AttributeValueTranslation
    fields = ['language', 'name']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    """Админка для значений атрибутов"""
    list_display = ['id', 'attribute_name', 'value_display', 'translations_count']
    list_filter = ['attribute__value_type', 'attribute']
    search_fields = ['translations__name', 'text__value', 'int__value', 'float__value', 'color__value']
    inlines = [AttributeValueTranslationInline]
    
    fieldsets = [
        ('Атрибут', {
            'fields': ['attribute']
        }),
    ]
    
    def get_fieldsets(self, request, obj=None):
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
        
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        readonly = []
        if obj and obj.attribute and obj.attribute.value_type == 'color':
            readonly.append('color_preview')
        return readonly
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('attribute').prefetch_related(
            'attribute__translations', 'translations'
        )
    
    def attribute_name(self, obj):
        translation = obj.attribute.translations.first()
        return translation.name if translation else obj.attribute.slug
    attribute_name.short_description = 'Атрибут'
    
    def value_display(self, obj):
        if hasattr(obj, 'text'):
            return obj.text.value
        elif hasattr(obj, 'int'):
            return obj.int.value
        elif hasattr(obj, 'float'):
            return obj.float.value
        elif hasattr(obj, 'boolean'):
            return 'Да' if obj.boolean.value else 'Нет'
        elif hasattr(obj, 'color'):
            return format_html(
                '<span style="color: {};">⬤</span> {}',
                obj.color.value, obj.color.value
            )
        return '-'
    value_display.short_description = 'Значение'
    
    def translations_count(self, obj):
        count = obj.translations.count()
        return format_html('<b>{}</b>', count)
    translations_count.short_description = 'Переводов'
    
    def color_preview(self, obj):
        if hasattr(obj, 'color') and obj.color:
            return format_html(
                '<div style="width: 50px; height: 50px; background-color: {}; border-radius: 4px;"></div>',
                obj.color.value
            )
        return '-'
    color_preview.short_description = 'Превью'


# Регистрация моделей значений атрибутов для возможности прямого редактирования
@admin.register(AttributeTextValue)
class AttributeTextValueAdmin(admin.ModelAdmin):
    list_display = ['base', 'value']
    search_fields = ['value']


@admin.register(AttributeIntValue)
class AttributeIntValueAdmin(admin.ModelAdmin):
    list_display = ['base', 'value']
    search_fields = ['value']


@admin.register(AttributeFloatValue)
class AttributeFloatValueAdmin(admin.ModelAdmin):
    list_display = ['base', 'value']
    search_fields = ['value']


@admin.register(AttributeBooleanValue)
class AttributeBooleanValueAdmin(admin.ModelAdmin):
    list_display = ['base', 'value']
    list_filter = ['value']


@admin.register(AttributeColorValue)
class AttributeColorValueAdmin(admin.ModelAdmin):
    list_display = ['base', 'value', 'color_preview']
    search_fields = ['value']
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px;"></div>',
            obj.value
        )
    color_preview.short_description = 'Превью'


# Настройка заголовка админки
admin.site.site_header = 'Управление интернет-магазином'
admin.site.site_title = 'Админка магазина'
admin.site.index_title = 'Добро пожаловать в панель управления'