"""Esup-Pod quiz app."""

from django.apps import AppConfig
from django.db import connection
from django.db.models.signals import pre_migrate, post_migrate
from django.utils.translation import gettext_lazy as _
from django.db import transaction

QUESTION_DATA = {
    "single_choice": [],
    "multiple_choice": [],
    "short_answer": [],
}

EXECUTE_QUIZ_MIGRATIONS = False


class QuizConfig(AppConfig):
    """Quiz config app."""

    name = "pod.quiz"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Quiz")

    def ready(self) -> None:
        pre_migrate.connect(self.check_quiz_migrations, sender=self)
        pre_migrate.connect(self.save_previous_questions, sender=self)
        pre_migrate.connect(self.remove_previous_questions, sender=self)
        post_migrate.connect(self.send_previous_questions, sender=self)

    def execute_query_mapping(self, query, mapping_dict, question_type) -> None:
        """
        Execute the given query and populate the mapping dictionary with the results.

        Args:
            query (str): The given query to execute
            mapping_dict (dict): The dictionary.
        """
        from pod.quiz.models import Quiz
        import json

        try:
            with connection.cursor() as c:
                c.execute(query)
                results = c.fetchall()
                for question_result in results:
                    quiz = Quiz.objects.get(id=question_result[6])
                    question_data = question_result[5]
                    if question_type in {"single_choice", "multiple_choice"}:
                        question_data = json.loads(question_data)
                    mapping_dict.append(
                        {
                            "question_type": question_type,
                            "quiz": quiz,
                            "title": question_result[1],
                            "explanation": question_result[2],
                            "start_timestamp": question_result[3],
                            "end_timestamp": question_result[4],
                            "question_data": question_data,
                        }
                    )
        except Exception as e:
            print(e)
            pass

    def check_quiz_migrations(self, sender, **kwargs) -> None:
        """Save previous questions from different tables."""
        from pod.quiz.models import (
            MultipleChoiceQuestion,
            ShortAnswerQuestion,
            SingleChoiceQuestion,
        )

        QUESTION_MODELS = [
            MultipleChoiceQuestion,
            ShortAnswerQuestion,
            SingleChoiceQuestion,
        ]

        global EXECUTE_QUIZ_MIGRATIONS
        quiz_exist = self.check_quiz_exist()
        if not quiz_exist:
            return

        for model in QUESTION_MODELS:
            query = f"SELECT id FROM {model.objects.model._meta.db_table} LIMIT 1"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result and isinstance(result[0], int):
                        EXECUTE_QUIZ_MIGRATIONS = True
                        break
            except Exception as e:
                print(e)
                pass

    def check_quiz_exist(self) -> bool:
        """Check if quiz exist in database."""
        from pod.quiz.models import Quiz

        try:
            quiz = Quiz.objects.first()
            if not quiz:
                return False
            return True
        except Exception:
            return False

    def save_previous_questions(self, sender, **kwargs) -> None:
        """Save previous questions from different tables."""
        from pod.quiz.models import (
            MultipleChoiceQuestion,
            ShortAnswerQuestion,
            SingleChoiceQuestion,
        )

        if not EXECUTE_QUIZ_MIGRATIONS:
            return

        queries = {
            "single_choice": f"SELECT id, title, explanation, start_timestamp, end_timestamp, choices, quiz_id FROM {SingleChoiceQuestion.objects.model._meta.db_table}",
            "multiple_choice": f"SELECT id, title, explanation, start_timestamp, end_timestamp, choices, quiz_id FROM {MultipleChoiceQuestion.objects.model._meta.db_table}",
            "short_answer": f"SELECT id, title, explanation, start_timestamp, end_timestamp, answer, quiz_id FROM {ShortAnswerQuestion.objects.model._meta.db_table}",
        }
        for question_type, query in queries.items():
            self.execute_query_mapping(query, QUESTION_DATA[question_type], question_type)

    def remove_previous_questions(self, sender, **kwargs) -> None:
        """Remove previous questions from different tables."""
        from pod.quiz.models import (
            MultipleChoiceQuestion,
            ShortAnswerQuestion,
            SingleChoiceQuestion,
        )

        if not EXECUTE_QUIZ_MIGRATIONS:
            return

        QUESTION_MODELS = [
            MultipleChoiceQuestion,
            ShortAnswerQuestion,
            SingleChoiceQuestion,
        ]

        for model in QUESTION_MODELS:
            model.objects.all().delete()
        print("--- Previous questions deleted successfuly ---")

    @transaction.atomic
    def send_previous_questions(self, sender, **kwargs) -> None:
        """Insert previously saved questions from QUESTION_DATA."""
        from pod.quiz.views import create_question

        if not EXECUTE_QUIZ_MIGRATIONS:
            return

        for question_type, questions in QUESTION_DATA.items():
            for question in questions:
                print(question["question_data"])
                create_question(
                    question_type=question_type,
                    quiz=question["quiz"],
                    title=question["title"],
                    explanation=question["explanation"],
                    start_timestamp=question["start_timestamp"],
                    end_timestamp=question["end_timestamp"],
                    question_data=question["question_data"],
                )
        print("--- New questions saved successfuly ---")
