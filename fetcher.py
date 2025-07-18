import requests
import re
from collections import defaultdict

def build_combined_cart_links(urls_input):
    urls = [url.strip() for url in urls_input.split(",") if url.strip()]
    domain_variants = defaultdict(list)
    errors = []

    for url in urls:
        match = re.search(r'/products/([^/?]+)', url)
        if not match:
            errors.append(f"{url} - ❌ Product handle not found.")
            continue

        handle = match.group(1)
        domain = re.search(r'https?://[^/]+', url).group(0)
        product_json_url = f"{domain}/products/{handle}.js"

        try:
            response = requests.get(product_json_url)
            response.raise_for_status()
            data = response.json()

            for variant in data.get("variants", []):
                variant_id = variant.get("id")
                if variant_id:
                    domain_variants[domain].append(f"{variant_id}:1")

        except Exception as e:
            errors.append(f"{url} - ❌ Error: {e}")

    # Print results
    if domain_variants:
        print("✅ Combined Add-to-Cart Links:")
        for domain, variant_chunks in domain_variants.items():
            cart_url = f"{domain}/cart/" + ",".join(variant_chunks)
            print(cart_url)

    if errors:
        print("\n❌ Errors:")
        for err in errors:
            print(err)

# Example usage
user_input = input("Paste Shopify product URLs separated by commas:\n")
build_combined_cart_links(user_input)
