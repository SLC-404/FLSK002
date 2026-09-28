from flask import render_template
from flask_login import current_user, login_required

from app.main import bp
from app.utils.decorators import permission_required


@bp.get("/")
def index():
    """Public page: anyone can see it."""
    return render_template("main/index.html")


@bp.get("/dashboard")
@login_required                          # only logged-in users (like middleware('auth'))
@permission_required("view-dashboard")   # and their role must have the permission
def dashboard():
    return render_template("main/dashboard.html", user=current_user)
