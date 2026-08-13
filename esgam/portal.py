from flask import Blueprint, render_template
from controle import carregar_portal

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/portal/<int:student_id>")
def portal(student_id):
    return render_template(
        "portal.html",
        **carregar_portal(student_id)
    )