from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
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
    if id_utilizador.isdigit():
        utilizador = Utilizador.query.filter(
            ((Utilizador.username == id_utilizador) | (Utilizador.id == int(id_utilizador))),
            Utilizador.ativo.is_(True)
        ).first()
    else:
        utilizador = Utilizador.query.filter(
            Utilizador.username == id_utilizador,
            Utilizador.ativo.is_(True)
        ).first()

    if not utilizador or not check_password_hash(utilizador.password or "", senha):
        flash("ID ou senha incorretos.", "erro")
        return redirect(url_for("login.login"))

    # 4. Registo na Sessão
    session["id"] = utilizador.id
    session["username"] = utilizador.username
    session["nome"] = utilizador.nome
    session["role"] = utilizador.role

    # 5. Redirecionamento baseado no tipo de perfil
    if utilizador.role in ["direcao", "admin"]:
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
