from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db, Aluno, Classe, Turma, Grupo, Banner, ConfiguracaoSistema, Nota

visao_bp = Blueprint('visao_geral', __name__)

SENHA_PORTAL_ALUNO = "ESGAM000"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Por favor, efetue login para aceder a esta página.', 'erro')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function


@visao_bp.route('/admin/central', methods=['GET'])
@login_required
def central_verificacao():
    total_aluno = Aluno.query.filter_by(deleted_at=None).count()
    total_classes = Classe.query.filter_by(deleted_at=None).count()
    total_turmas = Turma.query.filter_by(deleted_at=None).count()
    total_grupos = Grupo.query.filter_by(deleted_at=None).count()
    total_avisos = Banner.query.count()

    classe_filtro = request.args.get('classe_filtro', '').strip()
    grupo_filtro = request.args.get('grupo_filtro', '').strip()
    turma_filtro = request.args.get('turma', '').strip()
    pesquisa_id = request.args.get('pesquisa_id', '').strip()
    tem_filtro = bool(classe_filtro or grupo_filtro or turma_filtro or pesquisa_id)
    alunos = []

    if tem_filtro:
        query_alunos = Aluno.query.filter(Aluno.deleted_at.is_(None))

        if classe_filtro:
            # 1) alunos com classe_id ligado
            # 2) alunos cuja nota tem texto de classe (import Excel)
            ids_por_nota = (
                db.session.query(Nota.aluno_id)
                .filter(Nota.classe.isnot(None), Nota.classe.ilike(f"%{classe_filtro}%"))
                .distinct()
            )
            query_alunos = query_alunos.outerjoin(Classe, Aluno.classe_id == Classe.id)
            if classe_filtro.isdigit():
                n = int(classe_filtro)
                query_alunos = query_alunos.filter(
                    (Classe.numero == n)
                    | (Classe.nome.ilike(f"%{classe_filtro}%"))
                    | (Aluno.id.in_(ids_por_nota))
                )
            else:
                query_alunos = query_alunos.filter(
                    (Classe.nome.ilike(f"%{classe_filtro}%"))
                    | (Aluno.id.in_(ids_por_nota))
                )

        if grupo_filtro:
            query_alunos = query_alunos.outerjoin(
                Grupo, Aluno.grupo_id == Grupo.id
            ).filter(Grupo.nome.ilike(grupo_filtro.strip()))

        if turma_filtro:
            ids_turma = (
                db.session.query(Nota.aluno_id)
                .filter(Nota.turma.isnot(None), Nota.turma.ilike(f"%{turma_filtro}%"))
                .distinct()
            )
            query_alunos = query_alunos.outerjoin(
                Turma, Aluno.turma_id == Turma.id
            ).filter(
                (Turma.nome.ilike(f"%{turma_filtro}%"))
                | (Aluno.id.in_(ids_turma))
            )

        if pesquisa_id:
            if pesquisa_id.isdigit():
                query_alunos = query_alunos.filter(
                    (Aluno.id == int(pesquisa_id))
                    | (Aluno.codigo_estudante.ilike(f"%{pesquisa_id}%"))
                )
            else:
                query_alunos = query_alunos.filter(
                    Aluno.codigo_estudante.ilike(f"%{pesquisa_id}%")
                )

        alunos = (
            query_alunos.distinct()
            .order_by(Aluno.nome.asc())
            .limit(200)
            .all()
        )

    # Pesquisa individual: só código ESG ou ID numérico
    aluno_pesquisado = None
    if pesquisa_id:
        if pesquisa_id.isdigit():
            aluno_pesquisado = Aluno.query.filter_by(
                id=int(pesquisa_id), deleted_at=None
            ).first()
        if not aluno_pesquisado:
            aluno_pesquisado = Aluno.query.filter_by(
                codigo_estudante=pesquisa_id, deleted_at=None
            ).first()
        if not aluno_pesquisado:
            aluno_pesquisado = Aluno.query.filter(
                Aluno.deleted_at.is_(None),
                Aluno.codigo_estudante.ilike(f"%{pesquisa_id}%"),
            ).first()

    avisos_gerais = Banner.query.filter_by(status='normal', ativo=True).all()
    avisos_individuais = Banner.query.filter_by(status='urgente', ativo=True).all()

    return render_template(
        'visao_geral.html',
        total_aluno=total_aluno,
        total_classes=total_classes,
        total_turmas=total_turmas,
        total_grupos=total_grupos,
        total_avisos=total_avisos,
        alunos=alunos,
        aluno_pesquisado=aluno_pesquisado,
        senha_portal=SENHA_PORTAL_ALUNO,
        avisos_gerais=[b.mensagem for b in avisos_gerais],
        avisos_individuais=[b.mensagem for b in avisos_individuais],
        tem_filtro=tem_filtro,
        classe_filtro=classe_filtro,
        grupo_filtro=grupo_filtro,
        turma_filtro=turma_filtro,
        pesquisa_id=pesquisa_id,
    )


@visao_bp.route('/admin/controlar-sistema', methods=['POST'])
@login_required
def controlar_sistema():
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


@visao_bp.route('/admin/controlo-especifico', methods=['GET'])
@login_required
def controlo_especifico():
    tipo = request.args.get('tipo')
    classe = request.args.get('classe')
    turma = request.args.get('turma')
    grupo = request.args.get('grupo')
    aluno_id = request.args.get('id')

    if tipo == 'aluno' and aluno_id:
        return redirect(url_for('visao_geral.central_verificacao', pesquisa_id=aluno_id))
    if tipo == 'classe' and classe:
        return redirect(url_for('visao_geral.central_verificacao', classe_filtro=classe))
    if tipo == 'turma' and turma:
        return redirect(url_for('visao_geral.central_verificacao', turma=turma))
    if tipo == 'grupo' and grupo:
        return redirect(url_for('visao_geral.central_verificacao', grupo_filtro=grupo))

    return redirect(url_for('visao_geral.central_verificacao'))