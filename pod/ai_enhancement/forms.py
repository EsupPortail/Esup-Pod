"""Forms used in ai_enhancement application."""

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from tagulous.models import TagField

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.video.models import Video, Discipline

AI_ENHANCEMENT_FIELDS_HELP_TEXT = getattr(
    settings,
    "AI_ENHANCEMENT_FIELDS_HELP_TEXT",
    {
        "title": {
            "choose_information_string": _("Choose the title."),
            "initial_information": _("The initial title is loading…"),
            "initial_information_t": _("Your initial title."),
            "ai_information": _("The title proposed by the Aristote AI is loading…"),
            "ai_information_t": _("The title proposed by the Aristote AI."),
        },
        "description": {
            "choose_information_string": _("Choose the description."),
            "initial_information": _("The initial description is loading…"),
            "initial_information_t": _("Your initial description."),
            "ai_information": _(
                "The description proposed by the Aristote AI is loading…"
            ),
            "ai_information_t": _("The description proposed by the Aristote AI."),
        },
        "tags": {
            "choose_information_string": _("Choose the tags."),
            "ai_information": _("The tags proposed by the Aristote AI is loading…"),
        },
        "discipline": {
            "choose_information_string": _("Choose the discipline."),
            "initial_information": _("The initial discipline is loading…"),
            "initial_information_t": _("Your initial discipline."),
            "ai_information": _("The discipline proposed by the Aristote AI is loading…"),
            "ai_information_t": _("The discipline proposed by the Aristote AI."),
        },
    },
)
AI_ENHANCEMENT_CGU_URL = getattr(
    settings,
    "AI_ENHANCEMENT_CGU_URL",
    "",
)


class AIEnhancementChoice(forms.ModelForm):
    """Form class for choosing the title of a video with the AI enhancement."""

    class Meta:
        """Meta class."""

        model = Video
        fields = [
            "title",
            "description",
            "tags",
            "discipline",
        ]

    title = forms.CharField(
        label=_("Title"),
        widget=forms.TextInput(
            attrs={
                "aria-describedby": "id_titleHelp",
            },
        ),
        help_text=_("Please choose a title between 1 and %(max)s characters.")
        % {"max": 250},
    )

    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={
                "aria-describedby": "id_descriptionHelp",
            },
        ),
        required=False,
        help_text=_("Please choose a description."),
    )

    tags = TagField(
        help_text=_(
            """
            Please choose tags for your video.
            Separate tags with spaces, enclose the tags consist of several words in quotation marks.
        """
        ),
        verbose_name=_("Tags"),
    )

    disciplines = forms.ModelChoiceField(
        label=_("Discipline"),
        queryset=Discipline.objects.all(),
        required=False,
        help_text=_("Please choose the discipline of your video."),
    )

    fieldsets = [
        (
            "choose_title",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
                    {AI_ENHANCEMENT_FIELDS_HELP_TEXT['title']['choose_information_string']}<br>\
                    <div>\
                        <div class='row'>\
                            <div id='initial-version-title' class='col'>\
                                <div\
                                    class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                    title='{AI_ENHANCEMENT_FIELDS_HELP_TEXT['title']['initial_information_t']}'>\
                                        {AI_ENHANCEMENT_FIELDS_HELP_TEXT['title']['initial_information']}\
                                </div>\
                            </div>\
                            <div id='ai-version-title' class='col'>\
                                <div\
                                    class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                    title={AI_ENHANCEMENT_FIELDS_HELP_TEXT['title']['ai_information_t']}>\
                                        {AI_ENHANCEMENT_FIELDS_HELP_TEXT['title']['ai_information']}\
                                </div>\
                            </div>\
                        </div>\
                    </div>",
                "fields": ["title"],
            },
        ),
        (
            "choose_description",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
                {AI_ENHANCEMENT_FIELDS_HELP_TEXT['description']['choose_information_string']}<br>\
                <div>\
                    <div class='row'>\
                        <div id='initial-version-description' class='col'>\
                            <div\
                                class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                title='{AI_ENHANCEMENT_FIELDS_HELP_TEXT['description']['initial_information_t']}'>\
                                    {AI_ENHANCEMENT_FIELDS_HELP_TEXT['description']['initial_information']}\
                            </div>\
                        </div>\
                        <div id='ai-version-description' class='col'>\
                            <div\
                                class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                title={AI_ENHANCEMENT_FIELDS_HELP_TEXT['description']['ai_information_t']}>\
                                    {AI_ENHANCEMENT_FIELDS_HELP_TEXT['description']['ai_information']}\
                            </div>\
                        </div>\
                    </div>\
                </div>",
                "fields": ["description"],
            },
        ),
        (
            "choose_tags",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
            {AI_ENHANCEMENT_FIELDS_HELP_TEXT['tags']['choose_information_string']}<br>\
            <div id='tags-container'>\
                <div class='row'>\
                    <div class='col' id='tags-informations-text'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'>\
                                {AI_ENHANCEMENT_FIELDS_HELP_TEXT['tags']['ai_information']}\
                        </div>\
                    </div>\
                </div>\
            </div>",
                "fields": ["tags"],
            },
        ),
        (
            "choose_disciplines",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
            {AI_ENHANCEMENT_FIELDS_HELP_TEXT['discipline']['choose_information_string']}<br>\
            <div>\
                <div class='row'>\
                    <div id='initial-version-disciplines' class='col'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                            title='{AI_ENHANCEMENT_FIELDS_HELP_TEXT['discipline']['initial_information_t']}'>\
                                {AI_ENHANCEMENT_FIELDS_HELP_TEXT['discipline']['initial_information']}\
                        </div>\
                    </div>\
                    <div id='ai-version-disciplines' class='col'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                            title={AI_ENHANCEMENT_FIELDS_HELP_TEXT['discipline']['ai_information_t']}>\
                                {AI_ENHANCEMENT_FIELDS_HELP_TEXT['discipline']['ai_information']}\
                        </div>\
                    </div>\
                </div>\
            </div>",
                "fields": ["disciplines"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs):
        """Init method."""
        super(AIEnhancementChoice, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class NotifyUserThirdPartyServicesForm(forms.Form):
    """Form to notify user about third party services."""

    agree = forms.BooleanField(
        label=_("I agree to use third-party services"),
        help_text=_(
            "Please check this box if you agree to use a third-party service to improve this video."
        ),
        widget=forms.CheckboxInput(
            attrs={
                "aria-describedby": "id_agreeHelp",
            },
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(NotifyUserThirdPartyServicesForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
        if AI_ENHANCEMENT_CGU_URL != "" and self.fields.get("agree"):
            to_know_more = '<a href="%s" target="_blank" >' % AI_ENHANCEMENT_CGU_URL
            to_know_more += (
                '  <i class="bi bi-box-arrow-up-right" aria-hidden="true"></i>&nbsp;'
            )
            to_know_more += _("For more information.")
            to_know_more += "</a>"
            self.fields["agree"].help_text += "&nbsp;" + to_know_more


class NotifyUserDeleteEnhancementForm(forms.Form):
    """Form to notify user before delete an enhancement."""

    confirm = forms.BooleanField(
        label=_("I want to delete this enhancement"),
        help_text=_("Please check this box if you want to delete this enhance."),
        widget=forms.CheckboxInput(
            attrs={
                "aria-describedby": "id_confirmHelp",
            },
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(NotifyUserDeleteEnhancementForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
        if AI_ENHANCEMENT_CGU_URL != "" and self.fields.get("agree"):
            to_know_more = '<a href="%s" target="_blank" >' % AI_ENHANCEMENT_CGU_URL
            to_know_more += (
                '  <i class="bi bi-box-arrow-up-right" aria-hidden="true"></i>&nbsp;'
            )
            to_know_more += _("For more information.")
            to_know_more += "</a>"
            self.fields["agree"].help_text += "&nbsp;" + to_know_more
