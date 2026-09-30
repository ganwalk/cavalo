# DEZERT HORSE — reel "ISSO NÃO É UM SITE"

Vídeo vertical (1080×1920, 30 fps, ~31,6 s) para **Instagram Reels, TikTok e YouTube Shorts**,
chamando o público para experimentar https://dezerthorse.github.io/cavalo/

- `dezert-horse-reel.mp4` — vídeo final (H.264 + AAC, loudness −14 LUFS)
- `capa.png` — sugestão de capa/thumbnail
- `src/` — scripts que geraram o vídeo (captura do site real + trilha + pós-produção glitch)

## Conceito

O site é tratado como um **instrumento**: cada controle do painel mexe na imagem *e* no som ao mesmo tempo.
Tudo o que aparece foi capturado do site ao vivo (Three.js real, painel real, cores reais de cada faixa).
A trilha é "Realmente Óbvio" a 152 BPM, e cada corte cai no tempo.

| Tempo | Cena | Imagem | Som |
|---|---|---|---|
| 0:00 | Carregamento | "ISSO NÃO É UM SITE. / É UM INSTRUMENTO." | rádio, estática e bipes de carregamento |
| 0:03 | INICIAR TRANSMISSÃO | toque, flash, câmera mergulha no deserto | a fita acelera, impacto, a música entra |
| 0:06 | Velocidade do trote | slider 100 → 15 → 200 % com rastro de movimento | varispeed (mesmo `playbackRate` do site) |
| 0:09 | Estrutura de dados | wireframe + faixa de memória corrompida | bitcrush |
| 0:12 | Alongamento surreal | cavalo esticado 4× | overdrive (a mesma curva do WaveShaper do site) |
| 0:15 | Distorção de lente (FOV) | 40 → 120 → 20 com aberração cromática | filtros HP/LP (as mesmas fórmulas do site) |
| 0:19 | Frequência | um corte por tempo e 9 faixas/cores | trechos reais de cada faixa do álbum, com chiado de sintonia |
| 0:22 | Modo espectro + câmera | órbita 360°, espectro liga e desliga | tape-stop e beat-repeat |
| 0:25 | CTA | EXPERIMENTE · dezerthorse.github.io/cavalo · [ LINK NA BIO ] | a música volta a virar rádio |
| 0:31 | Loop | volta à tela INICIAR TRANSMISSÃO | mesma estática do início (o loop fecha sem emenda) |

As legendas ficam fora das zonas cobertas pela interface das plataformas (topo ~12 %, base ~20 %, lateral direita).

## Texto para postar

**Instagram Reels / TikTok**

> isso não é um site. é um instrumento. 🐎
> acelera o trote, estica o cavalo, abre a lente, sintoniza as 10 frequências: cada controle mexe na imagem e no som.
> entra e pilota: dezerthorse.github.io/cavalo (link na bio)
> álbum de DEZERT HORSE disponível em todas as plataformas.
>
> #dezerthorse #glitchart #creativecoding #threejs #webgl #musicaindependente #experimentalmusic #netart #interactiveart #novamusicabrasileira

**YouTube Shorts**

- Título: `ISSO NÃO É UM SITE 🐎 pilote o álbum de DEZERT HORSE #shorts`
- Descrição: `Um cavalo, um deserto e 10 frequências. Cada controle do site muda a imagem e o som. Experimente: https://dezerthorse.github.io/cavalo/`

## Como regenerar

Requer Node + Playwright (Chromium), Python 3 com `numpy scipy pillow imageio-ffmpeg`.

```sh
cd promo/src
# 1. captura quadro a quadro do site real (tempo virtual, 30 fps)
DPR=2 OUT=frames node capture.js
# 2. trilha (precisa de audio.f32 e tracks/N.f32, decodificados dos mp3 do site)
python3 audio.py
# 3. glitch + legendas + mux
python3 post.py dezert-horse-reel.mp4
```
