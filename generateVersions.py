import json
import os
import csv
import sys
import traceback

def format_traceback_with_locals(exc):
    traceback_segments = traceback.format_exception(exc)
    traceback_string = traceback_segments[0]
    tb = exc.__traceback__
    while tb is not None:
        locals_dict = {k: v for k, v in tb.tb_frame.f_locals.items() if not k.startswith("__")}
        traceback_segment = traceback.format_tb(tb)[0]
        traceback_string += traceback_segment
        traceback_string += "  -> local variables: " + str(locals_dict) + "\n"
        tb = tb.tb_next
    traceback_string += traceback_segments[-1]
    return traceback_string


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


def generate_component(component_type, component_styles, course_data, testing, templates_dir="./LMS Templates"):
    '''
    Generates html for a component within a page
    '''
    template_file = f"./LMS Templates/components/{component_type}-template.txt"
    with open(template_file, encoding="utf-8") as f:
      template = f.read()
      if testing:
        template = template.replace("_qlearn", "_local")
      html = template.format(**course_data, **component_styles)
    return html


def generate_page(course_code, page_type, styles, data, testing):
    """
    Generates a page for a given course_id and page_type ('home' or 'default').
    Returns the fully formatted HTML as a string.
    """
    # Load template
    template_file = f"./LMS Templates/pages/{page_type}-template.txt"
    with open(template_file, encoding="utf-8") as f:
        template_file_contents = f.read()

    # Get list of required components
    components, template = template_file_contents.split("$")
    if testing:
      template = template.replace("_qlearn", "_local")
    components = components.split()

    # Create required components and add to data
    for comp in components:
        data[f'{comp}-component'] = generate_component(comp, styles, data, testing)

    # Format the template with palette and data
    html = template.format(**data, **styles)
    metadata_block = (
      "<!-- ===================== -->\n"
      f"<!-- Style code: {data['style_code']} -->\n"
      f"<!-- Course title: {data['course_title']} -->\n"
      "<!-- ===================== -->\n"
    )

    html = metadata_block + html
    if testing:
      html = testing[0]+html+testing[1]

    # Save page
    filename = f"LMS Templates/{course_code}/{course_code}_{page_type}.html"
    if testing:
      filename = f"LMS Templates/{course_code}/{course_code}_{page_type}_test.html"
    else:
      filename = f"LMS Templates/{course_code}/{course_code}_{page_type}.html"
    save_page(html, filename)

    return html


if __name__ == "__main__":
    testing = False
    test_start = ('<!DOCTYPE html>\n<html lang="en">\n'
                  '<head>\n'
                  '<meta charset="UTF-8">\n'
                  '</head>'
                  '<body>')
    test_end = ("</body>\n"
                "</html>")

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

    config = input("Enter run type:\n"
                   "1. Default\n"
                   "2. All pages Qlearn\n"
                   "3. Single page Qlearn\n"
                   "4. All pages local\n"
                   "5. Single Page Local\n>> ")

    if int(config) > 3:
      testing = (test_start, test_end)

    if config in "35":
      course_ids = [input("Enter course ID")]
      pages = [input("Enter page")]
    else:
      course_ids = [x for x in sitedata.keys()]
      pages = ['home', 'default', 'class', 'unit', 'sample']

    for course_id in course_ids:
        data = sitedata[course_id]
        course_styles = palettes[data["style_code"]]
        styles_flat = flatten_dict(course_styles)
        code = data["style_code"]

        for page in pages:
          try:
            generate_page(code, page, styles_flat, data, testing)
            print(f"Successfully generated {page} page for {data["course_title"]} course.")
          except Exception as e:
            sys.exit(format_traceback_with_locals(e))

