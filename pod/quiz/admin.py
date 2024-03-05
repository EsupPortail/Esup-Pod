"""Esup-Pod quiz admin."""

from django.contrib import admin

from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    UniqueChoiceQuestion,
)


# Questions types


class BaseQuestionAdmin(admin.ModelAdmin):
    """Base admin configuration for question models."""

    list_display = (
        "id",
        "title",
        "quiz",
        "explanation",
        "start_timestamp",
        "end_timestamp",
    )
    list_display_links = ("id", "title", "quiz")
    list_filter = ("quiz",)


@admin.register(UniqueChoiceQuestion)
class UniqueChoiceQuestionAdmin(BaseQuestionAdmin):
    """Admin configuration for UniqueChoiceQuestion."""


@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(BaseQuestionAdmin):
    """Admin configuration for MultipleChoiceQuestion."""


@admin.register(LongAnswerQuestion)
class LongAnswerQuestionAdmin(BaseQuestionAdmin):
    """Admin configuration for LongAnswerQuestion."""


@admin.register(ShortAnswerQuestion)
class ShortAnswerQuestionAdmin(BaseQuestionAdmin):
    """Admin configuration for ShortAnswerQuestion."""


# Questions types inlines


class UniqueChoiceQuestionInline(admin.StackedInline):
    """Inline configuration for UniqueChoiceQuestion."""

    model = UniqueChoiceQuestion
    extra = 0


class MultipleChoiceQuestionInline(admin.StackedInline):
    """Inline configuration for MultipleChoiceQuestion."""

    model = MultipleChoiceQuestion
    extra = 0


class LongAnswerQuestionInline(admin.StackedInline):
    """Inline configuration for LongAnswerQuestion."""

    model = LongAnswerQuestion
    extra = 0


class ShortAnswerQuestionInline(admin.StackedInline):
    """Inline configuration for ShortAnswerQuestion."""

    model = ShortAnswerQuestion
    extra = 0


# Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for Quiz model."""

    list_display = ("video", "connected_user_only", "show_correct_answers")
    inlines = [
        UniqueChoiceQuestionInline,
        MultipleChoiceQuestionInline,
        LongAnswerQuestionInline,
        ShortAnswerQuestionInline,
    ]
