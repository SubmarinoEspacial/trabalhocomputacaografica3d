#!/usr/bin/env python3
"""Gera as texturas procedurais do projeto com Pillow e NumPy.

Substitui os antigos scripts ad-hoc não versionados. Todas as imagens são
determinísticas (seed fixa por textura) e saem em RGB, no mesmo tamanho dos
arquivos já commitados, para que o resultado possa substituí-los sem alterar
as malhas ou a leitura visual da cena.

Uso:
    python tools/generate_textures.py --check   # gera em pasta temporária e valida (nada é sobrescrito)
    python tools/generate_textures.py --force   # reescreve os PNGs em assets/textures/
    python tools/generate_textures.py --out DIR # escreve em DIR (não toca em assets/textures/); arquivos existentes são sobrescritos
    python tools/generate_textures.py --only paineis_disco,lua
    # Sem flags, arquivos já existentes em assets/textures/ são pulados (não destrutivo).

Requer Pillow e NumPy: pip install -r requirements-dev.txt
"""
import argparse
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parents[1]
ASSETS = RAIZ / "assets" / "textures"


def ruido(shape, escala, rng):
    """Ruído de valor contínuo por bilinear (grade aleatória ampliada).

    `escala` pode ser escalar (grade quadrada) ou tupla `(escala_y, escala_x)`.
    """
    if isinstance(escala, tuple):
        escala_y, escala_x = escala
    else:
        escala_y = escala_x = escala
    baixo = rng.random((shape[0] // escala_y + 1, shape[1] // escala_x + 1))
    imagem = Image.fromarray((baixo * 255).astype(np.uint8), "L")
    imagem = imagem.resize((shape[1], shape[0]), Image.BILINEAR)
    return np.asarray(imagem, dtype=np.float32) / 255.0


def salvar(nome, imagem):
    return nome, imagem


def gerar_ceu_estrelado():
    """4096×2048: gradiente noturno, neblina suave e estrelas."""
    largura, altura = 4096, 2048
    rng = np.random.default_rng(20261108)
    # Gradiente vertical: zênite quase negro, horizonte azul escuro.
    coluna = np.linspace(0.0, 1.0, altura, dtype=np.float32)
    topo, base = np.array((5.0, 8.0, 20.0), dtype=np.float32), np.array((16.0, 24.0, 48.0), dtype=np.float32)
    gradiente = topo[None, :, None] + (base - topo)[None, :, None] * (coluna ** 1.6)[:, None, None]
    gradiente = np.broadcast_to(gradiente, (altura, 3, largura)).transpose(0, 2, 1)
    imagem = np.ascontiguousarray(gradiente)
    # Faixa de "neblina galáctica" diagonal e tênue no céu.
    yy, xx = np.mgrid[0:altura, 0:largura].astype(np.float32)
    centro_y = altura * 0.40 + (xx / largura - 0.5) * altura * 0.34
    banda = np.exp(-((yy - centro_y) / (altura * 0.085)) ** 2)
    imagem = imagem + banda[:, :, None] * np.array((12.0, 15.0, 30.0), dtype=np.float32)[None, None, :]
    # Neblina suave: duas camadas de ruído em baixa frequência.
    nevoa = 0.55 * ruido((altura, largura), 256, rng) + 0.45 * ruido((altura, largura), 128, rng)
    nevoa = (nevoa - nevoa.mean()) * (0.055 / max(nevoa.std(), 1e-6))
    imagem = imagem + nevoa[:, :, None] * np.array((60.0, 80.0, 130.0), dtype=np.float32)[None, None, :]
    # Estrelas: distribuídas com densidade maior no alto (zênite).
    draw = ImageDraw.Draw(im := Image.fromarray(np.clip(imagem, 0, 255).astype(np.uint8), "RGB"))
    for _ in range(4200):
        x = int(rng.random() * largura)
        y = int((rng.random() ** 1.7) * altura)
        brilho = rng.integers(110, 256)
        raio = 0 if rng.random() < 0.86 else (1 if rng.random() < 0.9 else 2)
        cor = (int(brilho), int(brilho), min(255, int(brilho + 12)))
        if raio == 0:
            draw.point((x, y), fill=cor)
        else:
            draw.ellipse((x - raio, y - raio, x + raio, y + raio), fill=cor)
    # Algumas estrelas brilhantes com halo.
    for _ in range(36):
        x = int(rng.random() * largura)
        y = int((rng.random() ** 1.7) * altura)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(214, 224, 255))
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), outline=(120, 140, 200))
    return salvar("ceu_estrelado_procedural.png", im.filter(ImageFilter.GaussianBlur(0.4)))


def gerar_lua():
    """512×512: disco lunar cinza com manchas (maria) e borda clara; fora do disco, preto."""
    rng = np.random.default_rng(20261109)
    tamanho = 512
    yy, xx = np.mgrid[0:tamanho, 0:tamanho].astype(np.float32)
    centro = (tamanho - 1) / 2.0
    distancia = np.sqrt((xx - centro) ** 2 + (yy - centro) ** 2)
    raio = 236.0
    # Base: leve gradiente radial (borda mais escura por esfericidade).
    esfera = np.clip(1.0 - (distancia / raio) ** 2, 0.0, 1.0) ** 0.5
    # Manchas tipo maria: ruído suave em tons de cinza-azulado.
    maria = ruido((tamanho, tamanho), 48, rng)
    maria = (maria - maria.mean()) * 70.0
    detalhe = ruido((tamanho, tamanho), 12, rng)
    detalhe = (detalhe - detalhe.mean()) * 34.0
    base = 188.0 + 34.0 * esfera + maria + detalhe
    base = np.clip(base, 0.0, 255.0)
    azul = np.array((0.94, 0.97, 1.05), dtype=np.float32)
    imagem = np.clip(base[:, :, None] * azul[None, None, :], 0, 255)
    # Fosco fora do disco; no disco, nada de transparência (blending por alfa do alpha).
    mascara = distancia <= raio
    imagem[~mascara] = 0.0
    # Um toque de brilho na borda iluminada.
    borda = np.exp(-((distancia - raio) / 3.0) ** 2)
    imagem += borda[:, :, None] * 42.0
    return salvar("lua_procedural.png", Image.fromarray(np.clip(imagem, 0, 255).astype(np.uint8), "RGB"))


def gerar_espuma():
    """512×512: cristas de espuma em faixas onduladas com pontos de bolha (canal R) sobre preto."""
    rng = np.random.default_rng(20261110)
    tamanho = 512
    yy, xx = np.mgrid[0:tamanho, 0:tamanho].astype(np.float32)
    # Fase deformada por ruído grande: as "frentes de onda" serpenteiam na horizontal.
    ondulacao = ruido((tamanho, tamanho), 44, rng) * 6.2
    frentes = np.sin(xx * 0.052 + yy * 0.115 + ondulacao)
    cristas = np.clip(frentes, 0.0, None) ** 2.7
    # Filamentos claros secundários entre as cristas.
    filamentos = np.clip(np.sin(xx * 0.023 + yy * 0.21 + ruido((tamanho, tamanho), 80, rng) * 9.0), 0.0, None) ** 5.0
    # Pontos de bolha espalhados (espuma pipocante).
    pontos_finos = ruido((tamanho, tamanho), 9, rng)
    pontos = np.clip((pontos_finos - 0.74) * 8.0, 0.0, 1.0)
    imagem = np.clip(cristas * 0.62 + filamentos * 0.30 + pontos * 1.15, 0.0, 1.0)
    imagem = (imagem**1.35) * 255.0
    return salvar("espuma_procedural.png", Image.fromarray(imagem.astype(np.uint8), "L").convert("RGB"))


def gerar_pintura_submarino():
    """512×512: chapa naval escura — base azul-marinho, emendas, rebites claros e ferrugem discreta."""
    rng = np.random.default_rng(20261107)
    tamanho = 512
    base = 40.0 + 17.0 * ruido((tamanho, tamanho), 64, rng) + 9.0 * ruido((tamanho, tamanho), 11, rng)
    # Pinceladas horizontais sutis de tinta.
    base = base + (np.cumsum(rng.normal(0.0, 1.0, tamanho)) * 0.16)[None, :]
    tom = np.array((0.38, 0.47, 0.66), dtype=np.float32)  # azul-marinho escuro
    imagem = np.clip(base[:, :, None] * tom[None, None, :] * 1.9, 0, 255)
    im = Image.fromarray(imagem.astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(im)
    # Emendas de chapa: fenda escura + filete claro (alto-relevo aparente).
    emendas_y = (96, 208, 330, 430)
    emendas_x = (150, 330)
    for y in emendas_y:
        draw.line((0, y, tamanho, y), fill=(13, 17, 27), width=5)
        draw.line((0, y + 4, tamanho, y + 4), fill=(103, 115, 148), width=2)
        draw.line((0, y + 6, tamanho, y + 6), fill=(55, 63, 86), width=1)
    for x in emendas_x:
        draw.line((x, 0, x, tamanho), fill=(15, 19, 31), width=4)
        draw.line((x + 3, 0, x + 3, tamanho), fill=(94, 106, 136), width=1)
    # Rebites: fileiras junto às emendas e pontos soltos no campo.
    for y in emendas_y:
        for x in range(14, tamanho, 21):
            for yy in (y - 10, y + 13):
                draw.ellipse((x - 2.7, yy - 2.7, x + 2.7, yy + 2.7), fill=(154, 164, 189))
                draw.point((x - 1, yy - 1), fill=(224, 231, 243))
    for _ in range(230):
        x = int(rng.random() * tamanho)
        y = int(rng.random() * tamanho)
        clareza = int(120 + 100 * rng.random())
        draw.ellipse((x - 1.7, y - 1.7, x + 1.7, y + 1.7), fill=(clareza, clareza, min(255, int(clareza * 1.1))))
    # Riscos e manchas escuras de desgaste.
    for _ in range(46):
        x = int(rng.random() * tamanho)
        y = int(rng.random() * tamanho)
        draw.line((x, y, x + int(rng.normal(0, 22)), y + int(rng.normal(0, 6))), fill=int(95 + 60 * rng.random()), width=1)
    for _ in range(24):
        x = int(rng.random() * tamanho)
        y = int(rng.random() * tamanho)
        r = int(4 + 10 * rng.random())
        draw.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=(13, 16, 26))
    # Pontos de ferrugem discretos nas emendas.
    for _ in range(18):
        x = int(rng.random() * tamanho)
        y = int(emendas_y[int(rng.random() * len(emendas_y))] + rng.normal(0, 5))
        y = int(np.clip(y, 0, tamanho - 1))
        r = 1 + int(2.6 * rng.random())
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(99, 56, 28))
    return salvar("pintura_submarino_procedural.png", im)


def gerar_paineis_disco():
    """512×512: painéis metálicos escuros — grade de placas com berço/bevel, parafusos e desgaste."""
    rng = np.random.default_rng(20261106)
    tamanho = 512
    celula = tamanho // 4
    base = 56.0 + 12.0 * ruido((tamanho, tamanho), 64, rng) + 7.0 * ruido((tamanho, tamanho), 14, rng)
    # Variação por célula (painéis com tons ligeiramente diferentes).
    for linha in range(4):
        for coluna in range(4):
            jitter = rng.uniform(-10.0, 10.0)
            base[linha * celula:(linha + 1) * celula, coluna * celula:(coluna + 1) * celula] += jitter
    tom = np.array((0.80, 0.84, 0.94), dtype=np.float32)
    imagem = np.clip(base[:, :, None] * tom[None, None, :], 0, 255)
    im = Image.fromarray(imagem.astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(im)
    # Berço/bevel de cada painel: friso externo escuro + filete claro interno.
    for linha in range(4):
        for coluna in range(4):
            x0 = coluna * celula
            y0 = linha * celula
            x1 = x0 + celula
            y1 = y0 + celula
            draw.rectangle((x0 + 3, y0 + 3, x1 - 3, y1 - 3), outline=(18, 21, 29), width=3)
            draw.rectangle((x0 + 7, y0 + 7, x1 - 7, y1 - 7), outline=(116, 124, 146), width=1)
            # Linha de luz no topo/esquerda, sombra no rodapé/direita (bevel).
            draw.line((x0 + 7, y0 + 8, x1 - 7, y0 + 8), fill=(150, 158, 182), width=1)
            draw.line((x0 + 8, y0 + 7, x0 + 8, y1 - 7), fill=(140, 148, 170), width=1)
            draw.line((x0 + 7, y1 - 8, x1 - 7, y1 - 8), fill=(26, 29, 38), width=2)
            draw.line((x1 - 8, y0 + 7, x1 - 8, y1 - 7), fill=(30, 33, 43), width=2)
            # Parafusos nos cantos das placas: fenda escura + ponto claro.
            for px, py in ((x0 + 17, y0 + 17), (x1 - 17, y0 + 17), (x0 + 17, y1 - 17), (x1 - 17, y1 - 17)):
                draw.ellipse((px - 3.4, py - 3.4, px + 3.4, py + 3.4), fill=(22, 24, 31))
                draw.point((px - 1, py - 1), fill=(206, 214, 230))
            # Desgaste central: mancha clara suave e alguns riscos finos.
            if rng.random() < 0.55:
                mx = x0 + celula // 2 + int(rng.normal(0, 14))
                my = y0 + celula // 2 + int(rng.normal(0, 14))
                draw.ellipse((mx - 11, my - 7, mx + 11, my + 7), fill=(96, 102, 124))
            for _ in range(3):
                x = x0 + int(rng.random() * celula)
                y = y0 + int(rng.random() * celula)
                draw.line((x, y, x + int(rng.normal(0, 14)), y + int(rng.normal(0, 14))), fill=int(110 + 70 * rng.random()), width=1)
    # Estalo/filigrana fina: pontos discretos de rebites em cruz.
    for linha in range(5):
        for coluna in range(5):
            x = coluna * celula
            y = linha * celula
            draw.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=(172, 180, 200))
    return salvar("paineis_disco_procedural.png", im)


def gerar_feixe_ruido():
    """256×512: filamentos verticais suaves e curvos (canal R), como no feixe do disco."""
    rng = np.random.default_rng(20261105)
    largura, altura = 256, 512
    # Filamentos finos e alongados: grade muito esparsa na vertical, estreita na horizontal.
    filamentos = ruido((altura, largura), (64, 11), rng)
    filamentos = (filamentos - filamentos.mean()) / max(filamentos.std(), 1e-6)
    filamentos = 1.0 / (1.0 + np.exp(-1.5 * filamentos))  # sigmoid: filamentos macios, sem estalo seco
    # Curvatura lenta na horizontal, como fitas de luz curvadas.
    ondulacao = ruido((altura, largura), (120, 64), rng)
    curvatura = np.sin(np.linspace(0.0, math.pi * 1.6, altura, dtype=np.float32))[:, None] * (ondulacao - 0.5) * 0.35
    filamentos = np.clip(filamentos + curvatura, 0.0, 1.0)
    # Envelope vertical: mais brilho no meio do cone.
    vertical = np.clip(np.sin(np.linspace(0.0, math.pi, altura, dtype=np.float32)), 0.0, None) ** 1.35
    imagem = filamentos * (0.38 + 0.62 * vertical[:, None])
    imagem = (imagem**1.25) * 255.0
    return salvar("feixe_ruido_procedural.png", Image.fromarray(imagem.astype(np.uint8), "L").convert("RGB"))


GERADORES = {
    "ceu_estrelado": gerar_ceu_estrelado,
    "lua": gerar_lua,
    "espuma": gerar_espuma,
    "pintura_submarino": gerar_pintura_submarino,
    "paineis_disco": gerar_paineis_disco,
    "feixe_ruido": gerar_feixe_ruido,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="gera em pasta temporária e valida sem sobrescrever nada")
    parser.add_argument("--force", action="store_true", help="sobrescreve os PNGs em assets/textures/")
    parser.add_argument("--out", type=Path, default=None, help="diretório de saída (não toca em assets/textures/)")
    parser.add_argument("--only", type=str, default=None, help="lista separada por vírgula; ex.: --only lua,espuma")
    args = parser.parse_args()

    if args.check and args.force:
        parser.error("--check e --force são mutuamente excludentes")

    nomes = list(GERADORES)
    if args.only:
        nomes = [nome.strip() for nome in args.only.split(",") if nome.strip()]
        desconhecidos = [nome for nome in nomes if nome not in GERADORES]
        if desconhecidos:
            parser.error(f"texturas desconhecidas: {', '.join(desconhecidos)} (disponíveis: {', '.join(GERADORES)})")

    if args.check:
        saida = Path(tempfile.mkdtemp(prefix="texturas_check_"))
    elif args.out is not None:
        saida = args.out
        saida.mkdir(parents=True, exist_ok=True)
    else:
        saida = ASSETS

    gravados = []
    for nome in nomes:
        arquivo, imagem = GERADORES[nome]()
        destino = saida / arquivo
        if destino.exists() and not (args.check or args.out is not None or args.force):
            print(f"PULANDO {destino} (já existe; use --force ou --out)")
            continue
        imagem.save(destino, "PNG")
        gravados.append(destino)
        print(f"OK {destino} ({imagem.size[0]}×{imagem.size[1]})")

    if args.check:
        # Abre tudo de novo e exige conteúdo não uniforme (std > 0).
        for nome in nomes:
            arquivo, imagem = GERADORES[nome]()
            caminho = saida / arquivo
            with Image.open(caminho) as aberta:
                aberta.load()
                assert aberta.size == imagem.size, f"{arquivo}: tamanho inesperado"
                assert aberta.mode == "RGB"
                dados = np.asarray(aberta, dtype=np.float32)
                assert dados.shape == (*aberta.size[::-1], 3)
                assert dados.std() > 1.0, f"{arquivo} ficou uniforme demais (std={dados.std():.2f})"
        print(f"VALIDAÇÃO OK: {len(gravados)} imagem(ns) íntegra(s) em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
