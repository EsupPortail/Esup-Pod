"""Forms used in ai_enhancement application."""
from django import forms
from django.utils.translation import ugettext_lazy as _
from tagging.fields import TagField

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.video.models import Video, Discipline

strings = {
    "title": {
        "choose_information_string": _("Choose the title"),
        "initial_information": _("The initial title is loading…"),
        "initial_information_t": _("Your initial title"),
        "ai_information": _("The title proposed by the Aristote AI is loading…"),
        "ai_information_t": _("The title proposed by the Aristote AI"),
    },
    "description": {
        "choose_information_string": _("Choose the description"),
        "initial_information": _("The initial description is loading…"),
        "initial_information_t": _("Your initial description"),
        "ai_information": _("The description proposed by the Aristote AI is loading…"),
        "ai_information_t": _("The description proposed by the Aristote AI"),
    },
    "tags": {
        "choose_information_string": _("Choose the tags"),
        "ai_information": _("The tags proposed by the Aristote AI is loading…"),
    },
    "discipline": {
        "choose_information_string": _("Choose the discipline"),
        "initial_information": _("The initial discipline is loading…"),
        "initial_information_t": _("Your initial discipline"),
        "ai_information": _("The discipline proposed by the Aristote AI is loading…"),
        "ai_information_t": _("The discipline proposed by the Aristote AI"),
    },
}


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
        help_text=_('''
            Please choose a title between 1 and 250 characters.
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
        help_text=_("Please choose a description."),
    )

    tags = TagField(
        help_text=_('''
            Please choose tags for your video.
            Separate tags with spaces, enclose the tags consist of several words in quotation marks.
        '''),
        verbose_name=_("Tags"),
    )

    disciplines = forms.ModelChoiceField(
        label=_("Discipline"),
        queryset=Discipline.objects.all(),
        required=False,
        help_text=_('Please choose the discipline of your video.'),
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
        (
            "choose_tags",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
            {strings['tags']['choose_information_string']}<br>\
            <div id='tags-container'>\
                <div class='row'>\
                    <div class='col' id='tags-informations-text'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'>\
                                {strings['tags']['ai_information']}\
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
            {strings['discipline']['choose_information_string']}<br>\
            <div>\
                <div class='row'>\
                    <div id='initial-version-disciplines' class='col'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                            title='{strings['discipline']['initial_information_t']}'>\
                                {strings['discipline']['initial_information']}\
                        </div>\
                    </div>\
                    <div id='ai-version-disciplines' class='col'>\
                        <div\
                            class='border-d rounded-4 p-3 mb-3 mt-3 blockquote'\
                            title={strings['discipline']['ai_information_t']}>\
                                {strings['discipline']['ai_information']}\
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
