from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Utilizador  # Import do ORM e do Modelo

login_bp = Blueprint("login", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    # 1. Requisição GET: apenas exibe a página de login
    if request.method == "GET":
        return render_template("login.html")

    # 2. Requisição POST: captura os dados do formulário
    id_utilizador = request.form.get("studentID", "").strip()
    senha = request.form.get("password", "").strip()

    if not id_utilizador or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("login.login"))

    # 3. Consulta ORM limpa e segura
    utilizador = Utilizador.query.filter_by(
        id_escolar=id_utilizador,
        senha=senha
    ).first()

    if not utilizador:
        flash("ID ou senha incorretos.", "erro")
        return redirect(url_for("login.login"))

    # 4. Registo na Sessão
    session["id"] = utilizador.id
    session["id_escolar"] = utilizador.id_escolar
    session["nome"] = utilizador.nome
    session["tipo"] = utilizador.tipo

    # 5. Redirecionamento baseado no tipo de perfil
    if utilizador.tipo in ["direcao", "admin"]:
        # Flag necessária para liberar o decorator @login_required no controle.py
        session["admin_logged_in"] = True
        return redirect(url_for("controle.central_verificacao"))

    return redirect(url_for("portal.portal"))


@login_bp.route("/logout")
def logout():
    """Termina a sessão do utilizador."""
    session.clear()
    flash("Sessão encerrada com sucesso.", "sucesso")
    return redirect(url_for("login.login"))