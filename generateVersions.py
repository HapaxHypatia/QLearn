import json
import os

def flatten_dict(d, parent_key="", sep="_"):
    """
    Recursively flattens a nested dictionary.
    Example: {"page":{"background":"#fff"}} => {"page_background":"#fff"}
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def save_page(html, filename):
  """Write the HTML string to a file."""
  with open(filename, "w", encoding="utf-8") as f:
    f.write(html)

def generate_component(component_type, palettes, sitedata, templates_dir="./LMS Templates"):
    template_file = os.path.join(templates_dir, f"components/{component_type}-template.txt")
    with open(template_file, encoding="utf-8") as f:
      template = f.read()
      html = template.format(**sitedata, **palettes)
    return html


def generate_page(course_id, page_type, palettes, sitedata, templates_dir="./LMS Templates"):
    """
    Generates a page for a given course_id and page_type ('home' or 'default').
    Returns the fully formatted HTML as a string.
    """
    # Load template
    template_file = os.path.join(templates_dir, f"pages/{page_type}-template.txt")
    with open(template_file, encoding="utf-8") as f:
        template = f.read()

    palette_flat = flatten_dict(palettes[course_id])
    data_flat = flatten_dict(sitedata[course_id])

    # Create standard components
    data_flat["navbar-component"] = generate_component("navbar", palette_flat, data_flat, templates_dir)
    data_flat["cards-component"] = generate_component("cards", palette_flat, data_flat, templates_dir)

    # Format the template with flattened palette and site data
    html = template.format(**data_flat, **palette_flat)

    # Save page
    filename = f"LMS Templates/{course_id}/{course_id}_{page_type}.html"
    save_page(html, filename)

    return html


# -------------------------
# Main script
# -------------------------
if __name__ == "__main__":

    # Load palettes and sitedata once
    with open(os.path.join("css/palettes.json"), encoding="utf-8") as f:
        palettes = json.load(f)
    with open(os.path.join("data/sitedata.json"), encoding="utf-8") as f:
        sitedata = json.load(f)

    # List of course IDs to generate
    course_ids = ["07", "08", "09", "10", "11", "12"]

    for course_id in course_ids:

        # Generate homepage
        html_home = generate_page(course_id, "home", palettes, sitedata)

        # Generate default page
        html_default = generate_page(course_id, "default", palettes, sitedata)

        # Generate class page
        html_class = generate_page(course_id, "class", palettes, sitedata)

        # # Generate unit page
        # html_unit = generate_page(course_id, "unit", palettes, sitedata)

    print("All pages generated successfully.")
