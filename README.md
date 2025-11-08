# ✨ Figma to HTML Converter

This project converts **Figma designs** into **HTML + CSS** automatically using the Figma REST API.
It connects to Figma, fetches your design structure, and generates pixel-accurate, browser-ready code that reflects your mockup.

---

## Overview

The converter extracts design data from Figma (frames, text, rectangles, gradients, etc.) and transforms them into HTML elements styled with CSS.

---

## 📁 Repository Structure

```
📁 Figma-to-HTML/
│
├── figma_to_html.py        # Main script – converts Figma JSON data to HTML + CSS
├── figma_to_json.py        # 
├── test_converter.py       # 
├── main.html               # Final output – HTML/CSS generated from the given mockup
├── output.json             # (JSON) fetched from Figma API
├── requirements.txt        # 
├── .gitignore              # 
│
└── Trial/                  # Used to test converter on a second mockup
    ├── Trial_2.png         
    ├── trial_2.html        
    └── trial_2_old.html    
```

---

## ⚙️ Installation

### 1️ Clone the Repository

```bash
git clone https://github.com/yourusername/figma-to-html.git
cd figma-to-html
```

### 2️ Install Dependencies

```bash
pip install -r requirements.txt
```

*(This project uses the `requests` library to communicate with the Figma API.)*

---

## Configuration Setup

Create a file named **`config.py`** in the project’s root directory and add these details:

```python
FIGMA_TOKEN = "figd_45y..."     # Figma Personal Access Token
FILE_KEY = "your_file_key"      # File key from Figma file URL
NODE_ID = "0:1"                 # Node or frame ID to export
OUTPUT_FILE = "output.html"     # Output filename (edit this to rename the result)
```

**To rename generated output file** 

simply change the line:

```python
OUTPUT_FILE = "output.html"
```

to:

```python
OUTPUT_FILE = "mockup.html"
```

and the converter will save the generated HTML under that name.

These variables can be directly imported into the scripts:

```python
from config import FIGMA_TOKEN, FILE_KEY, NODE_ID, OUTPUT_FILE
```

---

## Running the Converter

Once the token and file key are ready, run:

```bash
python3 figma_to_html.py figd_45y-yourtoken your_file_key
```

This will:

1. Connect to the Figma API using these credentials.
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

## Main Script – `figma_to_html.py`

This is the **core logic** of the converter.

### How it Works:

1. **Fetches data** from the Figma API using given token and file key.
2. **Parses JSON nodes** for frames, text, rectangles, and shapes.
3. **Converts Figma layers into HTML elements**, preserving:

   * Size and position
   * Font, color, and corner radius
   * Gradients, fills, and strokes
4. **Generates CSS styles dynamically** for accurate design reproduction.
5. **Outputs** a complete HTML file that matches the mockup.

The resulting HTML can be directly opened in a browser to view the visual layout.

---

## `figma_to_json.py`

This script connects to Figma’s API and saves the design’s JSON data locally as `output.json`.
It’s useful for verifying that the API token, file key, and node ID are valid, and for understanding the Figma layer structure.

Run:

```bash
python3 figma_to_json.py
```

---

## `test_converter.py`

This script is used to **test and validate** the converter’s accuracy.

### What It Tests:

* Whether all major elements from the Figma design appear in the generated HTML.
* Whether important style attributes (width, height, color, etc.) are mapped correctly.
* Whether layout hierarchy is preserved between Figma’s JSON and the HTML output.

### How to Run:

```bash
pytest test_converter.py
```

If all tests pass, the HTML conversion logic is functioning correctly.

---

## Example Outputs

* **`main.html`** → The final HTML and CSS output generated for the provided mockup.
  This file represents the end result of the conversion process, a working HTML structure visually matching the original Figma design.
* **`output.json`** → The raw JSON data fetched from the Figma API that serves as input to the converter.
* **`Trial/` Folder** → A secondary test case used to evaluate the converter on another Figma mockup that included **images and SVGs**.

---

## Example Workflow

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

## Requirements

```
requests>=2.31.0
```

---

