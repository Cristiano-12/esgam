from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
 
from extensions import db
 
 
# ==============================================================================
# ADMINISTRADOR
# ==============================================================================
class Administrador(db.Model):
    """Utilizador do painel administrativo (secretaria, direção, etc.)."""
 
    __tablename__ = "administradores"
 
    NIVEIS_VALIDOS = ("super_admin", "secretaria", "direcao")
 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(150), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
 
    # "super_admin" (acesso total), "secretaria" (alunos/pautas/comunicados),
    # "direcao" (leitura + mensagem do diretor). Ajuste os níveis conforme
    # as permissões reais que decidir aplicar nas rotas.
    nivel_acesso = db.Column(db.String(30), nullable=False, default="secretaria")
 
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
 
    def definir_senha(self, senha_texto_plano: str) -> None:
        self.senha_hash = generate_password_hash(senha_texto_plano)
 
    def verificar_senha(self, senha_texto_plano: str) -> bool:
        return check_password_hash(self.senha_hash, senha_texto_plano)
 
    def registar_login(self) -> None:
        """Chamar isto na rota de login, após autenticar com sucesso."""
        self.ultimo_login = datetime.utcnow()
        db.session.commit()
 
    def __repr__(self):
        return f"<Administrador {self.username} ({self.nivel_acesso})>"
 
 
# ==============================================================================
# ALUNO
# ==============================================================================
class Aluno(db.Model):
    """
    Registo de um estudante. numero_identificacao é o ID legível usado em
    pautas e no cartão do aluno (ex.: ESGAM-2026-0007) — diferente da
    chave primária interna 'id', que é só para uso da base de dados.
    """
 
    __tablename__ = "alunos"
 
    ESTADOS_VALIDOS = ("ativo", "inativo", "transferido", "concluido")
 
    id = db.Column(db.Integer, primary_key=True)
 
    numero_identificacao = db.Column(
        db.String(30), unique=True, nullable=False, index=True
    )
 
    nome = db.Column(db.String(150), nullable=False, index=True)
    data_nascimento = db.Column(db.Date)
    genero = db.Column(db.String(20))
 
    classe = db.Column(db.String(20), nullable=False, index=True)   # ex.: "10ª"
    turma = db.Column(db.String(10), nullable=False, index=True)    # ex.: "A"
    grupo = db.Column(db.String(30))                                # ex.: "Ciências" (opcional)
 
    estado = db.Column(db.String(20), nullable=False, default="ativo", index=True)
 
    encarregado_nome = db.Column(db.String(150))
    encarregado_contacto = db.Column(db.String(50))
 
    # Login do estudante no Portal — fica nulo até o aluno definir a
    # primeira senha (ou a secretaria a definir por ele).
    senha_hash = db.Column(db.String(255))
 
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    def definir_senha(self, senha_texto_plano: str) -> None:
        self.senha_hash = generate_password_hash(senha_texto_plano)
 
    def verificar_senha(self, senha_texto_plano: str) -> bool:
        if not self.senha_hash:
            return False
        return check_password_hash(self.senha_hash, senha_texto_plano)
 
    @property
    def tem_acesso_portal(self) -> bool:
        """Um aluno só pode entrar no Portal se tiver senha definida E
        estiver com estado 'ativo' — evita que um aluno transferido ou
        inativo continue a conseguir entrar."""
        return bool(self.senha_hash) and self.estado == "ativo"
 
    @staticmethod
    def gerar_numero_identificacao(ano: int, sequencial: int) -> str:
        """
        Gera um ID no formato ESGAM-<ano>-<sequencial de 4 dígitos>.
        Ex.: Aluno.gerar_numero_identificacao(2026, 7) -> 'ESGAM-2026-0007'
 
        Calcule o próximo 'sequencial' nas rotas, por exemplo:
            total_do_ano = Aluno.query.filter(
                Aluno.numero_identificacao.like(f"ESGAM-{ano}-%")
            ).count()
            novo_id = Aluno.gerar_numero_identificacao(ano, total_do_ano + 1)
        """
        return f"ESGAM-{ano}-{sequencial:04d}"
 
    def __repr__(self):
        return f"<Aluno {self.numero_identificacao} — {self.nome}>"
 
 
# ==============================================================================
# CONFIGURAÇÃO GERAL DO SITE (linha única, id fixo = 1)
# ==============================================================================
class Configuracao(db.Model):
    """
    Tabela de configuração geral — sempre uma única linha (id=1).
    Controla o que aparece/desaparece no site público sem precisar de
    alterar código: disponibilidade do Portal, da Consulta Pública,
    dados de contacto e valores usados nas estatísticas.
    """
 
    __tablename__ = "configuracao"
 
    id = db.Column(db.Integer, primary_key=True)
 
    # --- Portal do Estudante --------------------------------------------------
    portal_disponivel = db.Column(db.Boolean, nullable=False, default=True)
    portal_mensagem = db.Column(db.String(255), default="")
 
    # --- Consulta Pública de Turmas ------------------------------------------
    turmas_disponivel = db.Column(db.Boolean, nullable=False, default=True)
    turmas_mensagem = db.Column(db.String(255), default="")
 
    # --- Contacto institucional -----------------------------------------------
    email_contacto = db.Column(db.String(120), default="")
    telefone_contacto = db.Column(db.String(50), default="")
 
    # --- Estatísticas ----------------------------------------------------------
    ano_fundacao = db.Column(db.Integer)
 
    # taxa_aprovacao fica manual por agora; quando a Parte 3 (Pauta/Nota)
    # estiver pronta, isto pode passar a ser calculado automaticamente a
    # partir das notas em vez de editado à mão.
    taxa_aprovacao = db.Column(db.Integer)
 
    @staticmethod
    def obter() -> "Configuracao":
        """
        Devolve a linha única de configuração, criando-a com valores por
        omissão na primeira vez que for chamada (evita ter de correr um
        script de seed só para isto existir).
        """
        config = Configuracao.query.get(1)
        if config is None:
            config = Configuracao(id=1)
            db.session.add(config)
            db.session.commit()
        return config
 
    def __repr__(self):
        return "<Configuracao geral do site>"
 