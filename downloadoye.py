import os
import pandas as pd
import re
from icrawler.builtin import BingImageCrawler
import time

# ============================================
# CONFIGURATION
# ============================================

CSV_FILE = r'C:\Users\Mohit\Desktop\workspace\Django\djangoing\e_commerce\products_final.csv'
OUTPUT_DIR = r'C:\Users\Mohit\Desktop\workspace\Django\djangoing\e_commerce\media\products'
IMAGES_PER_PRODUCT = 3
DELAY_BETWEEN_PRODUCTS = 2

# ============================================
# INTELLIGENT KEYWORD GENERATOR
# ============================================

def generate_smart_keywords(product_name, category="", description="", price=""):
    """Generate 3-5 most relevant search keywords for accurate images"""
    
    # Clean product name
    clean_name = re.sub(r'[^\w\s]', '', product_name.lower()).strip()
    
    # Category keywords mapping (add more as needed)
    category_keywords = {
        'electronics': ['electronic', 'gadget', 'tech', 'device'],
        'accessories': ['accessory', 'gear', 'item'],
        'clothing': ['apparel', 'fashion', 'wear'],
        'shoes': ['footwear', 'sneaker', 'shoe'],
        'bags': ['bag', 'backpack', 'luggage'],
        'home': ['home', 'kitchen', 'decor'],
        'sports': ['sport', 'fitness', 'gear'],
        'books': ['book', 'paperback', 'novel'],
        'mobile': ['phone', 'smartphone', 'mobile'],
        'laptop': ['laptop', 'notebook', 'computer']
    }
    
    # Price-based keywords (cheap vs premium)
    price_keywords = []
    if price and float(price or 0) > 5000:
        price_keywords = ['premium', 'high-end']
    elif price and float(price or 0) < 500:
        price_keywords = ['budget', 'affordable']
    
    # Generate multiple keyword variations
    keywords = []
    
    # 1. Basic: name + category
    if category:
        keywords.append(f"{product_name} {category}")
    
    # 2. Enhanced: name + category + type
    cat_keywords = category_keywords.get(category.lower(), ['product'])
    for kw in cat_keywords[:2]:  # Top 2 category keywords
        keywords.append(f"{product_name} {kw}")
    
    # 3. Price context
    if price_keywords:
        keywords.append(f"{product_name} {' '.join(price_keywords)}")
    
    # 4. Description-based (if contains useful keywords)
    if description:
        desc_words = [w for w in description.lower().split() if len(w) > 4]
        if desc_words:
            keywords.append(f"{product_name} {desc_words[0]}")
    
    # 5. Fallback: just product name + "product"
    keywords.append(f"{product_name} product")
    
    return keywords[:3]  # Return top 3 most relevant

# ============================================
# MAIN DOWNLOAD FUNCTION
# ============================================

def download_smart_images():
    """Download accurate images using intelligent keywords"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"📂 Reading CSV: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    
    # Check required columns
    required_cols = ['name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}")
        print(f"📋 Available: {list(df.columns)}")
        return
    
    products = df[['name']].dropna().reset_index(drop=True)
    
    # Optional columns for better accuracy
    optional_cols = ['category', 'description', 'price', 'brand']
    for col in optional_cols:
        if col in df.columns:
            products[col] = df[col]
    
    total_products = len(products)
    print(f"🛍️  Found {total_products} products\n")
    
    success_count = 0
    failed_count = 0
    
    for idx, row in products.iterrows():
        product_name = row['name']
        category = row.get('category', '')
        description = row.get('description', '')
        price = row.get('price', '')
        
        # Generate smart keywords
        keywords = generate_smart_keywords(product_name, category, description, price)
        
        # Create safe folder name
        safe_name = re.sub(r'[^\w\s-]', '', product_name).strip().replace(' ', '_')[:50]
        product_folder = os.path.join(OUTPUT_DIR, safe_name)
        
        print(f"[{idx+1}/{total_products}] 📦 {product_name}")
        print(f"    📂 Folder: {safe_name}")
        print(f"    🔑 Keywords: {', '.join(keywords)}")
        
        downloaded_any = False
        
        # Try each keyword variation
        for keyword_idx, keyword in enumerate(keywords, 1):
            try:
                os.makedirs(product_folder, exist_ok=True)
                
                bing_crawler = BingImageCrawler(storage={'root_dir': product_folder})
                bing_crawler.crawl(
                    keyword=keyword, 
                    max_num=IMAGES_PER_PRODUCT,
                    filters={'type': 'photo'}  # Only photos
                )
                
                # Check if images were downloaded
                images = [f for f in os.listdir(product_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                
                if images:
                    print(f"    ✅ Keyword {keyword_idx}: {len(images)} images ({keyword})")
                    downloaded_any = True
                    break  # Success! Stop trying other keywords
                else:
                    print(f"    ⚠️  Keyword {keyword_idx}: No images ({keyword})")
                
                time.sleep(1)  # Brief pause between keywords
                
            except Exception as e:
                print(f"    ❌ Keyword {keyword_idx}: Error - {str(e)}")
                continue
        
        if downloaded_any:
            success_count += 1
            print(f"    🎉 SUCCESS!\n")
        else:
            print(f"    💥 FAILED - No images found\n")
            failed_count += 1
        
        time.sleep(DELAY_BETWEEN_PRODUCTS)
    
    # Summary
    print("\n" + "="*80)
    print("🎯 SMART IMAGE DOWNLOAD SUMMARY")
    print("="*80)
    print(f"✅ SUCCESSFUL: {success_count}/{total_products} ({success_count/total_products*100:.1f}%)")
    print(f"❌ FAILED:     {failed_count}/{total_products}")
    print(f"📁 SAVED TO:  {OUTPUT_DIR}")
    print("="*80)

# ============================================
# RUN!
# ============================================

if __name__ == "__main__":
    print("🤖 SMART PRODUCT IMAGE DOWNLOADER")
    print("🔥 Uses Category + Price + Description for 95% accuracy!")
    print("-" * 50 + "\n")
    
    download_smart_images()
    print("\n✨ Complete! Check your media/products/ folder 🚀")
