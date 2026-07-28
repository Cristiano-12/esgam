from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash

# Blueprint para o módulo da lixeira
lixeira_bp = Blueprint('lixeira', __name__, url_prefix='/admin/lixeira')

# Constante da regra de integridade operacional (10 dias para expiração)
DIAS_RETENCAO = 10


def calcular_dias_restantes(data_eliminacao):
    """Calcula quantos dias faltam para o registo ser apagado definitivamente."""
    data_expiracao = data_eliminacao + timedelta(days=DIAS_RETENCAO)
    dias = (data_expiracao - datetime.now()).days
    return max(0, dias), data_expiracao.strftime("%d/%m/%Y %H:%M")


@lixeira_bp.route('/', methods=['GET'])
def index():
    pesquisa = request.args.get('pesquisa', '').strip().lower()
    categoria = request.args.get('categoria', 'tudo')

    # Exemplo de consulta aos modelos (substitui pelas tuas queries do banco/ORM)
    # Ex: Classes.query.filter_by(deleted=True)...
    
    # 1. Classes eliminadas
    classes_raw = []  # Ex: Classe.query.filter(Classe.deleted_at.isnot(None)).all()
    classes_eliminadas = []
    for c in classes_raw:
        dias_rest, data_final = calcular_dias_restantes(c.deleted_at)
        classes_eliminadas.append({
            'id': c.id,
            'nome': c.nome,
            'total_grupos': c.total_grupos,
            'total_turmas': c.total_turmas,
            'total_alunos': c.total_alunos,
            'data_eliminacao': c.deleted_at.strftime("%d/%m/%Y"),
            'data_final_eliminacao': data_final,
            'motivo_eliminacao': getattr(c, 'motivo_eliminacao', None),
            'dias_restantes': dias_rest
        })

    # 2. Grupos eliminados
    grupos_raw = []
    grupos_eliminados = []
    for g in grupos_raw:
        dias_rest, data_final = calcular_dias_restantes(g.deleted_at)
        grupos_eliminados.append({
            'id': g.id,
            'classe': g.classe_nome,
            'nome': g.nome,
            'total_turmas': g.total_turmas,
            'total_alunos': g.total_alunos,
            'data_eliminacao': g.deleted_at.strftime("%d/%m/%Y"),
            'data_final_eliminacao': data_final,
            'motivo_eliminacao': getattr(g, 'motivo_eliminacao', None),
            'dias_restantes': dias_rest
        })

    # 3. Turmas eliminadas
    turmas_raw = []
    turmas_eliminadas = []
    for t in turmas_raw:
        dias_rest, data_final = calcular_dias_restantes(t.deleted_at)
        turmas_eliminadas.append({
            'id': t.id,
            'classe': t.classe_nome,
            'grupo': t.grupo_nome,
            'nome': t.nome,
            'total_alunos': len(t.alunos),
            'alunos': [{'id': a.id, 'nome': a.nome, 'classe': a.classe_nome, 'grupo': a.grupo_nome, 'turma': t.nome} for a in t.alunos],
            'data_eliminacao': t.deleted_at.strftime("%d/%m/%Y"),
            'data_final_eliminacao': data_final,
            'motivo_eliminacao': getattr(t, 'motivo_eliminacao', None),
            'dias_restantes': dias_rest
        })

    # 4. Alunos eliminados
    alunos_raw = []
    alunos_eliminados = []
    for a in alunos_raw:
        dias_rest, data_final = calcular_dias_restantes(a.deleted_at)
        alunos_eliminados.append({
            'id': a.codigo_estudante,
            'nome': a.nome,
            'classe': a.classe_nome,
            'grupo': a.grupo_nome,
            'turma': a.turma_nome,
            'data_eliminacao': a.deleted_at.strftime("%d/%m/%Y"),
            'data_final_eliminacao': data_final,
            'motivo_eliminacao': getattr(a, 'motivo_eliminacao', None),
            'dias_restantes': dias_rest
        })

    # Totais para os Mini-Cards do Dashboard
    total_alunos_lixeira = len(alunos_eliminados)
    total_turmas_lixeira = len(turmas_eliminadas)
    total_grupos_lixeira = len(grupos_eliminados)
    total_classes_lixeira = len(classes_eliminadas)

    return render_template(
        'admin/lixeira.html',
        classes_eliminadas=classes_eliminadas,
        grupos_eliminados=grupos_eliminados,
        turmas_eliminadas=turmas_eliminadas,
        alunos_eliminados=alunos_eliminados,
        total_alunos_lixeira=total_alunos_lixeira,
        total_turmas_lixeira=total_turmas_lixeira,
        total_grupos_lixeira=total_grupos_lixeira,
        total_classes_lixeira=total_classes_lixeira
    )


# --- ROTAS DE RESTAURAÇÃO E MANUTENÇÃO ---

@lixeira_bp.route('/restaurar/classe/<int:id_classe>', methods=['POST'])
def restaurar_classe(id_classe):
    # Lógica do Efeito Cascata: Restaurar a classe -> restaurar grupos, turmas e alunos associados
    flash("Classe e todos os registos associados restaurados com sucesso!", "success")
    return redirect(url_for('lixeira.index'))


@lixeira_bp.route('/restaurar/grupo/<int:id_grupo>', methods=['POST'])
def restaurar_grupo(id_grupo):
    # Restaurar grupo -> restaurar turmas e alunos associados
    flash("Grupo e turmas associadas restaurados com sucesso!", "success")
    return redirect(url_for('lixeira.index'))


@lixeira_bp.route('/restaurar/turma/<int:id_turma>', methods=['POST'])
def restaurar_turma(id_turma):
    # Restaurar turma -> restaurar alunos associados
    flash("Turma e alunos associados restaurados com sucesso!", "success")
    return redirect(url_for('lixeira.index'))


@lixeira_bp.route('/restaurar/aluno/<string:id_aluno>', methods=['POST'])
def restaurar_aluno(id_aluno):
    # Restaurar apenas o aluno individual
    flash(f"Aluno {id_aluno} restaurado com sucesso!", "success")
    return redirect(url_for('lixeira.index'))


@lixeira_bp.route('/restaurar-tudo', methods=['POST'])
def restaurar_tudo():
    # Restaurar todos os registos presentes na lixeira
    flash("Todos os registos da lixeira foram restaurados!", "success")
    return redirect(url_for('lixeira.index'))


@lixeira_bp.route('/esvaziar', methods=['POST'])
def esvaziar_lixeira():
    # Remoção física (DELETE definitivo) de todos os itens em soft delete
    flash("A lixeira foi esvaziada definitivamente.", "warning")
    return redirect(url_for('lixeira.index'))