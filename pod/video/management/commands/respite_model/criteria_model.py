"""
Esup-Pod - Criteria Respite model.

This model allows for the calculation of an additional delay based on various criteria.
"""

import logging
from os.path import basename

from django.conf import settings

from pod.main.utils import to_date
from pod.video.models import Video

DEBUG = getattr(settings, "DEBUG", True)

RESPITE_MODEL_PARAMETERS = getattr(
    settings,
    "RESPITE_MODEL_PARAMETERS",
    {
        "respite_criteria_parameter": [],
        "archiving_criteria_parameter": {
            "excluded_title_terms": [],
            "excluded_discipline_terms": [],
        },
    },
)


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

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)


def match_criterion(
    param_name: str, param_value, criterion_value, dry_mode: bool = True
) -> bool:
    """Compare one parameter value against a single matching criterion."""
    matcher_type = PARAM_MATCHERS.get(param_name, "EQUALS")
    if param_value is None:
        return False
    matcher = MATCHERS[matcher_type]
    if dry_mode:
        logger.info(
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
        logger.info(
            "Compute delete respite for video %s - %s"
            % (video_data["id"], video_data["title"])
        )
    respite_criteria = RESPITE_MODEL_PARAMETERS.get("respite_criteria_parameter", [])
    if len(respite_criteria) == 0:
        logger.info("respite_criteria_parameter is empty. Setup your criteria first.")
    row_num = 0
    for row in respite_criteria:
        row_num += 1
        if dry_mode:
            logger.info(" * Processing criteria set #%s..." % row_num)
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


def can_video_be_archived(vid: Video):
    """Checks if a video can be archived"""
    archiving_criteria = RESPITE_MODEL_PARAMETERS.get("archiving_criteria_parameter", {})

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

    logger.debug("[Video %s] Metadata score completion = %s." % (vid.id, score))
    return score >= minimum_expected_score
