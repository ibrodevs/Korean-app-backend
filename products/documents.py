from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Product, ProductVariant

@registry.register_document
class ProductDocument(Document):
    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'slug': fields.KeywordField(),
    })
    
    brand = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'slug': fields.KeywordField(),
        'translations': fields.NestedField(properties={
            'language': fields.KeywordField(),
            'name': fields.KeywordField(),
        })
    })

    translations = fields.NestedField(properties={
        'language': fields.KeywordField(),
        'name': fields.TextField(analyzer='standard'),
        'description': fields.TextField(analyzer='standard'),
    })

    attributes = fields.NestedField(properties={
        'attribute_slug': fields.KeywordField(),
        'value_id': fields.IntegerField(),
        'value_type': fields.KeywordField(),
        'value_text': fields.KeywordField(),
        'value_name_translations': fields.NestedField(properties={
            'language': fields.KeywordField(),
            'name': fields.KeywordField(),
        })
    })

    class Index:
        name = 'products'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Product
        fields = [
            'id',
            'slug',
            'is_active',
            'min_price',
            'created_at',
        ]
        related_models = [ProductVariant]
        queryset_pagination = 5000

    def get_queryset(self):
        return super().get_queryset().select_related(
            'category', 'brand'
        ).prefetch_related(
            'translations',
            'brand__translations',
            'variants__single_attributes__attribute',
            'variants__single_attributes__value__translations',
            'variants__multi_attributes__attribute',
            'variants__multi_attributes__value__translations',
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, ProductVariant):
            return related_instance.product
        return None

    def prepare_brand(self, instance):
        if not instance.brand:
            return {}
        
        translations = []
        for t in instance.brand.translations.all():
            translations.append({
                'language': t.language,
                'name': t.name
            })
            
        return {
            'id': instance.brand.id,
            'slug': instance.brand.slug,
            'translations': translations
        }

    def prepare_category(self, instance):
        if not instance.category:
            return {}
        return {
            'id': instance.category.id,
            'slug': instance.category.slug,
        }

    def prepare_translations(self, instance):
        translations = []
        for t in instance.translations.all():
            translations.append({
                'language': t.language,
                'name': t.name,
                'description': t.description,
            })
        return translations

    def prepare_attributes(self, instance):
        attrs = []
        
        for variant in instance.variants.all():
            # Single attributes
            for pva in variant.single_attributes.all():
                value = pva.value
                translations = [{'language': t.language, 'name': t.name} for t in value.translations.all()]
                attrs.append({
                    'attribute_slug': pva.attribute.slug,
                    'value_id': value.id,
                    'value_type': pva.attribute.value_type,
                    'value_text': str(value.typed_value),
                    'value_name_translations': translations
                })
                
            # Multi attributes
            for pvma in variant.multi_attributes.all():
                value = pvma.value
                translations = [{'language': t.language, 'name': t.name} for t in value.translations.all()]
                attrs.append({
                    'attribute_slug': pvma.attribute.slug,
                    'value_id': value.id,
                    'value_type': pvma.attribute.value_type,
                    'value_text': str(value.typed_value),
                    'value_name_translations': translations
                })
                
        return attrs
