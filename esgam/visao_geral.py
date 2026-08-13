from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, Aluno, Classe, Turma, Grupo, Banner, ConfiguracaoSistema

visao_bp = Blueprint('visao_geral', __name__)


def login_required(f):
    """Decorator para restrição de acesso a administradores autenticados."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Por favor, efetue login para aceder a esta página.', 'erro')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# ROTA PRINCIPAL: CENTRAL DE VERIFICAÇÃO / VISÃO GERAL
# ==========================================

@visao_bp.route('/admin/central', methods=['GET'])
@login_required
def central_verificacao():
    """
    Exibe dados consolidados do sistema, métricas, avisos e permite
    a filtragem e pesquisa de estudantes na base de dados.
    """
    # 1. Métricas Globais (Contagem via SQLAlchemy ORM)
    total_aluno = Aluno.query.filter_by(deleted_at=None).count()
    total_classes = Classe.query.filter_by(deleted_at=None).count()
    total_turmas = Turma.query.filter_by(deleted_at=None).count()
    total_grupos = Grupo.query.filter_by(deleted_at=None).count()
    total_avisos = Banner.query.count()

    # 2. Configurações Globais do Sistema
    config = ConfiguracaoSistema.query.first()
    if not config:
        config = ConfiguracaoSistema()
        db.session.add(config)
        db.session.commit()

    portal_notas_aberto = config.portal_aberto
    portal_pauta_aberto = config.modo_pauta_aberto

    estado_consulta_publica = "Aberto" if portal_pauta_aberto else "Fechado"
    estado_portal_estudante = "Aberto" if portal_notas_aberto else "Fechado"

    # 3. Filtragem da Tabela Geral de Alunos
    classe_filtro = request.args.get('classe_filtro', '').strip()
    grupo_filtro = request.args.get('grupo_filtro', '').strip()
    turma_filtro = request.args.get('turma', '').strip()

    query_alunos = Aluno.query.filter_by(deleted_at=None)

    if classe_filtro:
        query_alunos = query_alunos.join(Classe).filter(Classe.nome == classe_filtro)
    if grupo_filtro:
        query_alunos = query_alunos.join(Grupo).filter(Grupo.nome == grupo_filtro)
    if turma_filtro:
        query_alunos = query_alunos.join(Turma).filter(Turma.nome == turma_filtro)

    alunos = query_alunos.order_by(Aluno.nome.asc()).limit(50).all()

    # 4. Pesquisa Específica por Código/ID de Aluno
    pesquisa_id = request.args.get('pesquisa_id', '').strip()
    aluno_pesquisado = None

    if pesquisa_id:
        if pesquisa_id.isdigit():
            aluno_pesquisado = Aluno.query.filter_by(id=int(pesquisa_id), deleted_at=None).first()
        if not aluno_pesquisado:
            aluno_pesquisado = Aluno.query.filter_by(codigo_estudante=pesquisa_id, deleted_at=None).first()

    # 5. Avisos / Banners
    avisos_gerais = Banner.query.filter_by(status='normal', ativo=True).all()
    avisos_individuais = Banner.query.filter_by(status='urgente', ativo=True).all()

    return render_template(
        'visao_geral.html',
        total_aluno=total_aluno,
        total_classes=total_classes,
        total_turmas=total_turmas,
        total_grupos=total_grupos,
        total_avisos=total_avisos,
        estado_consulta_publica=estado_consulta_publica,
        estado_portal_estudante=estado_portal_estudante,
        portal_notas_aberto=portal_notas_aberto,
        portal_pauta_aberto=portal_pauta_aberto,
        alunos=alunos,
        aluno_pesquisado=aluno_pesquisado,
        avisos_gerais=[b.mensagem for b in avisos_gerais],
        avisos_individuais=[b.mensagem for b in avisos_individuais]
    )


# ==========================================
# ROTA POST: CONTROLO DE ACESSO AO SISTEMA
# ==========================================

@visao_bp.route('/admin/controlar-sistema', methods=['POST'])
@login_required
def controlar_sistema():
    """Alterna os estados de visibilidade das pautas e do portal no sistema."""
    acao = request.form.get('acao')
    
    config = ConfiguracaoSistema.query.first()
    if not config:
        config = ConfiguracaoSistema()
        db.session.add(config)

    if acao == 'portal_notas':
        config.portal_aberto = not config.portal_aberto
    elif acao == 'pautas_publicas':
        config.modo_pauta_aberto = not config.modo_pauta_aberto
    elif acao == 'abrir_tudo':
        config.portal_aberto = True
        config.modo_pauta_aberto = True
    elif acao == 'fechar_tudo':
        config.portal_aberto = False
        config.modo_pauta_aberto = False

    try:
        db.session.commit()
        flash('Configurações do sistema atualizadas com sucesso!', 'sucesso')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar configurações: {str(e)}', 'erro')

    return redirect(url_for('visao_geral.central_verificacao'))


# ==========================================
# ROTA GET: CONTROLO ESPECÍFICO (REDIRECIONAMENTO)
# ==========================================

@visao_bp.route('/admin/controlo-especifico', methods=['GET'])
@login_required
def controlo_especifico():
    """Redireciona os filtros específicos da página central de volta para os parâmetros de consulta."""
    tipo = request.args.get('tipo')
    classe = request.args.get('classe')
    turma = request.args.get('turma')
    grupo = request.args.get('grupo')
    aluno_id = request.args.get('id')

    if tipo == 'aluno' and aluno_id:
        return redirect(url_for('visao_geral.central_verificacao', pesquisa_id=aluno_id))
    elif tipo == 'classe' and classe:
        return redirect(url_for('visao_geral.central_verificacao', classe_filtro=classe))
    elif tipo == 'turma' and turma:
        return redirect(url_for('visao_geral.central_verificacao', turma=turma))
    elif tipo == 'grupo' and grupo:
        return redirect(url_for('visao_geral.central_verificacao', grupo_filtro=grupo))

    return redirect(url_for('visao_geral.central_verificacao'))