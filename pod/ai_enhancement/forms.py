"""Forms used in playlist application."""
from django import forms
from django.utils.translation import ugettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.video.models import Video


strings = {
    "title": {
        "choose_information_string": _("Choose the title"),
        "initial_information": _("The initial title is loading..."),
        "initial_information_t": _("Your initial title"),
        "ai_information": _("The title proposed by the Aristote AI is loading..."),
        "ai_information_t": _("The title proposed by the Aristote AI"),
    },
    "description": {
        "choose_information_string": _("Choose the description"),
        "initial_information": _("The initial description is loading..."),
        "initial_information_t": _("Your initial description"),
        "ai_information": _("The description proposed by the Aristote AI is loading..."),
        "ai_information_t": _("The description proposed by the Aristote AI"),
    },
}


class AIEnrichmentChoice(forms.ModelForm):
    """Form class for choosing the title of a video with the AI enrichment."""

    class Meta:
        """Meta class."""

        model = Video
        fields = [
            "title",
            "description",
        ]

    title = forms.CharField(
        label=_("Title"),
        widget=forms.TextInput(
            attrs={
                "aria-describedby": "id_titleHelp",
            },
        ),
        help_text=_('''
            Please choose a title between 1 and 250 characters.
            You can also let Aristote choose for you press the button above.
        '''),
    )

    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={
                "aria-describedby": "id_descriptionHelp",
            },
        ),
        required=False,
        help_text=_("Please choose a description. This description is empty by default."),
    )

    fieldsets = [
        (
            "choose_title",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
                    {strings['title']['choose_information_string']}<br>\
                    <div>\
                        <div class='row'>\
                            <div id='initial-version-title' class='col'>\
                                <div\
                                    class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                    title='{strings['title']['initial_information_t']}'>\
                                        {strings['title']['initial_information']}\
                                </div>\
                            </div>\
                            <div id='ai-version-title' class='col'>\
                                <div\
                                    class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                    title={strings['title']['ai_information_t']}>\
                                        {strings['title']['ai_information']}\
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
                {strings['description']['choose_information_string']}<br>\
                <div>\
                    <div class='row'>\
                        <div id='initial-version-description' class='col'>\
                            <div\
                                class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                title='{strings['description']['initial_information_t']}'>\
                                    {strings['description']['initial_information']}\
                            </div>\
                        </div>\
                        <div id='ai-version-description' class='col'>\
                            <div\
                                class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                                title={strings['description']['ai_information_t']}>\
                                    {strings['description']['ai_information']}\
                            </div>\
                        </div>\
                    </div>\
                </div>",
                "fields": ["description"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs):
        """Init method."""
        super(AIEnrichmentChoice, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
