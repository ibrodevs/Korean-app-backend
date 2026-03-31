from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django import forms
from django.forms import TextInput, Textarea
from mptt.admin import DraggableMPTTAdmin
from .models import (
    Category, CategoryTranslation, Brand, BrandTranslation,
    Product, ProductTranslation, ProductVariant, ProductImage,
    Attribute, AttributeTranslation, AttributeValue, AttributeTextValue, AttributeIntValue, AttributeFloatValue,
    AttributeBooleanValue, AttributeColorValue,
    ProductVariantAttribute, ProductVariantMultiAttribute,
    Tag,
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
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['category', 'brand', 'slug', 'is_active', 'tags']
        }),
        ('Цены и рейтинг', {
            'fields': ['min_price', 'rating', 'review_count'],
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


class AttributeValueForm(forms.ModelForm):
    text_value = forms.CharField(max_length=255, required=False, label='Текст')
    int_value = forms.IntegerField(required=False, label='Целое число')
    float_value = forms.FloatField(required=False, label='Дробное число')
    boolean_value = forms.BooleanField(required=False, label='Булево', widget=forms.Select(choices=[(True, 'Да'), (False, 'Нет')]))
    color_value = forms.CharField(max_length=7, required=False, label='Цвет (HEX)')

    class Meta:
        model = AttributeValue
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'text'):
                self.initial['text_value'] = self.instance.text.value
            if hasattr(self.instance, 'int'):
                self.initial['int_value'] = self.instance.int.value
            if hasattr(self.instance, 'float'):
                self.initial['float_value'] = self.instance.float.value
            if hasattr(self.instance, 'boolean'):
                self.initial['boolean_value'] = self.instance.boolean.value
            if hasattr(self.instance, 'color'):
                self.initial['color_value'] = self.instance.color.value

    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        def save_related():
            attribute = getattr(instance, 'attribute', None)
            if not attribute:
                return
            
            val_type = attribute.value_type
            if val_type == 'text':
                v = self.cleaned_data.get('text_value')
                if v is not None:
                    AttributeTextValue.objects.update_or_create(base=instance, defaults={'value': v})
            elif val_type == 'int':
                v = self.cleaned_data.get('int_value')
                if v is not None:
                    AttributeIntValue.objects.update_or_create(base=instance, defaults={'value': v})
            elif val_type == 'float':
                v = self.cleaned_data.get('float_value')
                if v is not None:
                    AttributeFloatValue.objects.update_or_create(base=instance, defaults={'value': v})
            elif val_type == 'boolean':
                v = self.cleaned_data.get('boolean_value')
                if v is not None:
                    AttributeBooleanValue.objects.update_or_create(base=instance, defaults={'value': v})
            elif val_type == 'color':
                v = self.cleaned_data.get('color_value')
                if v is not None:
                    AttributeColorValue.objects.update_or_create(base=instance, defaults={'value': v})

        if commit:
            save_related()
        else:
            old_save_m2m = self.save_m2m
            def new_save_m2m():
                old_save_m2m()
                save_related()
            self.save_m2m = new_save_m2m
            
        return instance


class AttributeValueInline(admin.TabularInline):
    """Инлайн для значений атрибута"""
    model = AttributeValue
    form = AttributeValueForm
    extra = 1
    show_change_link = True
    classes = ['collapse']
    verbose_name = 'Значение атрибута'
    verbose_name_plural = 'Значения атрибута'
    
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
        return ['text_value', 'int_value', 'float_value', 'boolean_value', 'color_value']
    
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

# Добавьте эту простую регистрацию в конец файла (после всех остальных классов)

@admin.register(AttributeValue)
class SimpleAttributeValueAdmin(admin.ModelAdmin):
    """Простая админка для автодополнения"""
    search_fields = ['translations__name', 'text__value', 'int__value', 'float__value', 'color__value']
    autocomplete_fields = ['attribute']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'attribute'
        ).prefetch_related(
            'translations', 'text', 'int', 'float', 'boolean', 'color'
        )
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Добавляем поиск по связанным моделям значений
        if search_term:
            queryset |= self.model.objects.filter(
                models.Q(text__value__icontains=search_term) |
                models.Q(int__value__icontains=search_term) |
                models.Q(float__value__icontains=search_term) |
                models.Q(color__value__icontains=search_term)
            )
        
        return queryset, use_distinct
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


# Настройка заголовка админки
admin.site.site_header = 'Управление интернет-магазином'
admin.site.site_title = 'Админка магазина'
admin.site.index_title = 'Добро пожаловать в панель управления'