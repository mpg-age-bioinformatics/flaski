from wtforms import Form, FloatField, validators

class InputForm(Form):
    A = FloatField(
        label='title', default="my plot title",
        validators=[validators.InputRequired()])