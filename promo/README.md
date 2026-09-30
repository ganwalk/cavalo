# DEZERT HORSE — reel "UM ÁLBUM MERECE MAIS QUE UM LINK"

Vídeo vertical (1080×1920, 30 fps, ~34,7 s) para **Instagram Reels, TikTok e YouTube Shorts**.
Conta a solução do projeto: usar **HTML, CSS, JavaScript, Three.js/WebGL, GLSL e Web Audio API** para transformar
o álbum de DEZERT HORSE em um site interativo, e convida quem assiste a fazer o mesmo no próprio projeto.

- `dezert-horse-reel.mp4` — vídeo final (H.264 + AAC, loudness −14 LUFS)
- `capa.png` — sugestão de capa/thumbnail
- `src/` — scripts que geraram o vídeo (captura do site real + trilha + pós-produção glitch)

## Roteiro

Tudo o que aparece foi capturado do site ao vivo (https://dezerthorse.github.io/cavalo/).
A trilha é "Realmente Óbvio" a 152 BPM, e cada corte cai no tempo. Os trechos de código na tela são linhas reais
do `index.htm`, com os valores mudando ao vivo conforme o controle se move.

| Tempo | Legenda | Código na tela | Som |
|---|---|---|---|
| 0:00 | UM ÁLBUM MERECE / MAIS QUE UM LINK. | — | a música começa abafada e se abre |
| 0:03 | ENTÃO VIROU / UM SITE INTERATIVO. + HTML · CSS · JAVASCRIPT · THREE.JS · WEBGL · GLSL · WEB AUDIO | `<div id="canvas-container">`, `import * as THREE` | impacto: as cores do site acendem |
| 0:06 | JAVASCRIPT LIGA / O TROTE À MÚSICA. | `bgMusic.playbackRate = 0.15` → `2.00` | varispeed |
| 0:09 | WEBGL MOSTRA / O ESQUELETO 3D. | `wireMaterial.opacity` | bitcrush |
| 0:12 | A WEB AUDIO API / DISTORCE O SOM. | `distortionNode.curve = makeDistortionCurve(400)` | overdrive (a mesma curva do site) |
| 0:15 | A LENTE DA CÂMERA / VIRA FILTRO DE ÁUDIO. | `camera.fov`, `fovFilterLow.frequency` | filtros HP/LP (as mesmas fórmulas do site) |
| 0:19 | 10 FAIXAS. / 10 FREQUÊNCIAS. / CADA UMA COM SUA COR. + FREQ 01/10 → 10/10 | `changeTrack(i)`, `--primary-color` | trecho real de cada uma das 10 faixas, um por tempo |
| 0:24 | GLSL + THREE.JS: / 3D DIRETO NO NAVEGADOR. | shader das estrelas, `horseModel.material` | tape-stop e beat-repeat |
| 0:27 | E O SEU PROJETO? / ÁLBUM. CLIPE. SHOW. / EXPOSIÇÃO. MARCA. / TAMBÉM PODE VIRAR / UMA EXPERIÊNCIA. | — | tape-stop antes do cartão final |
| 0:31 | SITES INTERATIVOS PARA ARTISTAS · VEJA FUNCIONANDO: dezerthorse.github.io/cavalo · FALE COM @GANWALK | — | a música volta a se fechar |

O último plano volta ao plano de abertura (cavalo ao longe, som abafado), então o vídeo emenda sem corte quando repete.
As legendas ficam fora das zonas cobertas pela interface das plataformas.

## Texto para postar

**Instagram Reels / TikTok**

> um álbum merece mais que um link. 🐎
> o disco de DEZERT HORSE virou um site interativo feito com HTML, CSS, JavaScript, Three.js, GLSL e Web Audio API: o trote muda o tempo da música, a lente vira filtro, e são 10 faixas em 10 frequências.
> veja funcionando: dezerthorse.github.io/cavalo
> quer algo assim pro seu álbum, clipe, show ou marca? chama no direct.
>
> #creativecoding #threejs #webgl #webaudio #javascript #siteinterativo #glitchart #musicaindependente #dezerthorse #netart

**YouTube Shorts**

- Título: `Um álbum que vira site interativo 🐎 (HTML + JS + WebGL + Web Audio) #shorts`
- Descrição: `O álbum de DEZERT HORSE virou um site interativo: JavaScript liga o trote à música, a Web Audio API distorce e filtra o som, e Three.js/GLSL desenham o deserto no navegador. Veja funcionando: https://dezerthorse.github.io/cavalo/ · Quer um desses pro seu projeto? Fale com @ganwalk.`

## Como regenerar

Requer Node + Playwright (Chromium) e Python 3 com `numpy scipy pillow imageio-ffmpeg`.

```sh
cd promo/src
# 1. captura quadro a quadro do site real (tempo virtual, 30 fps)
DPR=2 OUT=frames2 node capture2.js
#    (post2.py reaproveita os quadros 190–568, as cenas dos sliders, de uma captura feita com
#     `DPR=2 OUT=frames node capture.js`; para capturar tudo de uma vez, rode capture2.js sem SKIP e
#     ajuste REUSE em post2.py)
# 2. trilha (precisa de audio.f32 e tracks/N.f32, decodificados dos mp3 do site)
python3 audio2.py
# 3. glitch + legendas + código ao vivo + mux
python3 post2.py dezert-horse-reel.mp4
```
