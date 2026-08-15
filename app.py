import os
import secrets

from flask import Flask, render_template, send_from_directory
from jinja2 import TemplateNotFound
from sqlalchemy import inspect, text
from sqlalchemy.engine import URL
from werkzeug.security import generate_password_hash

from models import Utilizador, db


try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


# ==========================================
# Configuração
# ==========================================
def _build_database_uri() -> str:
    db_host = os.getenv("DB_HOST", "").strip()
    db_port = os.getenv("DB_PORT", "5432").strip()
    db_name = os.getenv("DB_NAME", "").strip()
    db_user = os.getenv("DB_USER", "").strip()
    db_password = os.getenv("DB_PASSWORD", "").strip()
    db_supabase = os.getenv("DB_SUPABASE", "").strip()

    if db_port and not db_port.isdigit():
        raise RuntimeError("DB_PORT inválida.")

    if all([db_host, db_port, db_name, db_user, db_password]):
        return URL.create(
            drivername="postgresql+psycopg2",
            username=db_user,
            password=db_password,
            host=db_host,
            port=int(db_port),
            database=db_name,
        )

    if os.getenv("VERCEL"):
        print(
            "AVISO: DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD não estão todas "
            "definidas nas variáveis de ambiente do Vercel — a app vai usar SQLite "
            "temporário em /tmp, cujos dados NÃO persistem entre execuções."
        )
        return "sqlite:////tmp/esgam.db"

    return "sqlite:///esgam.db"


def create_app():
    app = Flask(__name__)

    # SECRET_KEY dinâmica e limpa
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_hex(32)

    app.config["SECRET_KEY"] = secret_key
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_database_uri()

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    db_uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    if db_uri.startswith("postgresql"):
        app.logger.info("Base de dados em uso: PostgreSQL (Supabase)")
    else:
        app.logger.warning("Base de dados em uso: %s", db_uri)

    # ==========================================
    # Base de Dados
    # ==========================================
    db.init_app(app)

    # ==========================================
    # Blueprints
    # ==========================================
    from controle import controle_bp
    from gestao import gestao_bp
    from index import index_bp
    from lixeira import lixeira_bp
    from login import login_bp
    from pauta import pauta_bp
    from portal import portal_bp
    from registar import registar_bp
    from visao_geral import visao_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(controle_bp)
    app.register_blueprint(registar_bp)
    app.register_blueprint(visao_bp)
    app.register_blueprint(lixeira_bp)
    app.register_blueprint(pauta_bp)
    app.register_blueprint(gestao_bp)

    # ==========================================
    # Error Handlers
    # ==========================================
    @app.errorhandler(404)
    def pagina_nao_encontrada(e):
        try:
            return render_template("404.html"), 404
        except TemplateNotFound:
            return "<h1>Página não encontrada</h1>", 404

    @app.errorhandler(500)
    def erro_servidor(e):
        try:
            return render_template("404.html"), 500
        except TemplateNotFound:
            return "<h1>Erro interno do servidor</h1>", 500

    @app.errorhandler(400)
    def servico_indisponivel(e):
        try:
            return render_template("404.html"), 400
        except TemplateNotFound:
            return "<h1>Pedido inválido</h1>", 400

    @app.route("/static/<path:filename>")
    def serve_static(filename):
        normalized_path = os.path.normpath(filename)
        if normalized_path.startswith("..") or normalized_path == "..":
            return "", 404

        full_path = os.path.join(app.static_folder, normalized_path)
        if os.path.isfile(full_path):
            return send_from_directory(app.static_folder, normalized_path)

        if normalized_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico")):
            fallback_path = os.path.join(app.static_folder, "logo.png")
            if os.path.isfile(fallback_path):
                return send_from_directory(app.static_folder, "logo.png")

        return "", 404

    # ==========================================
    # Inicialização
    # ==========================================
    with app.app_context():
        try:
            db.create_all()
            _garantir_colunas_pautas_turma(app)
            _garantir_colunas_notas(app)

            # Cria o utilizador admin apenas se não estiver a rodar no Vercel (ambiente local)
            if not os.getenv("VERCEL"):
                admin = Utilizador.query.filter_by(username="admin").first()
                if not admin:
                    db.session.add(
                        Utilizador(
                            username="123456",
                            password=generate_password_hash("654321"),
                            nome="Administrador",
                            role="admin",
                            ativo=True,
                        )
                    )
                    db.session.commit()
        except Exception as e:
            app.logger.exception("Erro durante a inicialização da base de dados")
            db.session.rollback()

    return app


def _garantir_colunas_pautas_turma(app):
    """Mantém a tabela pautas_turma compatível com o modelo atual sem apagar dados."""
    try:
        engine = db.engine
        insp = inspect(engine)
        if "pautas_turma" not in insp.get_table_names():
            return

        colunas = {col["name"] for col in insp.get_columns("pautas_turma")}
        alteracoes = []

        if "ficheiro" not in colunas:
            alteracoes.append("ALTER TABLE pautas_turma ADD COLUMN ficheiro BYTEA")
        if "mimetype" not in colunas:
            alteracoes.append("ALTER TABLE pautas_turma ADD COLUMN mimetype VARCHAR(120)")

        if alteracoes:
            with engine.begin() as conn:
                for sql in alteracoes:
                    conn.execute(text(sql))
            app.logger.info("Tabela pautas_turma atualizada com colunas em falta: %s", ", ".join(alteracoes))
    except Exception:
        app.logger.exception("Não foi possível garantir o esquema de pautas_turma.")


def _garantir_colunas_notas(app):
    """Garante a coluna nota_exame nas tabelas de notas sem apagar dados."""
    try:
        engine = db.engine
        insp = inspect(engine)
        tabelas = {
            "notas": "FLOAT",
            "notas_temporarias": "FLOAT",
        }
        for tabela, tipo in tabelas.items():
            if tabela not in insp.get_table_names():
                continue
            colunas = {col["name"] for col in insp.get_columns(tabela)}
            if "nota_exame" not in colunas:
                # SQLite usa REAL; PostgreSQL aceita FLOAT/DOUBLE PRECISION
                col_type = "DOUBLE PRECISION" if str(engine.url).startswith("postgresql") else "REAL"
                sql = f"ALTER TABLE {tabela} ADD COLUMN nota_exame {col_type}"
                with engine.begin() as conn:
                    conn.execute(text(sql))
                app.logger.info("Coluna nota_exame adicionada à tabela %s", tabela)
    except Exception:
        app.logger.exception("Não foi possível garantir a coluna nota_exame.")


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)