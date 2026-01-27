import json
import os
import csv


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

def generate_component(component_type, component_styles, course_data, templates_dir="./LMS Templates"):
    template_file = os.path.join(templates_dir, f"components/{component_type}-template.txt")
    with open(template_file, encoding="utf-8") as f:
      template = f.read()
      html = template.format(**course_data, **component_styles)
    return html


def generate_page(course_id, page_type, styles, data, templates_dir="./LMS Templates"):
    """
    Generates a page for a given course_id and page_type ('home' or 'default').
    Returns the fully formatted HTML as a string.
    """
    # Load template
    template_file = os.path.join(templates_dir, f"pages/{page_type}-template.txt")
    with open(template_file, encoding="utf-8") as f:
        template = f.read()

    # Create standard components
    data["navbar-component"] = generate_component("navbar", styles, data, templates_dir)
    data["cards-component"] = generate_component("cards", styles, data, templates_dir)

    # Format the template with palette and site data
    html = template.format(**data, **styles)

    # Save page
    filename = f"LMS Templates/{course_id}/{course_id}_{page_type}.html"
    save_page(html, filename)

    return html


# -------------------------
# Main script
# -------------------------
if __name__ == "__main__":

    # Load palettes and sitedata once
    sitedata = {}
    with open('data/coursedata.csv', 'r',  encoding='utf-8-sig') as f:
      dict_reader = csv.DictReader(f)
      headers = dict_reader.fieldnames
      for line in dict_reader:
        course_id = line["course_id"]
        sitedata[course_id] = {}
        for header in headers[1:]:
          sitedata[course_id][header] = line[header]

    with open(os.path.join("css/palettes.json"), encoding="utf-8") as f:
        palettes = json.load(f)

    course_ids = [x for x in sitedata.keys()]

    for course_id in course_ids:
        data = sitedata[course_id]
        course_styles = palettes[data["style_code"]]
        styles_flat = flatten_dict(course_styles)

        code = data["style_code"]

        # Generate homepage
        html_home = generate_page(code, "home", styles_flat , data)

        # # Generate default page
        html_default = generate_page(code, "default", styles_flat , data)
        #
        # Generate class page
        html_class = generate_page(code, "class", styles_flat , data)
        #
        # # Generate unit page
        html_unit = generate_page(code, "unit", styles_flat , data)

    # print("All pages generated successfully.")
