from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from vast_expenses.auth import login_required
from vast_expenses.db import get_db

bp = Blueprint('expenses', __name__)


@bp.route('/')
def index():
    db = get_db()
    expenses = db.execute(
        'SELECT p.id, expense_description, expense_amount, expense_date, user_id, username FROM expenses p JOIN users u ON p.user_id = u.id ORDER BY expense_date DESC').fetchall()
    return render_template('expenses/expense_summary.html', expenses=expenses)


def get_expenses(id, check_author=True):
    expenses = get_db().execute('SELECT p.id, expense_description, expense_amount, expense_date, receipt, user_id, username FROM expenses p JOIN users u ON p.user_id = u.id WHERE p.id = ?', (id,)).fetchone()

    if expenses is None:
        abort(404, f"expense id {id} doesn't exist.")

    if check_author and expenses['user_id'] != g.user['id']:
        abort(403)

    return expenses


@bp.route('/<int:id>/update_expense', methods=('GET', 'POST'))
@login_required
def update(id):
    expenses = get_expenses(id)

    if request.method == 'POST':
        description = request.form['expense_description']
        amount = request.form['expense_amount']
        error = None

        if not description:
            error = 'Description is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE expenses SET expense_description = ?, expense_amount = ?'
                ' WHERE id = ?',
                (description, amount, id)
            )
            db.commit()
            return redirect(url_for('expenses.expense_summary'))

    return render_template('expenses/update_expense.html', expenses=expenses)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_expenses(id)
    db = get_db()
    db.execute('DELETE FROM expenses WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('expenses.expense_summary'))
