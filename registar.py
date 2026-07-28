import random
import string
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from models import db, Aluno, Classe, Grupo, Turma

# Nome do blueprint ajustado para 'registar_bp' para coincidir com a importacao no app.py
registar_bp = Blueprint('registar_aluno', __name__)


def login_required(f):
    """Decorator para restricao de acesso apenas a administradores autenticados."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'sucesso': False, 'mensagem': 'Sessao expirada. Faca login novamente.'}), 401
            flash('Por favor, efetue login para aceder a esta pagina.', 'erro')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def gerar_codigo_estudante_unico():
    """
    Gera um codigo unico no formato ESGAM-XXXX (ex: ESGAM-8492).
    Garante por consulta SQLAlchemy que o codigo gerado nao existe previamente.
    """
    while True:
        sufixo = ''.join(random.choices(string.digits, k=4))
        codigo_gerado = f"ESGAM-{sufixo}"
        
        # Consulta usando a ORM no modelo Aluno
        existe = Aluno.query.filter_by(codigo_estudante=codigo_gerado).first()
        if not existe:
            return codigo_gerado


# ==========================================
# ROTA 1: RENDERIZACAO DA PAGINA DE REGISTO
# ==========================================

@registar_bp.route('/admin/registar-aluno', methods=['GET'])
@login_required
def pagina_registar_aluno():
    """Renderiza a interface do formulario de registo de novo aluno."""
    classes = Classe.query.filter_by(deleted_at=None).all()
    grupos = Grupo.query.filter_by(deleted_at=None).all()
    turmas = Turma.query.filter_by(deleted_at=None).all()
    
    return render_template(
        'registar_aluno.html', 
        classes=classes, 
        grupos=grupos, 
        turmas=turmas
    )


# ==========================================
# ROTA 2: PROCESSAMENTO E SALVAMENTO DO ALUNO
# ==========================================

@registar_bp.route('/admin/salvar-aluno', methods=['POST'])
@login_required
def salvar_aluno():
    """
    Processa a submissao do formulario usando Flask-SQLAlchemy.
    Gera um codigo unico de estudante e armazena os dados na tabela 'alunos'.
    """
    nome = request.form.get('nome', '').strip()
    classe_id = request.form.get('classe_id') or request.form.get('classe')
    grupo_id = request.form.get('grupo_id') or request.form.get('grupo')
    turma_id = request.form.get('turma_id') or request.form.get('turma')

    # Validacao basica dos campos obrigatorios
    if not nome or not classe_id or not turma_id:
        msg_erro = 'Os campos Nome, Classe e Turma sao de preenchimento obrigatorio.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'sucesso': False, 'mensagem': msg_erro}), 400
        flash(msg_erro, 'erro')
        return redirect(url_for('registar_aluno.pagina_registar_aluno'))

    try:
        # Gera o identificador unico ESGAM-XXXX
        codigo_estudante = gerar_codigo_estudante_unico()

        # Instancia e salva o aluno via ORM
        novo_aluno = Aluno(
            codigo_estudante=codigo_estudante,
            nome=nome,
            classe_id=int(classe_id) if classe_id else None,
            grupo_id=int(grupo_id) if grupo_id and str(grupo_id).isdigit() else None,
            turma_id=int(turma_id) if turma_id else None
        )

        db.session.add(novo_aluno)
        db.session.commit()

        # Resposta para requisicoes assincronas (AJAX/Fetch)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({
                'sucesso': True,
                'id_gerado': codigo_estudante,
                'mensagem': 'Aluno registado com sucesso.'
            }), 201

        # Resposta para submissao HTTP padrao
        flash(f'Aluno registado com sucesso! ID Gerado: {codigo_estudante}', 'sucesso')
        return redirect(url_for('registar_aluno.pagina_registar_aluno'))

    except Exception as e:
        db.session.rollback()
        msg_erro = f'Erro na base de dados ao salvar o aluno: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'sucesso': False, 'mensagem': msg_erro}), 500
        
        flash(msg_erro, 'erro')
        return redirect(url_for('registar_aluno.pagina_registar_aluno'))