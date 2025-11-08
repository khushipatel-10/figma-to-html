# 🎨 Figma to HTML Converter

This project converts **Figma designs** into **HTML + CSS** automatically using the Figma REST API.
It connects to Figma, fetches your design structure, and generates pixel-accurate, browser-ready code that reflects your mockup.

---

## 🧭 Overview

The converter extracts design data from Figma (frames, text, rectangles, gradients, etc.) and transforms them into HTML elements styled with CSS.
This helps designers and developers quickly preview or prototype front-end layouts based on Figma designs.

---

## 📁 Repository Structure

```
📁 Figma-to-HTML/
│
├── figma_to_html.py        # 🧠 Main script – converts Figma JSON data to HTML + CSS
├── figma_to_json.py        # 🌐 Fetches JSON design data from the Figma API
├── test_converter.py       # 🥪 Tests and validates generated HTML accuracy
├── main.html               # 💻 Final output – HTML/CSS generated from the given mockup
├── output.json             # 📄 Raw design data (JSON) fetched from Figma API
├── requirements.txt        # ⚙️ Python dependencies
├── .gitignore              # 🧹 Ignores unnecessary local files
│
└── Trial/                  # 🎨 Used to test converter on a second mockup
    ├── Trial_2.png         # Screenshot of the second mockup
    ├── trial_2.html        # Generated HTML output with images and SVGs
    └── trial_2_old.html    # Older version for comparison
```

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/figma-to-html.git
cd figma-to-html
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

*(This project uses the `requests` library to communicate with the Figma API.)*

---

## 🧾 Configuration Setup

Create a file named **`config.py`** in the project’s root directory and add your details:

```python
FIGMA_TOKEN = "figd_45y..."     # 🔑 Your Figma Personal Access Token
FILE_KEY = "your_file_key"      # 🗂️ File key from your Figma file URL
NODE_ID = "0:1"                 # 🎯 Node or frame ID to export
OUTPUT_FILE = "output.html"     # 💾 Output filename (edit this to rename the result)
```

🖊️ **To rename your generated output file** —
simply change the line:

```python
OUTPUT_FILE = "output.html"
```

to:

```python
OUTPUT_FILE = "mockup.html"
```

and the converter will save your generated HTML under that name.

You can also import these variables directly into your scripts:

```python
from config import FIGMA_TOKEN, FILE_KEY, NODE_ID, OUTPUT_FILE
```

---

## 🚀 Running the Converter

Once your token and file key are ready, run:

```bash
python3 figma_to_html.py figd_45y-yourtoken your_file_key
```

This will:

1. Connect to the Figma API using your credentials.
2. Retrieve the selected frame or node (`NODE_ID`).
3. Parse its structure and generate equivalent HTML + CSS.
4. Save the final output as defined in `OUTPUT_FILE`.

To preview the result, open the generated file:

```bash
open output.html   # macOS
# or
start output.html  # Windows
```

---

## 🧠 Main Script – `figma_to_html.py`

This is the **core logic** of the converter.

### How it Works:

1. **Fetches data** from the Figma API using your token and file key.
2. **Parses JSON nodes** for frames, text, rectangles, and shapes.
3. **Converts Figma layers into HTML elements**, preserving:

   * Size and position
   * Font, color, and corner radius
   * Gradients, fills, and strokes
4. **Generates CSS styles dynamically** for accurate design reproduction.
5. **Outputs** a complete HTML file that matches your mockup.

The resulting HTML can be directly opened in a browser to view the visual layout.

---

## 🌐 `figma_to_json.py`

This script connects to Figma’s API and saves your design’s JSON data locally as `output.json`.
It’s useful for verifying that your API token, file key, and node ID are valid, and for understanding the Figma layer structure.

Run:

```bash
python3 figma_to_json.py
```

---

## 🥪 `test_converter.py`

This script is used to **test and validate** the converter’s accuracy.
It is **not redundant** — it complements the main script by ensuring quality and correctness.

### What It Tests:

* Whether all major elements from the Figma design appear in the generated HTML.
* Whether important style attributes (width, height, color, etc.) are mapped correctly.
* Whether layout hierarchy is preserved between Figma’s JSON and the HTML output.

### How to Run:

```bash
pytest test_converter.py
```

If all tests pass ✅, your HTML conversion logic is functioning correctly.

---

## 🧹 Example Outputs

* **`main.html`** → The final HTML and CSS output generated for the provided mockup.
  This file represents the end result of the conversion process — a working HTML structure visually matching the original Figma design.
* **`output.json`** → The raw JSON data fetched from the Figma API that serves as input to the converter.
* **`Trial/` Folder** → A secondary test case used to evaluate the converter on another Figma mockup that included **images and SVGs**.
  It helped confirm that the conversion logic also works with visual assets, not just text or layout elements.

---

## ⚡ Example Workflow

1. Configure your Figma credentials in `config.py`.
2. Run the converter:

   ```bash
   python3 figma_to_html.py figd_45y-yourtoken your_file_key
   ```
3. Open the generated output (default `output.html` or your custom name, e.g. `mockup.html`).
4. (Optional) Run tests:

   ```bash
   pytest test_converter.py
   ```

---

## 📦 Requirements

```
requests>=2.31.0
```

---

## ✨ Summary

This project automates the process of turning Figma designs into front-end HTML/CSS.
It includes scripts for fetching design data, generating HTML, validating results, and testing the converter on different mockups — providing a complete, reproducible workflow from **design to code**.
