from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, request, send_file, abort
from models import ConfiguracaoSistema, PautaTurma

try:
    from openpyxl import load_workbook
except ModuleNotFoundError:
    load_workbook = None

pauta_bp = Blueprint("pauta", __name__)


@pauta_bp.route("/consulta-turmas")
def consulta_turmas():
    config = ConfiguracaoSistema.query.first()
    modo_pauta_aberto = config.modo_pauta_aberto if config else True

    publicacoes = []
    pautas = PautaTurma.query.filter_by(ativo=True).order_by(PautaTurma.data_publicacao.desc()).all()

    for pauta in pautas:
        preview_cabecalho = []
        preview_linhas = []
        tipo_arquivo = (pauta.mimetype or "").lower()

        if load_workbook and pauta.ficheiro and "spreadsheet" in tipo_arquivo:
            try:
                livro = load_workbook(BytesIO(pauta.ficheiro), data_only=True, read_only=True)
                folha = livro.active
                linhas = list(folha.iter_rows(values_only=True))
                if linhas:
                    preview_cabecalho = [str(celula or "") for celula in linhas[0][:8]]
                    for linha in linhas[1:9]:
                        preview_linhas.append([str(celula or "") for celula in linha[:8]])
            except Exception:
                preview_cabecalho = []
                preview_linhas = []

        publicacoes.append({
            "id": pauta.id,
            "titulo": pauta.titulo,
            "descricao": pauta.categoria or "Documento",
            "data_publicacao": pauta.data_publicacao,
            "preview_cabecalho": preview_cabecalho,
            "preview_linhas": preview_linhas,
            "tem_preview": bool(preview_cabecalho and preview_linhas),
            "mime": pauta.mimetype or "",
        })

    return render_template(
        'pauta.html',
        publicacoes=publicacoes,
        modo_pauta_aberto=modo_pauta_aberto
    )


@pauta_bp.route("/consulta-turmas/ficheiro/<int:pauta_id>")
def descarregar_ficheiro(pauta_id):
    pauta = PautaTurma.query.get_or_404(pauta_id)
    if not pauta.ficheiro:
        abort(404)

    nome = pauta.arquivo or f"pauta_{pauta.id}.xlsx"
    return send_file(
        BytesIO(pauta.ficheiro),
        mimetype=pauta.mimetype or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=False,
        download_name=nome,
    )
