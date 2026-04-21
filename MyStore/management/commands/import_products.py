import csv
from django.core.management.base import BaseCommand
from MyStore.models import Product, Category

class Command(BaseCommand):
    help = 'Import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Get or create category
                category_name = row.get('category__name', '').strip()
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': category_name.lower().replace(' ', '-')}
                )
                
                # Create or update product
                Product.objects.update_or_create(
                    sku=row['sku'],
                    defaults={
                        'name': row['name'],
                        'category': category,
                        'description': row.get('description', ''),
                        'price': float(row['price']),
                        'original_price': float(row.get('original_price', 0)) or None,
                        'stock': int(row.get('stock', 0)),
                        'brand': row.get('brand', ''),
                        'is_active': row.get('is_active', 'True').lower() == 'true',
                        'is_featured': row.get('is_featured', 'False').lower() == 'true',
                    }
                )
                
                self.stdout.write(self.style.SUCCESS(f'Imported: {row["name"]}'))
        
        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
