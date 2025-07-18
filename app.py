from flask import Flask, request, render_template_string
import requests
import re
from collections import defaultdict
import webbrowser

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Shopify Cart Link Builder</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 2em; background-color: #f4f4f4; }
    textarea { width: 100%; height: 150px; font-size: 1em; }
    button { margin-top: 10px; padding: 10px 20px; font-size: 1em; }
    .results { margin-top: 20px; padding: 1em; background-color: #fff; border-radius: 8px; }
    .error { color: red; }
  </style>
</head>
<body>
  <h1>Shopify Cart Link Builder</h1>
  <form method="POST">
    <label for="urls">Paste Shopify product URLs (comma-separated):</label><br>
    <textarea name="urls" id="urls">{{ default_urls }}</textarea><br>
    <button type="submit">Generate Cart Links</button>
  </form>

  {% if items %}
  <div class="results">
    <h2>Individual Items</h2>
    <ul>
      {% for item in items %}
      <li>
        {{ item.title }} x {{ item.quantity }}
        – <a href="{{ item.link }}" target="_blank">Open</a>
      </li>
      {% endfor %}
    </ul>
    <p><strong>Combined Cart Link:</strong> <a href="{{ cart_url }}" target="_blank">Open All</a></p>
  </div>
  {% endif %}

  {% if errors %}
  <div class="results error">
    <h2>Errors</h2>
    <ul>
      {% for error in errors %}
      <li>{{ error }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    default_urls = ""
    items = []
    errors = []
    domain_variants = defaultdict(list)
    cart_url = ""

    if request.method == "POST":
        urls_input = request.form.get("urls", "")
        default_urls = urls_input
        urls = [url.strip() for url in urls_input.split(",") if url.strip()]

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
                    variant_title = variant.get("title", "").strip()
                    base_title = data.get("title", "Unnamed Product").strip()

                    if variant_id:
                        # Add to global cart
                        domain_variants[domain].append(f"{variant_id}:1")

                        # Create individual cart URL
                        item_cart_link = f"{domain}/cart/{variant_id}:1"
                        display_title = (
                            f"{base_title} ({variant_title})" if variant_title and variant_title != "Default Title" else base_title
                        )
                        items.append({
                            "title": display_title,
                            "quantity": 1,
                            "link": item_cart_link
                        })

            except Exception as e:
                errors.append(f"{url} - ❌ Error: {e}")

        # Generate full cart link for the first domain only
        for domain, variants in domain_variants.items():
            cart_url = f"{domain}/cart/" + ",".join(variants)
            try:
                webbrowser.open(cart_url)
            except:
                errors.append(f"Could not open browser for {cart_url}")
            break  # Only one domain supported at a time

    return render_template_string(
        HTML_TEMPLATE,
        items=items,
        cart_url=cart_url,
        errors=errors,
        default_urls=default_urls
    )

if __name__ == "__main__":
    app.run(debug=False)
