from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length

from app.models import User, Ingredient, Recipe


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class IngredientForm(FlaskForm):
    name = StringField(_l('Добавить новый ингредиент:'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

    def validate_name(self, name):
        ingredient = Ingredient.query.filter_by(name=name.data).first()
        if ingredient is not None:
            raise ValidationError(_('Этот ингредиент уже есть в базе.'))


class IngredientInRecipeForm(FlaskForm):
    isBreakfast = BooleanField(_l('Завтрак'))
    isLunch = BooleanField(_l('Обед'))
    isDinner = BooleanField(_l('Ужин'))
    name = StringField(_l('Добавить новый ингредиент:'))
    submit = SubmitField(_l('Submit'))


class RecipeForm(FlaskForm):
    name = StringField(_l('Here you can add new recipe'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

    def validate_name(self, name):
        recipe = Recipe.query.filter_by(name=name.data).first()
        if recipe is not None:
            raise ValidationError(_('This recipe is already present.'))