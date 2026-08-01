import logging
import os
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from models import (
    db,
    ConfiguracaoSistema,
    Banner,
    Carrossel,
    Aluno,
    Professor,
    Turma,
    Comunicado,
    FAQ,
    Sobre,
    Diretor,
    Contacto,
    PendenciaPauta,
    Nota,
    NotaTemporaria,
    Aviso,
    Publicacao
)

controle_bp = Blueprint("controle", __name__)


# ==========================================
# 1. CLASSES FAKE / FALLBACK (POO)
# ==========================================

class BannerFake:
    def __init__(self):
        self.status = "normal"
        self.titulo = "Bem-vindo"
        self.mensagem = "Portal ESGAM"
        self.link = None
        self.link_texto = ""


class SobreFake:
    def __init__(self):
        self.eyebrow = "ESGAM"
        self.titulo = "Escola Secundária Geral de Alto Molócuè"
        self.texto = "Informações institucionais ainda não foram cadastradas."
        self.foto = "placeholder.png"


class DiretorFake:
    def __init__(self):
        self.titulo = "Mensagem da Direção"
        self.texto = "Mensagem ainda não disponível."
        self.foto = "placeholder.png"


class ContactoFake:
    def __init__(self):
        self.email = "esgam@email.com"
        self.telefone = "-"


# ==========================================
# 2. AUTENTICAÇÃO E SEGURANÇA
# ==========================================

def login_required(f):
    """Decorator para restrição de acesso a utilizadores autenticados."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Por favor, efetue login para aceder a esta página.', 'erro')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# 3. SERVIÇOS DA PÁGINA INICIAL (INDEX)
# ==========================================

def obter_configuracoes():
    try:
        config = ConfiguracaoSistema.query.first()
        if config:
            return (
                config.portal_aberto,
                config.mensagem_portal or "",
                config.turmas_abertas,
                config.mensagem_turmas or ""
            )
    except Exception:
        logging.exception("Erro ao carregar configurações.")

    return True, "", True, ""


def obter_banner():
    try:
        banner = Banner.query.filter_by(ativo=True).first()
        if banner:
            return banner
    except Exception:
        logging.exception("Erro ao carregar banner.")

    return BannerFake()


def obter_carrossel():
    try:
        return Carrossel.query.filter_by(ativo=True).order_by(Carrossel.ordem).all()
    except Exception:
        logging.exception("Erro ao carregar carrossel.")
        return []


def obter_estatisticas():
    def contar(modelo):
        try:
            return modelo.query.count()
        except Exception:
            return 0

    return [
        {"label": "Ano de Fundação", "valor": 2000, "animar": False, "sufixo": ""},
        {"label": "Alunos Registados", "valor": contar(Aluno), "animar": True, "sufixo": "+"},
        {"label": "Corpo Docente", "valor": contar(Professor), "animar": True, "sufixo": ""},
        {"label": "Turmas Activas", "valor": contar(Turma), "animar": True, "sufixo": ""}
    ]


def obter_comunicados():
    try:
        return Comunicado.query.order_by(Comunicado.data.desc()).all()
    except Exception:
        logging.exception("Erro ao carregar comunicados.")
        return []


def obter_faq():
    try:
        return FAQ.query.order_by(FAQ.id.desc()).all()
    except Exception:
        logging.exception("Erro ao carregar FAQ.")
        return []


def obter_sobre():
    try:
        sobre = Sobre.query.first()
        if sobre:
            return sobre
    except Exception:
        logging.exception("Erro ao carregar Sobre.")

    return SobreFake()


def obter_diretor():
    try:
        diretor = Diretor.query.first()
        if diretor:
            return diretor
    except Exception:
        logging.exception("Erro ao carregar Diretor.")

    return DiretorFake()


def obter_contacto():
    try:
        contacto = Contacto.query.first()
        if contacto:
            return contacto
    except Exception:
        logging.exception("Erro ao carregar contacto.")

    return ContactoFake()


def carregar_index():
    """Agrupa todos os dados necessários para renderizar a página inicial."""
    portal_disp, portal_msg, turmas_disp, turmas_msg = obter_configuracoes()

    return {
        "portal_disponivel": portal_disp,
        "portal_mensagem": portal_msg,
        "turmas_disponivel": turmas_disp,
        "turmas_mensagem": turmas_msg,
        "banner": obter_banner(),
        "fotos_carrossel": obter_carrossel(),
        "estatisticas": obter_estatisticas(),
        "comunicados": obter_comunicados(),
        "faq_dinamico": obter_faq(),
        "sobre": obter_sobre(),
        "diretor": obter_diretor(),
        "contacto": obter_contacto(),
        "ano_atual": datetime.now().year
    }


# ==========================================
# 4. GESTÃO DE PAUTAS E VERIFICAÇÃO DE DADOS
# ==========================================

@controle_bp.route('/admin/verificacao', methods=['GET'])
@login_required
def central_verificacao():
    erros_pauta = PendenciaPauta.query.filter_by(status='pendente').order_by(PendenciaPauta.id.desc()).all()
    return render_template('visao_geral.html', erros_pauta=erros_pauta)


@controle_bp.route('/admin/publicacoes', methods=['GET', 'POST'])
@login_required
def gerir_publicacoes():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('categoria', 'Outro').strip()
        descricao = request.form.get('descricao', '').strip()
        classe = request.form.get('classe', '').strip()
        arquivo = request.files.get('arquivo')

        if not titulo or not arquivo:
            flash('Título e PDF são obrigatórios.', 'erro')
            return redirect(url_for('controle.gerir_publicacoes'))

        nome_arquivo = arquivo.filename or 'documento.pdf'
        caminho = os.path.join('static', 'uploads', 'publicacoes', nome_arquivo)
        arquivo.save(caminho)

        publicacao = Publicacao(
            titulo=titulo,
            categoria=categoria or 'Outro',
            descricao=descricao or None,
            classe=classe or None,
            arquivo=nome_arquivo,
            ativo=True
        )
        db.session.add(publicacao)
        db.session.commit()
        flash('Publicação criada com sucesso.', 'sucesso')
        return redirect(url_for('controle.gerir_publicacoes'))

    publicacoes = Publicacao.query.filter_by(ativo=True).order_by(Publicacao.data_publicacao.desc()).all()
    return render_template('controle.html', publicacoes=publicacoes)


@controle_bp.route('/admin/substituir-pauta', methods=['POST'])
@login_required
def substituir_pauta():
    pendencia_id = request.form.get('id')
    if not pendencia_id:
        flash('Identificador de pendência inválido.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    pendencia = PendenciaPauta.query.get(pendencia_id)
    if not pendencia:
        flash('Registo de pendência não encontrado.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    try:
        Nota.query.filter_by(
            classe=pendencia.classe,
            turma=pendencia.turma,
            grupo=pendencia.grupo,
            periodo=pendencia.periodo
        ).delete(synchronize_session=False)

        notas_temp = NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).all()
        for nt in notas_temp:
            nova_nota = Nota(
                aluno_id=nt.aluno_id,
                disciplina=nt.disciplina,
                classe=nt.classe,
                turma=nt.turma,
                periodo=nt.periodo,
                nota_ac=nt.nota_ac,
                nota_pt=nt.nota_pt,
                nota_ap=nt.nota_ap
            )
            db.session.add(nova_nota)

        NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).delete(synchronize_session=False)
        pendencia.status = 'resolvido'

        db.session.commit()
        flash('Pauta substituída com sucesso!', 'sucesso')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar a substituição: {str(e)}', 'erro')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/ignorar-pauta', methods=['POST'])
@login_required
def ignorar_pauta():
    pendencia_id = request.form.get('id')
    if not pendencia_id:
        flash('Identificador de pendência inválido.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    pendencia = PendenciaPauta.query.get(pendencia_id)
    if not pendencia:
        flash('Pendência não encontrada.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    try:
        NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).delete(synchronize_session=False)
        pendencia.status = 'ignorado'

        db.session.commit()
        flash('A alteração foi descartada. A pauta original foi mantida.', 'sucesso')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao ignorar pauta: {str(e)}', 'erro')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/confirmar-aluno', methods=['POST'])
@login_required
def confirmar_aluno():
    pendencia_id = request.form.get('id')
    id_aluno = request.form.get('id_aluno')

    if not pendencia_id or not id_aluno:
        flash('Por favor, informe o ID correto do aluno.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    aluno_existe = Aluno.query.get(id_aluno)
    if not aluno_existe:
        flash(f'Aluno com ID {id_aluno} não foi encontrado na base de dados.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    pendencia = PendenciaPauta.query.get(pendencia_id)
    if not pendencia:
        flash('Pendência não encontrada.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    try:
        notas_temp = NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).all()
        for nt in notas_temp:
            nova_nota = Nota(
                aluno_id=aluno_existe.id,
                disciplina=nt.disciplina,
                classe=nt.classe,
                turma=nt.turma,
                periodo=nt.periodo,
                nota_ac=nt.nota_ac,
                nota_pt=nt.nota_pt,
                nota_ap=nt.nota_ap
            )
            db.session.add(nova_nota)

        NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).delete(synchronize_session=False)
        pendencia.status = 'resolvido'

        db.session.commit()
        flash(f'Notas associadas com sucesso ao aluno ID {id_aluno}.', 'sucesso')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao associar aluno: {str(e)}', 'erro')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/adicionar-aluno', methods=['POST'])
@login_required
def adicionar_aluno():
    pendencia_id = request.form.get('id')
    if not pendencia_id:
        flash('Identificador de pendência inválido.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    pendencia = PendenciaPauta.query.get(pendencia_id)
    if not pendencia or not pendencia.nome_excel:
        flash('Não foi possível obter os dados do aluno a partir da pendência.', 'erro')
        return redirect(url_for('controle.central_verificacao'))

    try:
        novo_aluno = Aluno(nome=pendencia.nome_excel)
        db.session.add(novo_aluno)
        db.session.flush()

        notas_temp = NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).all()
        for nt in notas_temp:
            nova_nota = Nota(
                aluno_id=novo_aluno.id,
                disciplina=nt.disciplina,
                classe=nt.classe,
                turma=nt.turma,
                periodo=nt.periodo,
                nota_ac=nt.nota_ac,
                nota_pt=nt.nota_pt,
                nota_ap=nt.nota_ap
            )
            db.session.add(nova_nota)

        NotaTemporaria.query.filter_by(pendencia_id=pendencia.id).delete(synchronize_session=False)
        pendencia.status = 'resolvido'

        db.session.commit()
        flash(f'Aluno "{pendencia.nome_excel}" registado e notas importadas com sucesso!', 'sucesso')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registar novo aluno: {str(e)}', 'erro')

    return redirect(url_for('controle.central_verificacao'))


# ==========================================
# 5. SERVIÇOS DO PORTAL
# ==========================================

def carregar_portal(student_id):
    """Carrega todos os dados necessários para o portal do estudante."""
    try:
        aluno = Aluno.query.filter_by(id=student_id).first()

        if not aluno:
            return {
                "aluno": {
                    "id": student_id,
                    "nome": "Estudante não encontrado",
                    "classe": "-",
                    "turma": "-",
                    "grupo": "-",
                    "media_geral": "-",
                    "situacao": None,
                },
                "pauta_disciplinas": [],
                "aviso_painel": "Estudante não encontrado no sistema escolar."
            }

        # Carrega todas as notas associadas ao aluno
        pauta_disciplinas = Nota.query.filter_by(
            aluno_id=student_id
        ).all()

        # Tenta carregar o aviso ativo (tratamento defensivo caso o modelo varie)
        aviso_mensagem = None
        try:
            aviso = Aviso.query.filter_by(ativo=True).first()
            if aviso:
                aviso_mensagem = getattr(aviso, 'mensagem', None) or getattr(aviso, 'texto', None)
        except Exception:
            logging.warning("Modelo Aviso não encontrado ou erro na consulta de aviso ativo.")

        return {
            "aluno": {
                "id": aluno.id,
                "nome": getattr(aluno, 'nome', 'Sem nome'),
                "classe": getattr(aluno, 'classe', '-') or '-',
                "turma": getattr(aluno, 'turma', '-') or '-',
                "grupo": getattr(aluno, 'grupo', '-') or '-',
                "media_geral": getattr(aluno, 'media_geral', '-') or '-',
                "situacao": getattr(aluno, 'situacao', None),
            },
            "pauta_disciplinas": pauta_disciplinas,
            "aviso_painel": aviso_mensagem
        }

    except Exception as e:
        logging.exception("Erro ao carregar o portal do estudante.")

        return {
            "aluno": {"classe": "0"},
            "pauta_disciplinas": [],
            "aviso_painel": "Erro ao carregar os dados."
        }


# ==========================================
# 6. SERVIÇOS DE AUTENTICAÇÃO (LOGIN)
# ==========================================

def carregar_login():
    """Lógica preparatória para a página de login."""
    return {}