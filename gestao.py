from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Aluno, Classe, Grupo, Turma

# Nome ajustado para gestao_bp para bater certo com a importação no app.py
gestao_bp = Blueprint('gestao', __name__)


@gestao_bp.route('/painel')
def painel():
    """Página principal do painel de controlo."""
    return render_template('painel.html')


@gestao_bp.route('/gestao-alunos', methods=['GET'])
def gestao_alunos():
    """Lista e pesquisa alunos registados que não estejam na lixeira (deleted_at IS NULL)."""
    pesquisa = request.args.get('pesquisa', '').strip()
    query = Aluno.query.filter_by(deleted_at=None)

    if pesquisa:
        query = query.filter(
            (Aluno.codigo_estudante.contains(pesquisa)) |
            (Aluno.nome.contains(pesquisa))
        )

    alunos = query.all()

    return render_template(
        'gestao_alunos.html', 
        alunos=alunos, 
        aluno_edicao=None
    )


@gestao_bp.route('/editar-aluno/<int:aluno_id>', methods=['GET'])
def editar_aluno(aluno_id):
    """Procura o aluno pelo ID e carrega a lista para renderizar a página com o formulário de edição."""
    aluno_selecionado = Aluno.query.get_or_404(aluno_id)
    alunos = Aluno.query.filter_by(deleted_at=None).all()

    return render_template(
        'gestao_alunos.html', 
        alunos=alunos, 
        aluno_edicao=aluno_selecionado
    )


@gestao_bp.route('/guardar-alteracoes/<int:aluno_id>', methods=['POST'])
def guardar_alteracoes(aluno_id):
    """Atualiza o nome e os relacionamentos de Classe, Grupo e Turma na BD de forma defensiva."""
    aluno = Aluno.query.get_or_404(aluno_id)

    nome = request.form.get('nome', '').strip().upper()
    if not nome:
        flash("O nome do aluno não pode estar vazio.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    # 1. Conversão segura da Classe
    try:
        classe_numero = int(request.form.get('classe', ''))
    except (TypeError, ValueError):
        flash("Classe inválida.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    # 2. Validação da Classe na Base de Dados
    classe = Classe.query.filter_by(numero=classe_numero).first()
    if not classe:
        flash("A classe selecionada não foi encontrada.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    # 3. Validação do Grupo associado à Classe
    grupo_nome = request.form.get('grupo', '').strip()
    grupo = Grupo.query.filter_by(nome=grupo_nome, classe_id=classe.id).first()
    if not grupo:
        flash(f"O Grupo '{grupo_nome}' não existe para a {classe.numero}ª classe.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    # 4. Validação da Turma associada ao Grupo
    turma_nome = request.form.get('turma', '').strip()
    turma = Turma.query.filter_by(nome=turma_nome, grupo_id=grupo.id).first()
    if not turma:
        flash(f"A Turma '{turma_nome}' não existe para o Grupo {grupo.nome}.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    # 5. Atualização das Propriedades
    aluno.nome = nome
    aluno.classe_id = classe.id
    aluno.grupo_id = grupo.id
    aluno.turma_id = turma.id

    # 6. Persistência Protegida com Rollback
    try:
        db.session.commit()
        flash("Dados do aluno atualizados com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro interno ao guardar as alterações na base de dados.", "danger")
        return redirect(url_for('gestao.editar_aluno', aluno_id=aluno.id))

    return redirect(url_for('gestao.gestao_alunos'))


@gestao_bp.route('/eliminar-aluno/<int:aluno_id>', methods=['POST'])
def eliminar_aluno(aluno_id):
    """Aplica Soft Delete com rollback seguro em caso de falha."""
    aluno = Aluno.query.get_or_404(aluno_id)

    aluno.deleted_at = datetime.now(timezone.utc)
    aluno.motivo_eliminacao = "Eliminado pelo administrador"

    try:
        db.session.commit()
        flash("Aluno enviado para a lixeira com sucesso!", "warning")
    except Exception:
        db.session.rollback()
        flash("Erro interno ao mover o aluno para a lixeira.", "danger")

    return redirect(url_for('gestao.gestao_alunos'))