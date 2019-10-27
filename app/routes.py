from app import app

from flask import render_template

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/admin')
def admin_page():
    return render_template("admin.html")