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
    pass


@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(BaseQuestionAdmin):
    pass


@admin.register(LongAnswerQuestion)
class LongAnswerQuestionAdmin(BaseQuestionAdmin):
    pass


@admin.register(ShortAnswerQuestion)
class ShortAnswerChoiceQuestionAdmin(BaseQuestionAdmin):
    pass


# Questions types inlines


class UniqueChoiceQuestionInline(admin.StackedInline):
    model = UniqueChoiceQuestion
    extra = 0


class MultipleChoiceQuestionInline(admin.StackedInline):
    model = MultipleChoiceQuestion
    extra = 0


class LongAnswerQuestionInline(admin.StackedInline):
    model = LongAnswerQuestion
    extra = 0


class ShortAnswerChoiceQuestionInline(admin.StackedInline):
    model = ShortAnswerQuestion
    extra = 0


# Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Quiz admin page."""

    list_display = ("video", "connected_user_only", "show_correct_answers")
    inlines = [
        UniqueChoiceQuestionInline,
        MultipleChoiceQuestionInline,
        LongAnswerQuestionInline,
        ShortAnswerChoiceQuestionInline,
    ]
