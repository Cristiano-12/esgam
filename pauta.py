from flask import Blueprint, render_template, request, abort
from models import Aluno, Classe, Turma

pauta_bp = Blueprint("pauta", __name__)


def carregar_dados_turmas(numero_classe):
    """Carrega as turmas e respetivos alunos da classe selecionada."""

    classe = Classe.query.filter_by(
        numero=numero_classe,
        deleted_at=None
    ).first()

    if not classe:
        return {}

    alunos = (
        Aluno.query
        .filter_by(
            classe_id=classe.id,
            deleted_at=None
        )
        .order_by(Aluno.nome.asc())
        .all()
    )

    dados = {}

    for aluno in alunos:
        grupo = aluno.grupo_nome or "Único"
        turma = aluno.turma_nome or "Sem Turma"

        dados.setdefault(grupo, {})
        dados[grupo].setdefault(turma, [])

        dados[grupo][turma].append({
            "matricula": aluno.codigo_estudante or f"ID-{aluno.id}",
            "nome": aluno.nome
        })

    return dados


@pauta_bp.route("/consulta-turmas")
def consulta_turmas():
    classe = request.args.get("classe", type=int)

    dados_estrutura = {}

    if classe:
        dados_estrutura = carregar_dados_turmas(classe)

    return render_template(
        "consulta_turmas.html",
        classe_selecionada=classe,
        dados_estrutura=dados_estrutura
    )