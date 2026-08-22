from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Aluno

gestao_bp = Blueprint("gestao", __name__)

SITUACOES = [
    "Aprovado",
    "Reprovado",
    "Reprovado por disciplina",
    "Reprovado por comportamento",
    "Transferido",
    "Anulado",
]
AVISO_MAX = 80


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Por favor, efetue login.", "erro")
            return redirect(url_for("login.login"))
        return f(*args, **kwargs)
    return decorated


def _formatar_nome(nome):
    nome = " ".join(str(nome or "").split())
    if not nome:
        return ""
    return " ".join(p.capitalize() for p in nome.split(" "))


@gestao_bp.route("/admin/gestao-alunos", methods=["GET"])
@login_required
def gestao_alunos():
    pesquisa = request.args.get("pesquisa", "").strip()
    alunos = []
    aluno_edicao = None

    if pesquisa:
        aluno_edicao = Aluno.query.filter_by(
            codigo_estudante=pesquisa, deleted_at=None
        ).first()
        if not aluno_edicao:
            aluno_edicao = Aluno.query.filter(
                Aluno.deleted_at.is_(None),
                Aluno.codigo_estudante.ilike(pesquisa),
            ).first()
        if not aluno_edicao and pesquisa.isdigit():
            aluno_edicao = Aluno.query.filter_by(
                id=int(pesquisa), deleted_at=None
            ).first()
        if not aluno_edicao:
            alunos = (
                Aluno.query.filter(
                    Aluno.deleted_at.is_(None),
                    (Aluno.codigo_estudante.ilike(f"%{pesquisa}%"))
                    | (Aluno.nome.ilike(f"%{pesquisa}%")),
                )
                .order_by(Aluno.nome.asc())
                .limit(50)
                .all()
            )
            if len(alunos) == 1:
                aluno_edicao = alunos[0]
        else:
            alunos = [aluno_edicao]

    return render_template(
        "gestao.html",
        alunos=alunos,
        aluno_edicao=aluno_edicao,
        pesquisa=pesquisa,
        situacoes=SITUACOES,
        aviso_max=AVISO_MAX,
    )


@gestao_bp.route("/admin/editar-aluno/<int:aluno_id>", methods=["GET"])
@login_required
def editar_aluno(aluno_id):
    aluno_edicao = Aluno.query.filter_by(id=aluno_id, deleted_at=None).first_or_404()
    return render_template(
        "gestao.html",
        alunos=[aluno_edicao],
        aluno_edicao=aluno_edicao,
        pesquisa=aluno_edicao.codigo_estudante or "",
        situacoes=SITUACOES,
        aviso_max=AVISO_MAX,
    )


@gestao_bp.route("/admin/guardar-alteracoes/<int:aluno_id>", methods=["POST"])
@login_required
def guardar_alteracoes(aluno_id):
    aluno = Aluno.query.filter_by(id=aluno_id, deleted_at=None).first_or_404()

    nome = _formatar_nome(request.form.get("nome", ""))
    if not nome:
        flash("O nome do aluno não pode estar vazio.", "danger")
        return redirect(url_for("gestao.editar_aluno", aluno_id=aluno.id))

    situacao = (request.form.get("situacao") or "").strip()
    if situacao and situacao not in SITUACOES:
        flash("Situação inválida.", "danger")
        return redirect(url_for("gestao.editar_aluno", aluno_id=aluno.id))

    aviso = (request.form.get("aviso") or "").strip()
    if len(aviso) > AVISO_MAX:
        aviso = aviso[:AVISO_MAX]

    aluno.nome = nome
    aluno.situacao = situacao or None
    aluno.aviso = aviso or None

    try:
        db.session.commit()
        flash("Dados atualizados com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao guardar as alterações.", "danger")
        return redirect(url_for("gestao.editar_aluno", aluno_id=aluno.id))

    return redirect(url_for("gestao.editar_aluno", aluno_id=aluno.id))


@gestao_bp.route("/admin/eliminar-aluno/<int:aluno_id>", methods=["POST"])
@login_required
def eliminar_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    aluno.deleted_at = datetime.now(timezone.utc)
    aluno.motivo_eliminacao = "Eliminado pelo administrador"
    try:
        db.session.commit()
        flash("Aluno enviado para a lixeira.", "warning")
    except Exception:
        db.session.rollback()
        flash("Erro ao mover o aluno para a lixeira.", "danger")
    return redirect(url_for("gestao.gestao_alunos"))