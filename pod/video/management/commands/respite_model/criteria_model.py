"""
Esup-Pod - Criteria Respite model.

This model allows for the calculation of an additional delay based on various criteria.
"""

from datetime import datetime, date
from django.conf import settings

RESPITE_MODEL_PARAMETER = getattr(settings, "RESPITE_MODEL_PARAMETER", [])


def to_date(v):
    """Convert a datetime or date to a date object."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    raise TypeError(f"Unexpected date type : {type(v)}")


# Signature (bool): lambda v=real_value, c=criterion_value: condition
MATCHERS = {
    "IS_IN": lambda v, c: v in c,
    "CONTAINS": lambda v, c: c.lower() in v.lower(),
    "AT_LEAST": lambda v, c: v >= c,
    "INTERSECT": lambda v, c: bool(set(v) & set(c)),
    "IS_AFTER": lambda v, c: to_date(v) >= to_date(c),
    "STR_EQUALS": lambda v, c: c.lower() == v.lower(),
    "EQUALS": lambda v, c: c == v,
}

# A dictionary that maps each parameter to its corresponding comparison lambda
PARAM_MATCHERS = {
    "id": "IS_IN",
    "title": "CONTAINS",
    "view_count": "AT_LEAST",
    "view_count_year": "AT_LEAST",
    "is_draft": "EQUALS",
    "is_restricted": "EQUALS",
    "date_added": "IS_AFTER",
    "days_on_platform": "AT_LEAST",
    "description": "CONTAINS",
    "channels.id": "INTERSECT",
    "channels#len": "AT_LEAST",
    "nb_fav": "AT_LEAST",
    "nb_comment": "AT_LEAST",
    "duration": "AT_LEAST",
    "disciplines.title": "INTERSECT",
    "type.id": "IS_IN",
    "themes.id": "INTERSECT",
    "themes#len": "AT_LEAST",
    "owner": "STR_EQUALS",
    "additional_owners.username": "INTERSECT",
    "categories.id": "INTERSECT",
}


def match_criterion(
    param_name: str, param_value, criterion_value, dry_mode: bool = True
) -> bool:
    """Compare one parameter value against a single matching criterion."""
    matcher_type = PARAM_MATCHERS.get(param_name, "EQUALS")
    if param_value is None:
        return False
    matcher = MATCHERS[matcher_type]
    if dry_mode:
        print(
            "\tCheck criterion “%s”=“%s” %s “%s”\t=> %s"
            % (
                param_name,
                param_value,
                matcher_type,
                criterion_value,
                matcher(param_value, criterion_value),
            )
        )
    return matcher(param_value, criterion_value)


def match_criteria_row(video_data: dict, criteria: dict, dry_mode: bool = True) -> bool:
    """Check whether all criteria in a row match the provided video data."""
    for name, value in criteria.items():
        if "." in name:
            param = name.split(".")
            video_attr = video_data[param[0]]
            if isinstance(video_attr, list):
                # Convert a list of object to a list of attributes
                # i.e "channels.id" will become a list of channel ids if channels is a list
                real_value = [getattr(attr, param[1]) for attr in video_attr]
            else:
                real_value = getattr(video_attr, param[1])
        elif "#" in name:
            param = name.split("#")
            video_attr = video_data[param[0]]
            if param[1] == "len":
                real_value = len(video_attr)
        else:
            real_value = video_data[name]

        if not match_criterion(name, real_value, value, dry_mode):
            return False
    return True


def calcul(video_data: dict, dry_mode: bool = True) -> int:
    """Compute the respite delay in days based on a matched criteria rule."""
    if dry_mode:
        print(
            "Compute delete respite for video %s - %s"
            % (video_data["id"], video_data["title"])
        )
    if len(RESPITE_MODEL_PARAMETER) == 0:
        print("RESPITE_MODEL_PARAMETER is empty. Setup your criteria first.")
    row_num = 0
    for row in RESPITE_MODEL_PARAMETER:
        row_num += 1
        if dry_mode:
            print(" * Processing criteria set #%s..." % row_num)
        if match_criteria_row(video_data, row["criteria"], dry_mode):
            date_added = video_data["date_added"]
            date_delete = video_data["date_delete"]
            age_years = row["age"]

            try:
                new_limit = date_added.replace(year=date_added.year + age_years)
            except ValueError:
                new_limit = date_added.replace(year=date_added.year + age_years, day=28)

            delta = (to_date(new_limit) - to_date(date_delete)).days
            return max(0, delta)

    return 0
