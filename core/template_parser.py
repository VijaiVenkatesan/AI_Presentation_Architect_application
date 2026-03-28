def detect_layouts(prs):

    layout_map = {
        "title": None,
        "content": None,
        "section": None,
        "blank": None
    }

    for layout in prs.slide_layouts:

        has_title = False
        has_body = False

        for shape in layout.shapes:
            if shape.is_placeholder:
                ptype = str(shape.placeholder_format.type)

                if "TITLE" in ptype:
                    has_title = True
                if "BODY" in ptype:
                    has_body = True

        if has_title and not has_body and not layout_map["title"]:
            layout_map["title"] = layout

        elif has_title and has_body and not layout_map["content"]:
            layout_map["content"] = layout

        elif not has_body and not layout_map["blank"]:
            layout_map["blank"] = layout

    return layout_map
