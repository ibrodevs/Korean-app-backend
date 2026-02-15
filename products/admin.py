from django.contrib import admin
from .models import (
     WomenClothes, MenClothes, KidsClothes, Shoes,
    Accessories, Beauty, HomeProduct, Electronics, SportsProduct,
    Order, OrderItem
)



@admin.register(WomenClothes)
class WomenClothesAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'size', 'color', 'material', 'price')
    list_filter = ('size', 'color', 'material', 'season', 'brand')
    search_fields = ('name_ru', 'brand')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('size', 'color', 'material', 'season', 'brand')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MenClothes)
class MenClothesAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'size', 'color', 'material', 'price')
    list_filter = ('size', 'color', 'material', 'style', 'brand')
    search_fields = ('name_ru', 'brand')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('size', 'color', 'material', 'style', 'brand')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(KidsClothes)
class KidsClothesAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'age_group', 'gender', 'color', 'price')
    list_filter = ('age_group', 'gender', 'color', 'material')
    search_fields = ('name_ru',)
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('age_group', 'gender', 'color', 'material')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Shoes)
class ShoesAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'size', 'color', 'material', 'price')
    list_filter = ('size', 'color', 'material', 'season', 'brand')
    search_fields = ('name_ru', 'brand')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('size', 'color', 'material', 'season', 'brand')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Accessories)
class AccessoriesAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'item_type', 'color', 'price')
    list_filter = ('item_type', 'material', 'brand')
    search_fields = ('name_ru', 'brand')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('item_type', 'material', 'brand', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Beauty)
class BeautyAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'product_type', 'volume', 'price')
    list_filter = ('product_type', 'purpose', 'shelf_life')
    search_fields = ('name_ru',)
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('product_type', 'purpose', 'ingredients', 'volume', 'shelf_life')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HomeProduct)
class HomeProductAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'item_type', 'color', 'price')
    list_filter = ('item_type', 'material')
    search_fields = ('name_ru',)
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('item_type', 'material', 'dimensions', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Electronics)
class ElectronicsAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'brand', 'model', 'condition', 'price')
    list_filter = ('condition', 'brand', 'warranty_months')
    search_fields = ('name_ru', 'brand', 'model')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Product Info', {
            'fields': ('brand', 'model', 'condition')
        }),
        ('Technical Specs', {
            'fields': ('ram', 'storage', 'processor', 'warranty_months')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SportsProduct)
class SportsProductAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'sport_type', 'level', 'price')
    list_filter = ('sport_type', 'level', 'material')
    search_fields = ('name_ru',)
    fieldsets = (
        ('Basic Info', {
            'fields': ('name_ru', 'name_en', 'name_kg', 'description_ru', 'description_en', 'description_kg')
        }),
        ('Pricing', {
            'fields': ('price', 'discount')
        }),
        ('Details', {
            'fields': ('sport_type', 'size', 'material', 'level')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('customer__username',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Order Info', {
            'fields': ('customer', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'quantity', 'price_at_purchase')
    list_filter = ('order__created_at',)
    search_fields = ('order__id',)
    readonly_fields = ('product',)
