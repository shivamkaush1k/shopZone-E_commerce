import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from MyStore.models import Product


class Command(BaseCommand):
    help = "Upload product images from local folder"

    IMAGE_DIR = r"C:\Users\Mohit\Desktop\workspace\Django\djangoing\e_commerce\media\products"
    VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

    def normalize(self, text):
        return str(text).strip().lower().replace(" ", "-").replace("_", "-")

    def find_product(self, filename):
        base = os.path.splitext(filename)[0]
        normalized = self.normalize(base)

        # 1. Match by slug
        product = Product.objects.filter(slug=normalized).first()
        if product:
            return product

        # 2. Match by SKU
        product = Product.objects.filter(sku__iexact=base).first()
        if product:
            return product

        # 3. Match by name
        product = Product.objects.filter(name__iexact=base).first()
        return product

    def handle(self, *args, **kwargs):
        if not os.path.exists(self.IMAGE_DIR):
            self.stdout.write(self.style.ERROR(f"Folder not found: {self.IMAGE_DIR}"))
            return

        files = [
            f for f in os.listdir(self.IMAGE_DIR)
            if f.lower().endswith(self.VALID_EXTENSIONS)
        ]

        self.stdout.write(f"\nFound {len(files)} images\n")

        uploaded = 0
        skipped = 0
        failed = 0

        for i, filename in enumerate(files, 1):
            self.stdout.write(f"[{i}/{len(files)}] {filename}")

            product = self.find_product(filename)

            if not product:
                self.stdout.write(self.style.WARNING("   ❌ No matching product"))
                skipped += 1
                continue

            if product.image:
                self.stdout.write(self.style.WARNING("   ⏭ Already has image"))
                skipped += 1
                continue

            file_path = os.path.join(self.IMAGE_DIR, filename)

            try:
                with open(file_path, "rb") as f:
                    product.image.save(filename, File(f), save=True)

                self.stdout.write(self.style.SUCCESS(f"   ✅ Uploaded to {product.name}"))
                uploaded += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Failed: {e}"))
                failed += 1

        self.stdout.write("\n======= RESULT =======")
        self.stdout.write(self.style.SUCCESS(f"Uploaded: {uploaded}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped}"))
        self.stdout.write(self.style.ERROR(f"Failed: {failed}"))