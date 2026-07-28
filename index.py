from flask import Blueprint, render_template
from controle import carregar_index

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def pagina_inicial():
    return render_template(
        "index.html",
        **carregar_index()
    )