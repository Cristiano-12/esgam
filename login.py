from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import Utilizador, Aluno

login_bp = Blueprint("login", __name__)

SENHA_PORTAL_ALUNO = "ESGAM000"


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    id_utilizador = request.form.get("studentID", "").strip()
    senha = request.form.get("password", "").strip()

    if not id_utilizador or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("login.login"))

    # 1) Admin / direção (tabela Utilizador)
    if id_utilizador.isdigit():
        utilizador = Utilizador.query.filter(
            ((Utilizador.username == id_utilizador) | (Utilizador.id == int(id_utilizador))),
            Utilizador.ativo.is_(True),
        ).first()
    else:
        utilizador = Utilizador.query.filter(
            Utilizador.username == id_utilizador,
            Utilizador.ativo.is_(True),
        ).first()

    if utilizador and check_password_hash(utilizador.password or "", senha):
        session.clear()
        session["id"] = utilizador.id
        session["username"] = utilizador.username
        session["nome"] = utilizador.nome
        session["role"] = utilizador.role

        if utilizador.role in ("direcao", "admin"):
            session["admin_logged_in"] = True
            return redirect(url_for("controle.central_verificacao"))

        # Outros roles de utilizador — se tiverem portal, adaptar aqui
        return redirect(url_for("controle.central_verificacao"))

    # 2) Aluno (código ESG-… ou ID interno) — senha fixa ESGAM000
    aluno = Aluno.query.filter(
        Aluno.deleted_at.is_(None),
        Aluno.codigo_estudante == id_utilizador,
    ).first()

    if not aluno:
        aluno = Aluno.query.filter(
            Aluno.deleted_at.is_(None),
            Aluno.codigo_estudante.ilike(id_utilizador),
        ).first()

    if not aluno and id_utilizador.isdigit():
        aluno = Aluno.query.filter_by(id=int(id_utilizador), deleted_at=None).first()

    if aluno and senha == SENHA_PORTAL_ALUNO:
        session.clear()
        session["id"] = aluno.id
        session["student_id"] = aluno.id
        session["username"] = aluno.codigo_estudante or str(aluno.id)
        session["nome"] = aluno.nome
        session["role"] = "aluno"
        return redirect(url_for("portal.portal", student_id=aluno.id))

    flash("ID ou senha incorretos.", "erro")
    return redirect(url_for("login.login"))


@login_bp.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "sucesso")
    return redirect(url_for("login.login"))
