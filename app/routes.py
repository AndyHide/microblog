from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g
from flask_babel import _, get_locale
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from random import shuffle

from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, IngredientForm, RecipeForm, IngredientInRecipeForm
from app.models import User, Post, Ingredient, Recipe, RecipeIngredients
from app.classes import Mealplan


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))


@app.route('/ingredients', methods=['GET', 'POST'])
@login_required
def ingredients():
    form = IngredientForm()
    if form.validate_on_submit():
        ingredient = Ingredient(name=form.name.data)
        db.session.add(ingredient)
        db.session.commit()
        flash(_('Your ingredient added!'))
        return redirect(url_for('ingredients'))
    page = request.args.get('page', 1, type=int)
    ingredients = Ingredient.query.order_by(Ingredient.name).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('ingredients', page=ingredients.next_num) \
        if ingredients.has_next else None
    prev_url = url_for('ingredients', page=ingredients.prev_num) \
        if ingredients.has_prev else None
    return render_template('ingredients.html', title=_('Ingredients'), form=form,
                           ingredients=ingredients.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/recipes', methods=['GET', 'POST'])
@login_required
def recipes():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(name=form.name.data)
        db.session.add(recipe)
        db.session.commit()
        flash(_('Your recipe added!'))
        return redirect(url_for('recipe', name=recipe.name))
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.name).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipes', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('recipes', page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template('recipes.html', title=_('Recipes'), form=form,
                           recipes=recipes.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/recipe/<name>', methods=['GET', 'POST'])
@login_required
def recipe(name):
    recipe = Recipe.query.filter_by(name=name).first_or_404()
    form = IngredientInRecipeForm(isBreakfast=recipe.isBreakfast, isLunch=recipe.isLunch, isDinner=recipe.isDinner)
    if form.validate_on_submit():
        if form.name.data:
            ingredient = Ingredient.query.filter_by(name=form.name.data).first()
            if ingredient is None:
                flash(_('Ingredient is not found'))
                return redirect(url_for('recipe', name=name))
            if ingredient in recipe.find_ingredients():
                flash(_('Ingredient is already in this recipe'))
                return redirect(url_for('recipe', name=name))
            else:
                recipe.ingredients.append(ingredient)
        recipe.isBreakfast = form.isBreakfast.data
        recipe.isLunch = form.isLunch.data
        recipe.isDinner = form.isDinner.data
        db.session.commit()
        flash(_('Изменения сохранены!'))
        return redirect(url_for('recipe', name=name))
    page = request.args.get('page', 1, type=int)
    ingredients = recipe.find_ingredients().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('recipe', name=recipe.name, page=ingredients.next_num) \
        if ingredients.has_next else None
    prev_url = url_for('recipe', name=recipe.name, page=ingredients.prev_num) \
        if ingredients.has_prev else None
    return render_template('recipe.html', form=form, recipe=recipe, ingredients=ingredients.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/delete_recipe/<name>', methods=['GET', 'POST'])
@login_required
def delete_recipe(name):
    recipe = Recipe.query.filter_by(name=name).first()
    db.session.delete(recipe)
    db.session.commit()
    flash(_('Recipe was deleted'))
    return redirect(url_for('recipes'))


@app.route('/ingredient/<name>')
@login_required
def ingredient(name):
    ingredient = Ingredient.query.filter_by(name=name).first_or_404()
    page = request.args.get('page', 1, type=int)
    recipes = ingredient.find_recipes().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('ingredient', name=ingredient.name, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('ingredient', name=ingredient.name, page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template('ingredient.html', ingredient=ingredient, recipes=recipes.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/delete_ingredient/<ingredient>')
@login_required
def delete_ingredient(ingredient):
    target_ingredient = Ingredient.query.filter_by(name=ingredient).first_or_404()
    db.session.delete(target_ingredient)
    db.session.commit()
    flash(_('Ingredient deleted'))
    return redirect(url_for('ingredients'))


@app.route('/delete_ingredient_from_recipe/<ingredient>/<recipe>')
@login_required
def delete_ingredient_from_recipe(ingredient, recipe):
    target_recipe = Recipe.query.filter_by(name=recipe).first_or_404()
    target_ingredient = Ingredient.query.filter_by(name=ingredient).first_or_404()
    db.session.query(RecipeIngredients).filter(RecipeIngredients.c.ingredient_id == target_ingredient.id and
                                               RecipeIngredients.c.recipe_id == target_recipe.id).delete(
        synchronize_session=False)
    db.session.commit()
    return redirect(url_for('recipe', name=recipe))


@app.route('/mealplan', methods=['GET', 'POST'])
@login_required
def mealplan():
    mealplan = Mealplan()
    breakfast_recipes = Recipe.query.filter_by(isBreakfast=True).all()
    lunch_recipes = Recipe.query.filter_by(isLunch=True).all()
    dinner_recipes = Recipe.query.filter_by(isDinner=True).all()

    shuffle(breakfast_recipes)
    shuffle(lunch_recipes)
    shuffle(dinner_recipes)

    breakfast_recipes = breakfast_recipes[:5]
    lunch_recipes = lunch_recipes[:5]
    dinner_recipes = dinner_recipes[:5]

    """print(breakfast_recipes)"""

    for day in mealplan.days:
        day.breakfast = breakfast_recipes.pop()
        day.lunch = lunch_recipes.pop()
        day.dinner = dinner_recipes.pop()

    """for day in mealplan.days:
        print(day.name)
        print(day.breakfast)
        print(day.lunch)
        print(day.dinner)"""

    return render_template('mealplan.html', mealplan=mealplan)