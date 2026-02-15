import json
import os
import csv
import sys
import traceback
import re

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


def extract_style_code(html: str) -> str:
    """
    Extract style_code from embedded metadata comment.
    """

    match = re.search(r'<!--\s*Style code:\s*(.*?)\s*-->', html)
    if not match:
        raise ValueError("No style code metadata found in HTML.")

    return match.group(1).strip()


def convert_html_to_template_auto(html: str, palettes: dict) -> tuple:
    """
    Extract style code from metadata block,
    convert styled HTML to template placeholders,
    and remove metadata block from template output.

    Returns:
    (style_code, converted_html)
    """

    style_code = extract_style_code(html)

    flat_palette = flatten_dict(palettes[style_code])

    converted_html = convert_styled_html_to_template(
    html,
    flat_palette
    )

    # Remove entire metadata block from template output
    converted_html = re.sub(
    r'<!--\s*=====================.*?=====================\s*-->',
    '',
    converted_html,
    flags=re.DOTALL
    )

    return style_code, converted_html


def convert_styled_html_to_template(html: str, flat_palette: dict) -> str:
    """
    Replace hard-coded palette colour values with template placeholders.
    """

    updated_html = html

    # Sort by length to prevent short hex collisions (#000 inside #000000)
    for key, value in sorted(flat_palette.items(), key=lambda x: -len(str(x[1]))):
      if not isinstance(value, str):
        continue

      colour = value.lower()
      placeholder = "{" + key + "}"

      pattern = re.compile(re.escape(colour), re.IGNORECASE)
      updated_html = pattern.sub(placeholder, updated_html)
    html = "$"+html
    return updated_html


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


def parse_admin_command(cmd):
  """
  Parse a one-line admin command for the LMS generator.

  Format:
      generate|<environment>|<course_id OR all>|<page_name OR all>
      convert|<path_to_file>

  Returns:
      dict with keys:
          mode: "generate" or "convert"
          environment: "qlearn" or "local" or None
          course_scope: "single" or "all" or None
          page_scope: "single" or "all" or None
          course_id: str or None
          page_name: str or None
          input_path: str or None
  """
  parts = cmd.strip().split("|")
  config = {
    "mode": None,
    "environment": None,
    "course_scope": None,
    "page_scope": None,
    "course_id": None,
    "page_name": None,
    "input_path": None
  }

  if not parts:
    raise ValueError("Empty command string")

  mode = parts[0].lower()
  if mode not in ("generate", "convert"):
    raise ValueError(f"Invalid mode '{mode}'. Must be 'generate' or 'convert'")
  config["mode"] = mode

  if mode == "convert":
    if len(parts) != 2:
      raise ValueError("Convert mode requires exactly one argument: path_to_file")
    config["input_path"] = parts[1].strip()
    return config

  # mode == "generate"
  if len(parts) != 4:
    raise ValueError("Generate mode requires exactly 4 parts: generate|env|course_id/all|page_name/all")

  env, course_input, page_input = parts[1:4]
  env = env.lower()
  if env not in ("qlearn", "local"):
    raise ValueError(f"Invalid environment '{env}'. Must be 'qlearn' or 'local'")
  config["environment"] = env

  # Determine course scope
  if course_input.lower() == "all":
    config["course_scope"] = "all"
    config["course_id"] = None
  else:
    config["course_scope"] = "single"
    config["course_id"] = course_input.strip()

  # Determine page scope
  if page_input.lower() == "all":
    config["page_scope"] = "all"
    config["page_name"] = None
  else:
    config["page_scope"] = "single"
    config["page_name"] = page_input.strip()

  return config


def get_run_configuration():
  """
  Prompts user for configuration or parses a full admin command.
  The first input handles both interactive mode and one-line admin mode.
  """
  raw = input(
    "Enter run type or paste admin command:\n"
    "1. Generate pages\n"
    "2. Convert styled page to template\n"
    "(Or paste a full admin command like 'generate|local|16820|home')\n>> "
  ).strip()

  # --- Check if it looks like a full admin command ---
  if "|" in raw:
    return parse_admin_command(raw)

  # --- Interactive guided mode ---
  if raw not in ("1", "2"):
    print("Invalid choice. Defaulting to Generate pages.")
    raw = "1"

  if raw == "2":
    return {"mode": "convert"}

  # Generate pages mode
  env_choice = input(
    "\nSelect environment:\n"
    "1. Qlearn-ready\n"
    "2. Local test\n>> "
  ).strip()
  environment = "local" if env_choice == "2" else "qlearn"

  course_choice = input(
    "\nGenerate for:\n"
    "1. All courses\n"
    "2. Single course\n>> "
  ).strip()
  course_scope = "single" if course_choice == "2" else "all"

  page_choice = input(
    "\nGenerate:\n"
    "1. All pages\n"
    "2. Single page\n>> "
  ).strip()
  page_scope = "single" if page_choice == "2" else "all"

  config = {
    "mode": "generate",
    "environment": environment,
    "course_scope": course_scope,
    "page_scope": page_scope
  }

  if course_scope == "single":
    config["course_id"] = input("Enter course ID:\n>> ").strip()

  if page_scope == "single":
    config["page_name"] = input("Enter page name:\n>> ").strip()

  return config

if __name__ == "__main__":
    # Local testing tags
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

    config=get_run_configuration()

    if config["mode"] == "convert":
      input_path = config.get("input_path") or input("Enter path:\n>> ")
      template_name = config.get("template_name") or input("Template name:\n>> ")

      with open(input_path, encoding="utf-8") as f:
        styled_html = f.read()

      style_code, template_html = convert_html_to_template_auto(
        styled_html,
        palettes
      )

      output_path = f"LMS Templates/pages/{template_name}.txt"

      with open(output_path, "w", encoding="utf-8") as f:
        f.write(template_html)

      print(f"✔ Converted successfully ({style_code})")
      sys.exit()

    testing = (test_start, test_end) if config["environment"] == "local" else False

    if config["course_scope"] == "single":
      course_ids = [config["course_id"]]
    else:
      course_ids = list(sitedata.keys())

    if config["page_scope"] == "single":
      pages = [config["page_name"]]
    else:
      filenames = os.listdir("LMS Templates/pages")
      pages = [x[:-13] for x in filenames if x.endswith("-template.txt")]


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

