from datetime import datetime, date
from os.path import basename
from django.conf import settings
from pod.video.models import Video


RESPIT_MODEL_PARAMETERS = getattr(
    settings,
    "RESPIT_MODEL_PARAMETERS",
    {
        "respit_criteria_parameter": [],
        "archiving_criteria_parameter": {
            "excluded_title_terms": [],
            "excluded_discipline_terms": [],
        },
    }
)


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
    """Check a criterion"""
    if dry_mode:
        print("\tCheck criterion ", param_name, " = ", param_value, " compared with ", criterion_value)

    if param_value is None:
        return False
    matcher = PARAM_MATCHERS.get(param_name, DEFAULT_MATCHER)
    if dry_mode:
        if matcher(param_value, criterion_value):
            print("\t\tReturn True")
        else:
            print("\t\tReturn False")
    return matcher(param_value, criterion_value)


def match_criteria_row(parameters: dict, criteria: dict, dry_mode: bool = True) -> bool:
    """Check a criteria row"""
    if dry_mode:
        print("Check criteria row")
    return all(
        match_criterion(name, parameters.get(name), value)
        for name, value in criteria.items()
    )


def calcul(parameters: dict, dry_mode: bool = True) -> int:
    """Calculate the number of days to add to date_delete"""
    if dry_mode:
        print(
            "Compute delete respit for video ",
            parameters["id"],
            " - ",
            parameters["title"],
        )
    for row in RESPIT_MODEL_PARAMETERS.get("respit_criteria_parameter", []):
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


def can_video_be_archived(vid: Video):
    """Checks if a video can be archived"""
    archiving_criteria = RESPIT_MODEL_PARAMETERS.get("archiving_criteria_parameter", {})

    attribute_scores = archiving_criteria.get("attribute_scores", {})
    minimum_expected_score = archiving_criteria.get("minimum_expected_score", 0)
    excluded_title_terms = archiving_criteria.get("excluded_title_terms", [])
    excluded_discipline_terms = archiving_criteria.get("excluded_discipline_terms", [])

    score = 0

    title = (getattr(vid, "title", "") or "").strip()
    title_lower = title.lower()
    video_field = getattr(vid, "video", None)
    filename = basename(getattr(video_field, "name", "") or "")
    is_title_excluded = any(term in title_lower for term in excluded_title_terms)

    if title and filename and title_lower != filename.lower() and not is_title_excluded:
        score += attribute_scores.get("title", 0)

    description = (getattr(vid, "description", "") or "").strip()
    if description:
        score += attribute_scores.get("description", 0)

    disciplines = getattr(vid, "discipline", None)
    if disciplines is not None:
        has_valid_discipline = any(
            (getattr(discipline, "slug", "") not in excluded_discipline_terms)
            for discipline in disciplines.all()
        )
        if has_valid_discipline:
            score += attribute_scores.get("discipline", 0)

    tags = getattr(vid, "tags", None)
    if tags is not None and tags.count() > 0:
        score += attribute_scores.get("tags", 0)

    if getattr(vid, "date_evt", None):
        score += attribute_scores.get("date_evt", 0)

    print("Metadata score completion = %s." % score)
    return score >= minimum_expected_score
