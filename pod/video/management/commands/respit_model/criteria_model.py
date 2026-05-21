from datetime import datetime, date
from django.conf import settings

RESPIT_MODEL_PARAMETER = getattr(settings, "RESPIT_MODEL_PARAMETER", [])


def to_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    raise TypeError(f"Unexpected date type : {type(v)}")


# A dictionary that maps each parameter to its corresponding comparison lambda
# Signature : lambda param_value, criterion_value -> bool
PARAM_MATCHERS = {
    "id": lambda v, c: v == c,
    "type_id_video": lambda v, c: v in c,
    "view_count": lambda v, c: v >= c,
    "view_count_year": lambda v, c: v >= c,
    "nb_fav": lambda v, c: v >= c,
    "nb_comment": lambda v, c: v >= c,
    "duration_video": lambda v, c: v >= c,
    "nb_channel": lambda v, c: v >= c,
    "nb_theme": lambda v, c: v >= c,
    "channel_list": lambda v, c: bool(set(v) & set(c)),
    "theme_list": lambda v, c: bool(set(v) & set(c)),
    "days_on_platform": lambda v, c: v >= c,
    "category_list": lambda v, c: bool(set(v) & set(c)),
    "date_added": lambda v, c: to_date(v) >= to_date(c),
    "date_delete": lambda v, c: to_date(v) >= to_date(c),
    "title": lambda v, c: c.lower() in v.lower(),
    "description": lambda v, c: c.lower() in v.lower(),
    "owner_video": lambda v, c: c.lower() == v.lower(),
    "owner_video_additional": lambda v, c: bool(set(v) & set(c)),
    "is_draft": lambda v, c: c.lower() == v.lower(),
    "is_restricted": lambda v, c: c.lower() == v.lower(),
}

# Fallback for any parameter missing from the dictionary
DEFAULT_MATCHER = PARAM_MATCHERS["id"]


def match_criterion(param_name: str, param_value, criterion_value, dry_mode: bool = True) -> bool:
    if dry_mode:
        print("\tCheck criterion ", param_name, " = ", param_value, " compared with ", criterion_value)
    if param_value is None:
        return False
    matcher = PARAM_MATCHERS.get(param_name, DEFAULT_MATCHER)
    if dry_mode:
        if matcher(param_value, criterion_value) :
            print("\t\tReturn True")
        else :
            print("\t\tReturn False")
    return matcher(param_value, criterion_value)


def match_criteria_row(parameters: dict, criteria: dict, dry_mode: bool = True) -> bool:
    if dry_mode:
        print("Check criteria row")
    return all(
        match_criterion(name, parameters.get(name), value)
        for name, value in criteria.items()
    )


def calcul(parameters: dict, dry_mode: bool = True) -> int:
    if dry_mode:
        print("Compute delete respit for video ", parameters["id"], " - ", parameters["title"])
    for row in RESPIT_MODEL_PARAMETER:
        if match_criteria_row(parameters, row["criteria"], dry_mode):
            date_added = parameters["date_added"]
            date_delete = parameters["date_delete"]
            age_years = row["age"]

            try:
                new_limit = date_added.replace(year=date_added.year + age_years)
            except ValueError:
                new_limit = date_added.replace(year=date_added.year + age_years, day=28)

            delta = (to_date(new_limit) - to_date(date_delete)).days
            return max(0, delta)

    return 0
