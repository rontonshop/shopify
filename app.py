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

  {% if links %}
  <div class="results">
    <h2>Cart Links</h2>
    <ul>
      {% for link in links %}
      <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
      {% endfor %}
    </ul>
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

    if request.method == "POST":
        urls_input = request.form.get("urls", "")
        default_urls = urls_input
        urls = [url.strip() for url in urls_input.split(",") if url.strip()]
        domain_variants = defaultdict(list)

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

        for domain, variant_chunks in domain_variants.items():
            if variant_chunks:
                cart_url = f"{domain}/cart/" + ",".join(variant_chunks)
                links.append(cart_url)
                try:
                    webbrowser.open(cart_url)
                except:
                    errors.append(f"Could not open browser for {cart_url}")

    return render_template_string(HTML_TEMPLATE, links=links, errors=errors, default_urls=default_urls)

if __name__ == "__main__":
    # Run without debug=True to avoid _multiprocessing error
    app.run(debug=False)
