from django.core.management.base import BaseCommand
from MyStore.models import Product

class Command(BaseCommand):
    help = 'Fix product is_active and stock status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stock',
            type=int,
            default=10,
            help='Default stock quantity'
        )

    def handle(self, *args, **options):
        stock_qty = options['stock']
        
        # Update all products
        products = Product.objects.all()
        updated = 0
        
        for product in products:
            old_active = product.is_active
            old_stock = product.stock
            
            # Update
            product.is_active = True
            product.stock = stock_qty if product.stock == 0 or product.stock is None else product.stock
            product.save()
            
            updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {product.name}: active={old_active}→True, stock={old_stock}→{product.stock}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Total updated: {updated}')
        )
