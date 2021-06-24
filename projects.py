import os
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from vast_expenses.auth import login_required, session
from vast_expenses.db import get_db


from vast_expenses.__init__ import app

bp = Blueprint('projects', __name__)

UPLOAD_FOLDER = 'vast_expenses/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@bp.route('/')
def index():
    db = get_db()
    projects = db.execute(
        'SELECT p.id, project_name, project_description, user_id, username FROM projects p JOIN users u ON p.user_id = u.id ORDER BY project_name DESC').fetchall()
    return render_template('projects/index.html', projects=projects)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
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
            db.execute('INSERT INTO projects (project_name, project_description, user_id) VALUES (?, ?, ?)',
                       (name, description, g.user['id']))
            db.commit()
            return redirect(url_for('projects.index'))

    return render_template('projects/create.html')


def get_project(id, check_author=True):
    projects = get_db().execute('SELECT p.id, project_name, project_description, user_id, username FROM projects p JOIN users u ON p.user_id = u.id WHERE p.id = ?', (id,)).fetchone()

    if projects is None:
        abort(404, f"Project id {id} doesn't exist.")

    if check_author and projects['user_id'] != g.user['id']:
        abort(403)

    return projects


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    projects = get_project(id)

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
            db.execute(
                'UPDATE projects SET project_name = ?, project_description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('projects.index'))

    return render_template('projects/update.html', projects=projects)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_project(id)
    db = get_db()
    db.execute('DELETE FROM projects WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('projects.index'))


@bp.route('/new_expense', methods=('GET', 'POST'))
@login_required
def new_expense():
    if request.method == 'POST':
        description = request.form['expense_description']
        amount = request.form['expense_amount']
        date = request.form['expense_date']
        file = request.form['file']
        if allowed_file(file):
            receipt = upload_file(file)
        elif not allowed_file(file):
            error = 'This file type is not allowed. Allowed filetypes: PDF, PNG, JPG, JPEG'
        projects = get_project(session['user_id'])
        project_id = projects['id']
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
            return redirect(url_for('expense_summary.index'))

    return render_template('expenses/new_expense.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(bp.config['UPLOAD_FOLDER'], filename))

            return(url_for('download_file', name=filename))
