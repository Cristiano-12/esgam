import os
from flask import Flask, render_template, send_from_directory
from jinja2 import TemplateNotFound
from werkzeug.exceptions import NotFound as WerkzeugNotFound
from models import db


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ESGAM_2026_CHAVE_INTERNA")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if os.environ.get("VERCEL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/esgam.db"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///esgam.db"

    db.init_app(app)

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

    @app.route('/static/<path:filename>')
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

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
