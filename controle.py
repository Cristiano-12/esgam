import logging
import os
import requests
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
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
    Classe,
    Grupo,
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

try:
    from openpyxl import load_workbook
except ModuleNotFoundError:
    load_workbook = None

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


class FAQFake:
    def __init__(self):
        self.id = ""
        self.pergunta = ""
        self.resposta = ""


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

def obter_banner():
    try:
        banner = Banner.query.filter_by(ativo=True).first()
        if banner:
            return banner
    except Exception:
        logging.exception("Erro ao carregar banner.")
        db.session.rollback()

    return BannerFake()


def obter_carrossel():
    try:
        return Carrossel.query.filter_by(ativo=True).order_by(Carrossel.ordem).all()
    except Exception:
        logging.exception("Erro ao carregar carrossel.")
        db.session.rollback()
        return []


def obter_estatisticas():
    def contar(modelo):
        try:
            return modelo.query.count()
        except Exception:
            db.session.rollback()
            return 0

    return [
        {"id": 1, "cod": "ANO", "label": "Ano de Fundação", "valor": 2000, "animar": False, "sufixo": ""},
        {"id": 2, "cod": "ALUNO", "label": "Alunos Registados", "valor": contar(Aluno), "animar": True, "sufixo": "+"},
        {"id": 3, "cod": "PROF", "label": "Corpo Docente", "valor": contar(Professor), "animar": True, "sufixo": ""},
        {"id": 4, "cod": "TURMA", "label": "Turmas Activas", "valor": contar(Turma), "animar": True, "sufixo": ""}
    ]


def obter_comunicados():
    try:
        return Comunicado.query.order_by(Comunicado.data.desc()).limit(1).all()
    except Exception:
        logging.exception("Erro ao carregar comunicados.")
        db.session.rollback()
        return []


def obter_faq():
    try:
        return FAQ.query.order_by(FAQ.id.desc()).limit(1).all()
    except Exception:
        logging.exception("Erro ao carregar FAQ.")
        db.session.rollback()
        return []


def obter_sobre():
    try:
        sobre = Sobre.query.first()
        if sobre:
            return sobre
    except Exception:
        logging.exception("Erro ao carregar Sobre.")
        db.session.rollback()

    return SobreFake()


def obter_diretor():
    try:
        diretor = Diretor.query.first()
        if diretor:
            return diretor
    except Exception:
        logging.exception("Erro ao carregar Diretor.")
        db.session.rollback()

    return DiretorFake()


def obter_contacto():
    try:
        contacto = Contacto.query.first()
        if contacto:
            return contacto
    except Exception:
        logging.exception("Erro ao carregar contacto.")
        db.session.rollback()

    return ContactoFake()


def carregar_index():
    """Agrupa todos os dados necessários para renderizar a página inicial."""
    return {
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
    pendencias = PendenciaPauta.query.filter_by(status='pendente').order_by(PendenciaPauta.id.desc()).all()

    config = ConfiguracaoSistema.query.first()

    faqs = obter_faq()
    faq1 = faqs[0] if len(faqs) > 0 else FAQFake()
    faq2 = faqs[1] if len(faqs) > 1 else FAQFake()

    contexto = {
        "total_alunos": Aluno.query.filter_by(deleted_at=None).count(),
        "total_classes": Classe.query.filter_by(deleted_at=None).count(),
        "total_grupos": Grupo.query.filter_by(deleted_at=None).count(),
        "trimestre_atual": (config.ano_letivo if config else datetime.now().year),
        "banner": obter_banner(),
        "sobre": obter_sobre(),
        "diretor": obter_diretor(),
        "contacto": obter_contacto(),
        "ano_atual": datetime.now().year,
        "estatisticas": obter_estatisticas(),
        "fotos_carrossel": obter_carrossel(),
        "faq_dinamico": faqs,
        "faq1": faq1,
        "faq2": faq2,
        "publicacoes": Publicacao.query.filter_by(ativo=True).order_by(Publicacao.data_publicacao.desc()).all(),
        "excel_recebidos": 0,
        "excel_importados": 0,
        "pendencias": pendencias,
    }

    return render_template('controle.html', **contexto)


@controle_bp.route('/admin/publicacoes', methods=['GET', 'POST'])
@login_required
def gerir_publicacoes():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('categoria', 'Outro').strip()
        descricao = request.form.get('descricao', '').strip()
        classe = request.form.get('classe', '').strip()
        arquivo = request.files.get('arquivo')

        if not titulo or not arquivo or not arquivo.filename:
            flash('Título e PDF são obrigatórios.', 'erro')
            return redirect(url_for('controle.central_verificacao'))

        url_arquivo = _guardar_ficheiro('arquivo', subpasta='publicacoes')
        if not url_arquivo:
            return redirect(url_for('controle.central_verificacao'))

        publicacao = Publicacao(
            titulo=titulo,
            categoria=categoria or 'Outro',
            descricao=descricao or None,
            classe=classe or None,
            arquivo=url_arquivo,
            ativo=True
        )
        db.session.add(publicacao)
        db.session.commit()
        flash('Publicação criada com sucesso.', 'sucesso')

    return redirect(url_for('controle.central_verificacao'))


SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gmiwrafjeqpixesqvuxe.supabase.co").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_BUCKET = "uploads"


def _guardar_ficheiro(campo_nome, subpasta=''):
    """Envia um ficheiro para o Supabase Storage e devolve o URL público, ou None."""
    arquivo = request.files.get(campo_nome)
    if not (arquivo and arquivo.filename):
        return None

    if not SUPABASE_KEY:
        logging.error("SUPABASE_KEY não está definida — não é possível enviar ficheiros.")
        flash('Configuração de armazenamento em falta. Contacte o suporte técnico.', 'erro')
        return None

    nome_arquivo = secure_filename(arquivo.filename)
    caminho_storage = f"{subpasta}/{nome_arquivo}" if subpasta else nome_arquivo

    conteudo = arquivo.read()
    tipo_mime = arquivo.mimetype or 'application/octet-stream'

    url_upload = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{caminho_storage}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": tipo_mime,
        "x-upsert": "true",  # substitui o ficheiro se já existir com o mesmo nome
    }

    try:
        resposta = requests.put(url_upload, headers=headers, data=conteudo, timeout=30)
        if resposta.status_code not in (200, 201):
            logging.error("Erro ao enviar '%s' para o Supabase Storage: %s - %s",
                          nome_arquivo, resposta.status_code, resposta.text)
            flash('Não foi possível guardar a imagem. As restantes alterações foram guardadas.', 'erro')
            return None
    except requests.RequestException:
        logging.exception("Erro de rede ao enviar '%s' para o Supabase Storage.", nome_arquivo)
        flash('Não foi possível guardar a imagem (erro de rede). As restantes alterações foram guardadas.', 'erro')
        return None

    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{caminho_storage}"


def _extension_excel(nome_arquivo):
    return os.path.splitext(nome_arquivo.lower())[1] in {".xlsx", ".xls"}


def _guardar_upload_excel(arquivo, subpasta="pautas"):
    if not arquivo or not arquivo.filename:
        return None, "Ficheiro inválido."

    nome_arquivo = secure_filename(arquivo.filename)
    if not _extension_excel(nome_arquivo):
        return None, "Apenas ficheiros Excel (.xlsx ou .xls) são aceites."

    pasta_destino = os.path.join("static", "uploads", subpasta)
    try:
        os.makedirs(pasta_destino, exist_ok=True)
        caminho = os.path.join(pasta_destino, nome_arquivo)
        arquivo.save(caminho)
        return nome_arquivo, None
    except OSError:
        logging.exception("Erro ao guardar ficheiro Excel '%s'.", nome_arquivo)
        return None, "Não foi possível guardar o ficheiro Excel neste servidor."


def _subpasta_para_tipo_pauta(tipo_pauta):
    tipo = (tipo_pauta or "").strip().lower()
    if tipo == "notas":
        return "controle"
    if tipo == "turmas":
        return "pautas"
    return "pautas"


@controle_bp.route('/admin/banner', methods=['POST'])
@login_required
def atualizar_banner():
    status = request.form.get('status', 'info').strip()
    titulo = request.form.get('titulo', '').strip()
    mensagem = request.form.get('mensagem', '').strip()
    link_texto = request.form.get('link_texto', '').strip()

    banner = Banner.query.filter_by(ativo=True).first()
    if not banner:
        banner = Banner(titulo=titulo, mensagem=mensagem, ativo=True)
        db.session.add(banner)

    banner.status = status
    banner.titulo = titulo
    banner.mensagem = mensagem
    banner.link_texto = link_texto

    try:
        db.session.commit()
        flash('Banner atualizado com sucesso!', 'banner')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar o banner: {str(e)}', 'banner')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/sobre', methods=['POST'])
@login_required
def atualizar_sobre():
    texto = request.form.get('texto', '').strip()

    sobre = Sobre.query.first()
    if not sobre:
        sobre = Sobre(titulo='Sobre a Escola', texto=texto)
        db.session.add(sobre)

    sobre.texto = texto

    nome_foto = _guardar_ficheiro('foto')
    if nome_foto:
        sobre.foto = nome_foto

    try:
        db.session.commit()
        flash('Informações atualizadas com sucesso!', 'sobre')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar informações: {str(e)}', 'sobre')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/diretor', methods=['POST'])
@login_required
def atualizar_diretor():
    titulo = request.form.get('titulo', '').strip()
    texto = request.form.get('texto', '').strip()

    diretor = Diretor.query.first()
    if not diretor:
        diretor = Diretor(titulo=titulo, texto=texto)
        db.session.add(diretor)

    diretor.titulo = titulo
    diretor.texto = texto

    nome_foto = _guardar_ficheiro('foto')
    if nome_foto:
        diretor.foto = nome_foto

    try:
        db.session.commit()
        flash('Mensagem do diretor atualizada com sucesso!', 'diretor')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar mensagem: {str(e)}', 'diretor')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/comunicado', methods=['POST'])
@login_required
def publicar_comunicado():
    titulo = request.form.get('titulo', '').strip()
    texto = request.form.get('texto', '').strip()

    if not titulo or not texto:
        flash('Título e mensagem são obrigatórios.', 'comunicado')
        return redirect(url_for('controle.central_verificacao'))

    novo = Comunicado(titulo=titulo, texto=texto)
    db.session.add(novo)

    try:
        db.session.commit()

        # Mantém apenas os 3 comunicados mais recentes
        todos = Comunicado.query.order_by(Comunicado.data.desc()).all()
        for antigo in todos[3:]:
            db.session.delete(antigo)
        db.session.commit()

        flash('Comunicado publicado com sucesso!', 'comunicado')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao publicar comunicado: {str(e)}', 'comunicado')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/contacto', methods=['POST'])
@login_required
def atualizar_contacto():
    email = request.form.get('email', '').strip()
    telefone = request.form.get('telefone', '').strip()

    contacto = Contacto.query.first()
    if not contacto:
        contacto = Contacto(email=email or 'esgam@email.com', telefone=telefone or '-')
        db.session.add(contacto)

    if email:
        contacto.email = email
    if telefone:
        contacto.telefone = telefone

    try:
        db.session.commit()
        flash('Contactos atualizados com sucesso!', 'contacto')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar contactos: {str(e)}', 'contacto')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/faq', methods=['POST'])
@login_required
def atualizar_faq():
    faq_id = request.form.get('id')
    pergunta = request.form.get('pergunta', '').strip()
    resposta = request.form.get('resposta', '').strip()

    if not faq_id:
        flash('Selecione uma pergunta válida.', 'faq')
        return redirect(url_for('controle.central_verificacao'))

    item = FAQ.query.get(faq_id)
    if not item:
        item = FAQ(pergunta=pergunta, resposta=resposta)
        db.session.add(item)
    else:
        item.pergunta = pergunta
        item.resposta = resposta

    try:
        db.session.commit()
        flash('FAQ atualizada com sucesso!', 'faq')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar FAQ: {str(e)}', 'faq')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/publicar-aviso', methods=['POST'])
@login_required
def publicar_aviso():
    destino = request.form.get('destino', '').strip()
    mensagem = request.form.get('mensagem', '').strip()

    if not destino or not mensagem:
        flash('Destino e mensagem são obrigatórios.', 'aviso')
        return redirect(url_for('controle.central_verificacao'))

    # Desativa avisos anteriores e publica o novo como ativo
    Aviso.query.filter_by(ativo=True).update({'ativo': False})

    novo_aviso = Aviso(
        mensagem=f"[{destino}] {mensagem}",
        texto=mensagem,
        ativo=True
    )
    db.session.add(novo_aviso)

    try:
        db.session.commit()
        flash('Aviso publicado com sucesso!', 'aviso')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao publicar aviso: {str(e)}', 'aviso')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/upload-pauta', methods=['POST'])
@login_required
def upload_pauta():
    tipo_pauta = request.form.get('tipo_pauta', '').strip() or 'turmas'
    ficheiros = request.files.getlist('arquivo_pauta')
    subpasta = _subpasta_para_tipo_pauta(tipo_pauta)

    if not ficheiros:
        flash('Seleciona pelo menos um ficheiro Excel.', 'pauta')
        return redirect(url_for('controle.central_verificacao'))

    recebidos = 0
    guardados = 0

    for arquivo in ficheiros:
        if not arquivo or not arquivo.filename:
            continue

        recebidos += 1
        nome_arquivo, erro = _guardar_upload_excel(arquivo, subpasta=subpasta)
        if erro:
            flash(erro, 'pauta')
            continue

        guardados += 1
        pendencia = PendenciaPauta(
            arquivo=nome_arquivo,
            classe=tipo_pauta if tipo_pauta != 'notas' else 'controle',
            turma=None,
            grupo=None,
            periodo=None,
            tipo=tipo_pauta,
            descricao=f'Ficheiro Excel recebido para validação. Pasta: {subpasta}.',
            nome_excel=nome_arquivo,
            status='pendente',
        )
        db.session.add(pendencia)

    if guardados:
        try:
            db.session.commit()
            flash(f'{guardados} ficheiro(s) Excel recebido(s) com sucesso.', 'pauta')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registar a pauta recebida: {str(e)}', 'pauta')
    else:
        flash('Nenhum ficheiro Excel válido foi enviado.', 'pauta')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/grupos', methods=['POST'])
@login_required
def gerir_grupos():
    classe_numero = request.form.get('classe', '').strip()
    turma_nome = request.form.get('turma', '').strip()
    grupo_nome = request.form.get('grupo', '').strip()

    if not classe_numero or not turma_nome or not grupo_nome:
        flash('Classe, turma e grupo são obrigatórios.', 'grupo')
        return redirect(url_for('controle.central_verificacao'))

    try:
        classe_numero = int(classe_numero)
    except ValueError:
        flash('Classe inválida.', 'grupo')
        return redirect(url_for('controle.central_verificacao'))

    classe = Classe.query.filter_by(numero=classe_numero, deleted_at=None).first()
    if not classe:
        classe = Classe(numero=classe_numero, nome=f"{classe_numero}ª Classe")
        db.session.add(classe)
        db.session.flush()

    grupo = Grupo.query.filter_by(nome=grupo_nome, classe_id=classe.id, deleted_at=None).first()
    if not grupo:
        grupo = Grupo(nome=grupo_nome, classe_id=classe.id)
        db.session.add(grupo)
        db.session.flush()

    turma = Turma.query.filter_by(nome=turma_nome, grupo_id=grupo.id, deleted_at=None).first()
    if not turma:
        turma = Turma(nome=turma_nome, classe_id=classe.id, grupo_id=grupo.id)
        db.session.add(turma)

    try:
        db.session.commit()
        flash(f'Grupo "{grupo_nome}" e turma "{turma_nome}" criados/confirmados com sucesso!', 'grupo')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar grupo/turma: {str(e)}', 'grupo')

    return redirect(url_for('controle.central_verificacao'))


@controle_bp.route('/admin/carrossel', methods=['POST'])
@login_required
def atualizar_carrossel():
    posicoes_atualizadas = []

    for posicao in range(1, 6):
        nome_foto = _guardar_ficheiro(f'foto{posicao}')
        if not nome_foto:
            continue

        item = Carrossel.query.filter_by(ordem=posicao).first()
        if not item:
            item = Carrossel(imagem=nome_foto, ordem=posicao, ativo=True)
            db.session.add(item)
        else:
            item.imagem = nome_foto
            item.ativo = True

        posicoes_atualizadas.append(posicao)

    if not posicoes_atualizadas:
        flash('Nenhuma imagem foi selecionada — o carrossel não foi alterado.', 'carrossel')
        return redirect(url_for('controle.central_verificacao'))

    try:
        db.session.commit()
        posicoes_texto = ', '.join(str(p) for p in posicoes_atualizadas)
        flash(f'Carrossel atualizado com sucesso! Posição(ões) alterada(s): {posicoes_texto}.', 'carrossel')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar carrossel: {str(e)}', 'carrossel')

    return redirect(url_for('controle.central_verificacao'))


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
                "aluno": {"classe": "0"},
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
            db.session.rollback()

        return {
            "aluno": aluno,
            "pauta_disciplinas": pauta_disciplinas,
            "aviso_painel": aviso_mensagem
        }

    except Exception as e:
        logging.exception("Erro ao carregar o portal do estudante.")
        db.session.rollback()

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