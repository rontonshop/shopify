from flask import Flask, request, render_template_string
import requests
import re
from collections import defaultdict
import webbrowser
from waitress import serve

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

  {% if links %}
  <div class="results">
    <h2>Cart Items</h2>
    <ul>
      {% for item in links %}
      <li>{{ item.title }} x {{ item.quantity }}</li>
      {% endfor %}
    </ul>
    <p><strong>Final Cart Link:</strong> <a href="{{ cart_url }}" target="_blank">Open Cart</a></p>
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
    links = []
    errors = []
    default_urls = ""
    cart_url = ""

    if request.method == "POST":
        urls_input = request.form.get("urls", "")
        default_urls = urls_input
        urls = [url.strip() for url in urls_input.split(",") if url.strip()]
        domain_variants = defaultdict(list)
        display_items = []

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
                    variant_title = variant.get("title")
                    if variant_id:
                        domain_variants[domain].append(f"{variant_id}:1")
                        display_items.append({
                            "title": f"{data.get('title')} ({variant_title})" if variant_title and variant_title != "Default Title" else data.get('title'),
                            "quantity": 1
                        })

            except Exception as e:
                errors.append(f"{url} - ❌ Error: {e}")

        for domain, variant_chunks in domain_variants.items():
            if variant_chunks:
                cart_url = f"{domain}/cart/" + ",".join(variant_chunks)
                try:
                    webbrowser.open(cart_url)
                except:
                    errors.append(f"Could not open browser for {cart_url}")

    return render_template_string(HTML_TEMPLATE, links=display_items, errors=errors, default_urls=default_urls, cart_url=cart_url)

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)
