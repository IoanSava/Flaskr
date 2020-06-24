from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM posts p JOIN users u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    likes = {}
    for post in posts:
        likes[post['id']] = get_users_who_like_post(post['id'])

    return render_template('blog/index.html', posts=posts, likes=likes)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO posts (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM posts p JOIN users u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


def get_users_who_like_post(id):
    db = get_db()
    users_rows = db.execute(
        'SELECT user_id'
        ' FROM likes l JOIN users u ON u.id = l.user_id'
        ' WHERE post_id = ?', (id,)
    ).fetchall()

    return [list(dict(row).values())[0] for row in users_rows]


@bp.route('/<int:id>')
def get_single_post(id):
    post = get_post(id, False)
    return render_template('blog/single_post.html', post=post)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE posts SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM posts WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:user_id>/<int:post_id>/like', methods=('POST',))
@login_required
def like(user_id, post_id):
    get_post(post_id, False)
    db = get_db()
    db.execute(
        'INSERT INTO likes (user_id, post_id)'
        ' VALUES (?, ?)',
        (user_id, post_id)
    )
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:user_id>/<int:post_id>/unlike', methods=('POST',))
@login_required
def unlike(user_id, post_id):
    get_post(post_id, False)
    db = get_db()
    db.execute(
        'DELETE FROM likes WHERE user_id = ? AND post_id = ?',
        (user_id, post_id)
    )
    db.commit()
    return redirect(url_for('blog.index'))
