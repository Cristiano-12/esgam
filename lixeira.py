from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Aluno, Classe, Grupo, Turma

lixeira_bp = Blueprint("lixeira", __name__, url_prefix="/admin/lixeira")
DIAS_RETENCAO = 10


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Por favor, efetue login.", "erro")
            return redirect(url_for("login.login"))
        return f(*args, **kwargs)
    return decorated


def calcular_dias_restantes(data_eliminacao):
    if not data_eliminacao:
        return 0, "—"
    data_expiracao = data_eliminacao + timedelta(days=DIAS_RETENCAO)
    dias = (data_expiracao - datetime.now()).days
    return max(0, dias), data_expiracao.strftime("%d/%m/%Y %H:%M")


def _fmt(dt):
    return dt.strftime("%d/%m/%Y") if dt else "—"


@lixeira_bp.route("/", methods=["GET"])
@login_required
def index():
    pesquisa = request.args.get("pesquisa", "").strip().lower()
    categoria = request.args.get("categoria", "tudo")

    classes_eliminadas = []
    for c in Classe.query.filter(Classe.deleted_at.isnot(None)).order_by(Classe.deleted_at.desc()).all():
        dias_rest, data_final = calcular_dias_restantes(c.deleted_at)
        classes_eliminadas.append({
            "id": c.id,
            "nome": c.numero,
            "total_grupos": Grupo.query.filter_by(classe_id=c.id).count(),
            "total_turmas": Turma.query.filter_by(classe_id=c.id).count(),
            "total_alunos": Aluno.query.filter_by(classe_id=c.id).count(),
            "data_eliminacao": _fmt(c.deleted_at),
            "data_final_eliminacao": data_final,
            "motivo_eliminacao": c.motivo_eliminacao,
            "dias_restantes": dias_rest,
        })

    grupos_eliminados = []
    for g in Grupo.query.filter(Grupo.deleted_at.isnot(None)).order_by(Grupo.deleted_at.desc()).all():
        dias_rest, data_final = calcular_dias_restantes(g.deleted_at)
        grupos_eliminados.append({
            "id": g.id,
            "classe": g.classe_rel.numero if g.classe_rel else "—",
            "nome": g.nome,
            "total_turmas": Turma.query.filter_by(grupo_id=g.id).count(),
            "total_alunos": Aluno.query.filter_by(grupo_id=g.id).count(),
            "data_eliminacao": _fmt(g.deleted_at),
            "data_final_eliminacao": data_final,
            "motivo_eliminacao": g.motivo_eliminacao,
            "dias_restantes": dias_rest,
        })

    turmas_eliminadas = []
    for tu in Turma.query.filter(Turma.deleted_at.isnot(None)).order_by(Turma.deleted_at.desc()).all():
        dias_rest, data_final = calcular_dias_restantes(tu.deleted_at)
        alunos_t = Aluno.query.filter_by(turma_id=tu.id).all()
        turmas_eliminadas.append({
            "id": tu.id,
            "classe": tu.classe_rel.numero if tu.classe_rel else "—",
            "grupo": tu.grupo_rel.nome if tu.grupo_rel else "—",
            "nome": tu.nome,
            "total_alunos": len(alunos_t),
            "alunos": [{"id": a.codigo_estudante or a.id, "nome": a.nome} for a in alunos_t],
            "data_eliminacao": _fmt(tu.deleted_at),
            "data_final_eliminacao": data_final,
            "motivo_eliminacao": tu.motivo_eliminacao,
            "dias_restantes": dias_rest,
        })

    alunos_eliminados = []
    for a in Aluno.query.filter(Aluno.deleted_at.isnot(None)).order_by(Aluno.deleted_at.desc()).all():
        dias_rest, data_final = calcular_dias_restantes(a.deleted_at)
        alunos_eliminados.append({
            "id": a.codigo_estudante or str(a.id),
            "nome": a.nome,
            "classe": a.classe_rel.numero if a.classe_rel else (a.classe_nome or "—"),
            "grupo": a.grupo_rel.nome if a.grupo_rel else (a.grupo_nome or "—"),
            "turma": a.turma_rel.nome if a.turma_rel else (a.turma_nome or "—"),
            "data_eliminacao": _fmt(a.deleted_at),
            "data_final_eliminacao": data_final,
            "motivo_eliminacao": a.motivo_eliminacao,
            "dias_restantes": dias_rest,
        })

    if pesquisa:
        def match(*vals):
            return any(pesquisa in str(v or "").lower() for v in vals)
        classes_eliminadas = [x for x in classes_eliminadas if match(x["nome"], x.get("motivo_eliminacao"))]
        grupos_eliminados = [x for x in grupos_eliminados if match(x["nome"], x["classe"])]
        turmas_eliminadas = [x for x in turmas_eliminadas if match(x["nome"], x["classe"], x["grupo"])]
        alunos_eliminados = [x for x in alunos_eliminados if match(x["nome"], x["id"], x["classe"])]

    show_c = categoria in ("tudo", "classes")
    show_g = categoria in ("tudo", "grupos")
    show_t = categoria in ("tudo", "turmas")
    show_a = categoria in ("tudo", "alunos")

    return render_template(
        "lixeira.html",
        classes_eliminadas=classes_eliminadas if show_c else [],
        grupos_eliminados=grupos_eliminados if show_g else [],
        turmas_eliminadas=turmas_eliminadas if show_t else [],
        alunos_eliminados=alunos_eliminados if show_a else [],
        total_alunos_lixeira=Aluno.query.filter(Aluno.deleted_at.isnot(None)).count(),
        total_turmas_lixeira=Turma.query.filter(Turma.deleted_at.isnot(None)).count(),
        total_grupos_lixeira=Grupo.query.filter(Grupo.deleted_at.isnot(None)).count(),
        total_classes_lixeira=Classe.query.filter(Classe.deleted_at.isnot(None)).count(),
        pesquisa=request.args.get("pesquisa", ""),
        categoria_selecionada=categoria,
    )


@lixeira_bp.route("/restaurar/classe/<int:id>", methods=["POST"])
@login_required
def restaurar_classe(id):
    c = Classe.query.get_or_404(id)
    c.deleted_at = None
    c.motivo_eliminacao = None
    for g in Grupo.query.filter_by(classe_id=c.id).all():
        g.deleted_at = None
        g.motivo_eliminacao = None
    for tu in Turma.query.filter_by(classe_id=c.id).all():
        tu.deleted_at = None
        tu.motivo_eliminacao = None
    for a in Aluno.query.filter_by(classe_id=c.id).all():
        a.deleted_at = None
        a.motivo_eliminacao = None
    db.session.commit()
    flash("Classe e registos associados restaurados. Acesso ao portal reposto.", "success")
    return redirect(url_for("lixeira.index"))


@lixeira_bp.route("/restaurar/grupo/<int:id>", methods=["POST"])
@login_required
def restaurar_grupo(id):
    g = Grupo.query.get_or_404(id)
    g.deleted_at = None
    g.motivo_eliminacao = None
    for tu in Turma.query.filter_by(grupo_id=g.id).all():
        tu.deleted_at = None
        tu.motivo_eliminacao = None
    for a in Aluno.query.filter_by(grupo_id=g.id).all():
        a.deleted_at = None
        a.motivo_eliminacao = None
    db.session.commit()
    flash("Grupo restaurado. Acesso ao portal reposto.", "success")
    return redirect(url_for("lixeira.index"))


@lixeira_bp.route("/restaurar/turma/<int:id>", methods=["POST"])
@login_required
def restaurar_turma(id):
    tu = Turma.query.get_or_404(id)
    tu.deleted_at = None
    tu.motivo_eliminacao = None
    for a in Aluno.query.filter_by(turma_id=tu.id).all():
        a.deleted_at = None
        a.motivo_eliminacao = None
    db.session.commit()
    flash("Turma restaurada. Acesso ao portal reposto.", "success")
    return redirect(url_for("lixeira.index"))


@lixeira_bp.route("/restaurar/aluno/<path:id>", methods=["POST"])
@login_required
def restaurar_aluno(id):
    """id = código ESG ou id numérico (como no HTML da lixeira)."""
    aluno = Aluno.query.filter_by(codigo_estudante=str(id)).first()
    if not aluno and str(id).isdigit():
        aluno = Aluno.query.get(int(id))
    if not aluno:
        flash("Aluno não encontrado na lixeira.", "erro")
        return redirect(url_for("lixeira.index"))
    aluno.deleted_at = None
    aluno.motivo_eliminacao = None
    db.session.commit()
    flash(f"Aluno {aluno.codigo_estudante or aluno.id} restaurado. Pode aceder ao portal.", "success")
    return redirect(url_for("lixeira.index"))


@lixeira_bp.route("/restaurar-tudo", methods=["POST"])
@login_required
def restaurar_tudo():
    for model in (Aluno, Turma, Grupo, Classe):
        for row in model.query.filter(model.deleted_at.isnot(None)).all():
            row.deleted_at = None
            row.motivo_eliminacao = None
    db.session.commit()
    flash("Toda a lixeira foi restaurada.", "success")
    return redirect(url_for("lixeira.index"))


@lixeira_bp.route("/esvaziar", methods=["POST"])
@login_required
def esvaziar_lixeira():
    for a in Aluno.query.filter(Aluno.deleted_at.isnot(None)).all():
        db.session.delete(a)
    for tu in Turma.query.filter(Turma.deleted_at.isnot(None)).all():
        db.session.delete(tu)
    for g in Grupo.query.filter(Grupo.deleted_at.isnot(None)).all():
        db.session.delete(g)
    for c in Classe.query.filter(Classe.deleted_at.isnot(None)).all():
        db.session.delete(c)
    db.session.commit()
    flash("Lixeira esvaziada definitivamente.", "warning")
    return redirect(url_for("lixeira.index"))