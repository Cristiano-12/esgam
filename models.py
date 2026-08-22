from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ==========================================
# 0. GESTÃO DE UTILIZADORES / AUTENTICAÇÃO
# ==========================================
class Utilizador(db.Model):
    __tablename__ = 'utilizadores'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='admin', nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Utilizador {self.username}>"


# ==========================================
# 1. CONFIGURAÇÕES GERAIS DO SISTEMA
# ==========================================
class ConfiguracaoSistema(db.Model):
    __tablename__ = 'configuracoes_sistema'

    id = db.Column(db.Integer, primary_key=True)
    
    # Controlo de Visibilidade e Mensagens do Portal
    portal_aberto = db.Column(db.Boolean, default=True, nullable=False)
    mensagem_portal = db.Column(db.Text, default="", nullable=True)
    
    turmas_abertas = db.Column(db.Boolean, default=True, nullable=False)
    mensagem_turmas = db.Column(db.Text, default="", nullable=True)

    # Controla se a consulta pública das pautas está visível
    modo_pauta_aberto = db.Column(db.Boolean, default=True, nullable=False)
    
    # Ano letivo ativo
    ano_letivo = db.Column(db.Integer, default=datetime.now().year, nullable=False)
    
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<ConfiguracaoSistema portal={self.portal_aberto} turmas={self.turmas_abertas}>"


# ==========================================
# 2. HIERARQUIA ACADÉMICA (Classes, Grupos, Turmas)
# ==========================================
class Classe(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)  # Ex: 10, 11, 12
    nome = db.Column(db.String(20), nullable=False)              # Ex: "10ª Classe"

    # Soft Delete / Lixeira
    deleted_at = db.Column(db.DateTime, nullable=True)
    motivo_eliminacao = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    grupos = db.relationship('Grupo', backref='classe_rel', lazy=True, cascade="all, delete-orphan")
    turmas = db.relationship('Turma', backref='classe_rel', lazy=True, cascade="all, delete-orphan")
    alunos = db.relationship('Aluno', backref='classe_rel', lazy=True, cascade="all, delete-orphan")

    @property
    def total_grupos(self):
        return Grupo.query.filter_by(classe_id=self.id, deleted_at=None).count()

    @property
    def total_turmas(self):
        return Turma.query.filter_by(classe_id=self.id, deleted_at=None).count()

    @property
    def total_alunos(self):
        return Aluno.query.filter_by(classe_id=self.id, deleted_at=None).count()


class Grupo(db.Model):
    __tablename__ = 'grupos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)  # Ex: "A", "B", "Ciências"
    
    classe_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

    # Soft Delete / Lixeira
    deleted_at = db.Column(db.DateTime, nullable=True)
    motivo_eliminacao = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    turmas = db.relationship('Turma', backref='grupo_rel', lazy=True, cascade="all, delete-orphan")
    alunos = db.relationship('Aluno', backref='grupo_rel', lazy=True, cascade="all, delete-orphan")

    @property
    def classe_nome(self):
        return self.classe_rel.nome if self.classe_rel else ""

    @property
    def total_turmas(self):
        return Turma.query.filter_by(grupo_id=self.id, deleted_at=None).count()

    @property
    def total_alunos(self):
        return Aluno.query.filter_by(grupo_id=self.id, deleted_at=None).count()


class Turma(db.Model):
    __tablename__ = 'turmas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)  # Ex: "Turma 01", "A1"
    
    classe_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=True)

    # Soft Delete / Lixeira
    deleted_at = db.Column(db.DateTime, nullable=True)
    motivo_eliminacao = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    alunos = db.relationship('Aluno', backref='turma_rel', lazy=True, cascade="all, delete-orphan")

    @property
    def classe_nome(self):
        return self.classe_rel.nome if self.classe_rel else ""

    @property
    def grupo_nome(self):
        return self.grupo_rel.nome if self.grupo_rel else "Sem Grupo"


# ==========================================
# 3. REGISTO DOS ESTUDANTES
# ==========================================
class Aluno(db.Model):
    __tablename__ = 'alunos'

    id = db.Column(db.Integer, primary_key=True)
    codigo_estudante = db.Column(db.String(30), unique=True, nullable=True)  # Ex: Matricula
    nome = db.Column(db.String(150), nullable=False)

    classe_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=True)

    data_cadastro = db.Column(db.DateTime, default=datetime.now)

    situacao = db.Column(db.String(80), nullable=True)
    aviso = db.Column(db.String(120), nullable=True)

    # Soft Delete / Lixeira
    deleted_at = db.Column(db.DateTime, nullable=True)
    motivo_eliminacao = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    notas = db.relationship('Nota', backref='aluno_rel', lazy=True, cascade="all, delete-orphan")

    @property
    def matricula(self):
        return self.codigo_estudante

    @property
    def classe_nome(self):
        return self.classe_rel.nome if self.classe_rel else ""

    @property
    def grupo_nome(self):
        return self.grupo_rel.nome if self.grupo_rel else "Único"

    @property
    def turma_nome(self):
        return self.turma_rel.nome if self.turma_rel else ""


# ==========================================
# 4. CORPO DOCENTE
# ==========================================
class Professor(db.Model):
    __tablename__ = 'professores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telefone = db.Column(db.String(30), nullable=True)
    disciplina = db.Column(db.String(100), nullable=True)

    data_cadastro = db.Column(db.DateTime, default=datetime.now)

    # Soft Delete / Lixeira
    deleted_at = db.Column(db.DateTime, nullable=True)
    motivo_eliminacao = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Professor {self.nome}>"


# ==========================================
# 5. COMUNICADOS E AVISOS
# ==========================================
class Banner(db.Model):
    __tablename__ = 'banner'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="normal", nullable=False)  # Ex: "normal", "alerta", "urgente"
    titulo = db.Column(db.String(150), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    link_texto = db.Column(db.String(50), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Banner {self.titulo}>"


class Carrossel(db.Model):
    __tablename__ = 'carrossel'

    id = db.Column(db.Integer, primary_key=True)
    imagem = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    ordem = db.Column(db.Integer, default=1, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Carrossel ordem={self.ordem}>"


class Comunicado(db.Model):
    __tablename__ = 'comunicados'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    
    data = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Comunicado {self.titulo}>"

    @property
    def data_formatada(self):
        return self.data.strftime("%d/%m/%Y")


class FAQ(db.Model):
    __tablename__ = 'faq'

    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String(255), nullable=False)
    resposta = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<FAQ id={self.id}>"


class EstatisticaPagina(db.Model):
    __tablename__ = 'estatisticas_pagina'

    id = db.Column(db.Integer, primary_key=True)
    cod = db.Column(db.String(30), unique=True, nullable=False)
    label = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False, default=0)
    sufixo = db.Column(db.String(20), nullable=True, default="")
    animar = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<EstatisticaPagina cod={self.cod}>"


class PautaTurma(db.Model):
    __tablename__ = 'pautas_turma'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default='turmas')
    categoria = db.Column(db.String(50), nullable=True)
    classe = db.Column(db.String(20), nullable=True)
    turma = db.Column(db.String(20), nullable=True)
    periodo = db.Column(db.String(50), nullable=True)
    arquivo = db.Column(db.String(255), nullable=False)
    ficheiro = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(120), nullable=True)
    data_publicacao = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<PautaTurma id={self.id} tipo={self.tipo}>"


class Aviso(db.Model):
    __tablename__ = 'avisos'

    id = db.Column(db.Integer, primary_key=True)
    mensagem = db.Column(db.Text, nullable=False)
    texto = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Aviso id={self.id} ativo={self.ativo}>"


# ==========================================
# 6. INFORMAÇÕES INSTITUCIONAIS
# ==========================================
class Sobre(db.Model):
    __tablename__ = 'sobre'

    id = db.Column(db.Integer, primary_key=True)
    eyebrow = db.Column(db.String(100), nullable=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(255), nullable=True, default="placeholder.png")

    def __repr__(self):
        return f"<Sobre {self.titulo}>"


class Diretor(db.Model):
    __tablename__ = 'diretor'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(255), nullable=True, default="placeholder.png")

    def __repr__(self):
        return f"<Diretor {self.titulo}>"


class Contacto(db.Model):
    __tablename__ = 'contacto'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, default="esgam@email.com")
    telefone = db.Column(db.String(50), nullable=False, default="-")

    def __repr__(self):
        return f"<Contacto email={self.email}>"


class Publicacao(db.Model):
    __tablename__ = 'publicacoes'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default='Outro')
    descricao = db.Column(db.Text, nullable=True)
    classe = db.Column(db.String(20), nullable=True)
    arquivo = db.Column(db.String(255), nullable=False)
    data_publicacao = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Publicacao {self.titulo}>"


# ==========================================
# 7. GESTÃO DE PAUTAS E PENDÊNCIAS DE NOTAS
# ==========================================
class PendenciaPauta(db.Model):
    __tablename__ = 'pendencias_pauta'

    id = db.Column(db.Integer, primary_key=True)
    arquivo = db.Column(db.String(255), nullable=True)
    classe = db.Column(db.String(50), nullable=True)
    turma = db.Column(db.String(50), nullable=True)
    grupo = db.Column(db.String(50), nullable=True)
    periodo = db.Column(db.String(50), nullable=True)
    tipo = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    nome_excel = db.Column(db.String(150), nullable=True)
    nome_banco = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), default='pendente', nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    notas_temporarias = db.relationship('NotaTemporaria', backref='pendencia_rel', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PendenciaPauta id={self.id} status={self.status}>"


class Nota(db.Model):
    __tablename__ = 'notas'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    disciplina = db.Column(db.String(100), nullable=False)
    classe = db.Column(db.String(50), nullable=True)
    turma = db.Column(db.String(50), nullable=True)
    periodo = db.Column(db.String(50), nullable=True)

    nota_ac = db.Column(db.Float, nullable=True)
    nota_pt = db.Column(db.Float, nullable=True)
    nota_ap = db.Column(db.Float, nullable=True)
    nota_exame = db.Column(db.Float, nullable=True)  # nota X / exame

    def __repr__(self):
        return f"<Nota aluno_id={self.aluno_id} disciplina={self.disciplina}>"

    @property
    def media_parcial(self):
        """Média de AC + PT + AP (ignora None)."""
        vals = [v for v in (self.nota_ac, self.nota_pt, self.nota_ap) if v is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    @property
    def media_com_exame(self):
        """Média parcial + exame (quando existir)."""
        base = self.media_parcial
        if base is None:
            return self.nota_exame
        if self.nota_exame is None:
            return base
        return round((base + self.nota_exame) / 2, 1)


class NotaTemporaria(db.Model):
    __tablename__ = 'notas_temporarias'

    id = db.Column(db.Integer, primary_key=True)
    pendencia_id = db.Column(db.Integer, db.ForeignKey('pendencias_pauta.id'), nullable=False)
    aluno_id = db.Column(db.Integer, nullable=True)
    disciplina = db.Column(db.String(100), nullable=False)
    classe = db.Column(db.String(50), nullable=True)
    turma = db.Column(db.String(50), nullable=True)
    periodo = db.Column(db.String(50), nullable=True)

    nota_ac = db.Column(db.Float, nullable=True)
    nota_pt = db.Column(db.Float, nullable=True)
    nota_ap = db.Column(db.Float, nullable=True)
    nota_exame = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<NotaTemporaria pendencia_id={self.pendencia_id}>"