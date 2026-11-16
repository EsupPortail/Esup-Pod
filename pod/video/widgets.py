"""Esup-Pod Video custom Widgets."""

from django import forms


class HelpedRadioSelect(forms.RadioSelect):
    """Radio Select with help on each option."""

    def __init__(self, *args, help_texts=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_texts = help_texts or {}

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Overrides the default create_option to add help_texts"""
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value in self.help_texts:
            option["help_text"] = self.help_texts[value]
        return option
