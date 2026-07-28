import os
import secrets
from flask import Flask, render_template
from models import db

# -------------------------------------------------------------------
# Inicialização da Aplicação Flask
# -------------------------------------------------------------------
app = Flask(__name__)

# Configurações do Flask
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ESGAM_2026_CHAVE_INTERNA")

# No Vercel, o SQLite só funciona dentro da pasta /tmp
if os.environ.get("VERCEL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/esgam.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///esgam.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar SQLAlchemy com o App
db.init_app(app)

# -------------------------------------------------------------------
# Importação e Registo de Blueprints
# -------------------------------------------------------------------
from index import index_bp
from login import login_bp
from portal import portal_bp
from controle import controle_bp
from registar import registar_bp
from visao_geral import visao_bp
from lixeira import lixeira_bp
from pauta import pauta_bp
from gestao import gestao_bp

app.register_blueprint(index_bp)
app.register_blueprint(login_bp)
app.register_blueprint(portal_bp) 
app.register_blueprint(controle_bp)
app.register_blueprint(registar_bp)
app.register_blueprint(visao_bp)
app.register_blueprint(lixeira_bp)
app.register_blueprint(pauta_bp)
app.register_blueprint(gestao_bp)

# -------------------------------------------------------------------
# Tratamento de Erros Globais (HTTP Error Handlers)
# -------------------------------------------------------------------

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    """Trata caminhos/páginas não encontradas no sistema."""
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_servidor(e):
    """Trata erros internos imprevistos do servidor."""
    return render_template("404.html"), 500

# -------------------------------------------------------------------
# Base de Dados
# -------------------------------------------------------------------
import models

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)