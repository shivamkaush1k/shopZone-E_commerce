from import_export import resources, fields, widgets
from django.utils.text import slugify
import uuid
from .models import Product, Category

# =============================
# CUSTOM CATEGORY WIDGET (NEW)
# =============================
class CategoryWidget(widgets.ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        # Auto-create category if it doesn't exist
        category, created = Category.objects.get_or_create(
            name=value.strip(),
            defaults={'slug': slugify(value.strip())}
        )
        return category

# =============================
# CATEGORY RESOURCE
# =============================
class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ['name']
        skip_unchanged = True
        report_skipped = True

# =============================
# PRODUCT RESOURCE (FIXED)
# =============================
class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category__name',  # Maps CSV column
        attribute='category',          # Model field
        widget=CategoryWidget(Category, field='name')  # ✅ Auto-creates!
    )

    class Meta:
        model = Product
        import_id_fields = ['sku']
        skip_unchanged = True
        report_skipped = True
        fields = (  # ✅ Fixed fields list
            'id', 'name', 'slug', 'category',  # Use custom field
            'description', 'price', 'original_price', 'stock',
            'image', 'image2', 'image3', 'brand', 'sku',
            'is_active', 'is_featured', 'meta_keywords', 'meta_description'
        )

    def before_import_row(self, row, **kwargs):
        if not row.get('sku') or row['sku'].strip() == '':
            base_sku = slugify(row.get('name', '')).upper().replace('-', '')[:20]
            row['sku'] = f"{base_sku}-{uuid.uuid4().hex[:6].upper()}"
        
        # Auto-generate slug if missing
        if not row.get('slug') or not row['slug'].strip():
            row['slug'] = slugify(row.get('name', ''))
        return row