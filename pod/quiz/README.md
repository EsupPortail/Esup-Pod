# How add a new type of question?

1. Add a model who inherits from `Question`, the new model must incluse:
    - An attribute (choices in JSON, or another...)
    - `Meta` class
    - `clean(self)` method
    - `__str__(self)` method
    - `get_type(self)` method
    - `get_answer(self)` method
    - `get_question_form(self, data=None)` method

2. Admin
    - Register your new class in `admin.py`
    - Add an inline configuration for your new class

3. Form
    - Add a new form in `forms.py`

4. `utils.py` file
    - Update `get_quiz_questions()` function

5. `views.py` file
Update these functions:
    - `update_questions`
    - `create_questions`
    - `calculate_score`
    - `get_initial_data`

6. Javascript
    - Add new function: `handleYourNewTypeOfQuestionQuestion(questionForm)`
    - Update: `handleQuestionType` function
    - Add new function `handleYourNewTypeOfQuestionSubmission`
    - Update `manage_form_submission` function
