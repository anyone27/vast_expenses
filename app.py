import os
import sqlite3
from flask import Flask, flash, g, redirect, render_template, request, url_for, session
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import functools

# initiate app
app = Flask(__name__)

UPLOAD_FOLDER = './static/uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app.secret_key = 'dev',
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# initiate database


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('expenses.db')
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


# register and login functions

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f"User {username} is already registered. "

        if error is None:
            db.execute('INSERT INTO users (username, hash) VALUES (?, ?)',
                       (username, generate_password_hash(password)))
            db.commit()
            return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        users = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if users is None:
            error = 'Incorrect username.'
        elif not check_password_hash(users['hash'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = users['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view


# if logged in will show dashboard, else will show landing page
@app.route('/')
def index():
    if g.user is None:
        return render_template('index.html')
    else:
        db = get_db()
        projects = db.execute(
            'SELECT p.id, project_name, project_description, user_id, username FROM projects p JOIN users u ON p.user_id = u.id ORDER BY p.id').fetchall()
        return render_template('dashboard.html', projects=projects)

# projects function


def get_project(project_id, check_author=True):
    projects = get_db().execute(
        'SELECT user_id, project_name, project_description FROM projects WHERE id = ?', [project_id]).fetchone()

    if projects is None:
        abort(404, f"Project id {project_id} doesn't exist.")

        if check_author and projects['user_id'] != g.user['id']:
            abort(403)

            return projects


@app.route('/new_project', methods=('GET', 'POST'))
@login_required
def new_project():
    if request.method == 'POST':
        name = request.form['project_name']
        description = request.form['project_description']
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('INSERT INTO projects (user_id, project_name, project_description) VALUES (?, ?, ?)',
                       (g.user['id'], name, description))
            db.commit()
            return redirect('/')

    return render_template('new_project.html')


@ app.route('/<int:project_id>/update_project', methods=('GET', 'POST'))
@ login_required
def update_project(project_id):
    get_project(project_id)
    projects = get_db().execute(
        'SELECT id, user_id, project_name, project_description FROM projects WHERE id = ?', [project_id]).fetchone()

    if request.method == 'POST':
        name = request.form['project_name']
        description = request.form['project_description']
        error = None

        if not name:
            error = 'Project name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('UPDATE projects SET project_name = ?, project_description = ? WHERE id = ?',
                       (name, description, project_id))
            db.commit()
            return redirect('/')

    return render_template('update_project.html', projects=projects)


@ app.route('/<int:project_id>/delete_project', methods=('POST',))
@ login_required
def delete_project(project_id):
    get_project(project_id)
    db = get_db()
    db.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    db.commit()
    return redirect('/')

# expenses functions


def get_expenses(project_id):
    expenses = get_db().execute(
        'SELECT id, project_id, expense_description, expense_amount, expense_date, receipt FROM expenses WHERE project_id = ?', (project_id,)).fetchall()

    if expenses is None:
        abort(404, "There are currently no expenses for this project.")

    return expenses


@ app.route('/<int:project_id>/expense_summary')
@login_required
def expense_summary(project_id):
    expenses = get_expenses(project_id)
    return render_template('expense_summary.html', project_id=project_id, expenses=expenses)


@ app.route('/<int:project_id>/new_expense', methods=('GET', 'POST'))
@ login_required
def new_expense(project_id):
    if request.method == 'POST':
        description = request.form['expense_description']
        amount = request.form['expense_amount']
        date = request.form['expense_date']
        # TODO check allowed file extensions
        # if allowed_file(request.files['file']):
        receipt = upload_file(request.files['file'])
        # elif not allowed_file(request.files['file']):
        #     error = 'This file type is not allowed. Allowed filetypes: PDF, PNG, JPG, JPEG'
        projects = get_project(project_id)
        error = None

        if not description:
            error = 'Description is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('INSERT INTO expenses (expense_description, expense_amount, expense_date, receipt, project_id) VALUES (?, ?, ?, ?, ?)',
                       (description, amount, date, receipt, project_id))
            db.commit()
            return redirect(url_for('expense_summary', project_id=project_id))

    return render_template('new_expense.html')


@ app.route('/<int:expense_id>/update_expense', methods=('GET', 'POST'))
@ login_required
def update_expense(expense_id):
    expenses = get_db().execute(
        'SELECT id, project_id, expense_description, expense_amount, expense_date, receipt FROM expenses WHERE id = ?', (expense_id,)).fetchone()

    if request.method == 'POST':
        description = request.form['expense_description']
        amount = request.form['expense_amount']
        date = request.form['expense_date']
        receipt = upload_file(request.files['file'])
        project_id = expenses['project_id']
        error = None

        if not description:
            error = 'Description is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE expenses SET expense_description = ?, expense_amount = ?, expense_date = ?, receipt = ? WHERE id = ?', (
                    description, amount, date, receipt, expense_id)
            )
            db.commit()
            return redirect(url_for('expense_summary', project_id))

    return render_template('update_expense.html', expenses=expenses)


@app.route('/<int:expense_id>/delete_expense', methods=('POST',))
@login_required
def delete_expense(expense_id):
    db = get_db()
    db.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    db.commit()
    return redirect('/')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(file_upload):
    # check if the post request has the file part
    if 'file' not in request.files:
        return 'there is no file in form'
    file = file_upload
    filename = secure_filename(file.filename)
    with open(filename, 'rb') as file:
        receipt = file.read()

    return receipt
