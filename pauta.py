from flask import Blueprint, render_template, request, redirect, url_for
from models import Publicacao, ConfiguracaoSistema

pauta_bp = Blueprint("pauta", __name__)


@pauta_bp.route("/consulta-turmas")
def consulta_turmas():
    config = ConfiguracaoSistema.query.first()
    modo_pauta_aberto = config.modo_pauta_aberto if config else True
    publicacoes = Publicacao.query.filter_by(ativo=True).order_by(Publicacao.data_publicacao.desc()).all()

    return render_template(
        "pauta.html",
        publicacoes=publicacoes,
        modo_pauta_aberto=modo_pauta_aberto
    )