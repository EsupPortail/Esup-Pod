
def add_placeholder_and_asterisk(fields):
    """Add placeholder and asterisk to specified fields."""
    for fieldName in fields:
        myField = fields[fieldName]
        classname = myField.widget.__class__.__name__
        if classname == "PasswordInput" or classname == "TextInput":
            myField.widget.attrs["placeholder"] = myField.label

        if classname == "CheckboxInput":
            bsClass = "form-check-input"
        elif classname == "Select":
            bsClass = "form-select"
        else:
            bsClass = "form-control"

        if myField.required:
            myField.label = mark_safe(
                '%s <span class="required_star">*</span>' % myField.label
            )
            myField.widget.attrs["required"] = ""
            myField.widget.attrs["class"] = "required " + bsClass
        else:
            myField.widget.attrs["class"] = bsClass

    return fields
