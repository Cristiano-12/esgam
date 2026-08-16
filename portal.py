from flask import Blueprint, render_template, session, redirect, url_for, flash
from controle import carregar_portal

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/portal")
@portal_bp.route("/portal/<int:student_id>")
def portal(student_id=None):
    if student_id is None:
        student_id = session.get("student_id") or session.get("id")
        role = session.get("role")
        if role == "aluno" and student_id:
            return redirect(url_for("portal.portal", student_id=student_id))
        flash("Sessão de aluno não encontrada. Faça login.", "erro")
        return redirect(url_for("login.login"))

    return render_template(
        "portal.html",
        **carregar_portal(student_id),
    )
