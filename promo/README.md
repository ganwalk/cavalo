# Reel "UM SITE PODE SER MAIS QUE UMA PÁGINA"

Vídeo vertical (1080×1920, 30 fps, ~34,7 s) para **Instagram Reels, TikTok e YouTube Shorts**.
Apresenta a solução usada em https://dezerthorse.github.io/cavalo/: uma **experiência interativa na web** feita com
**HTML, CSS, JavaScript, Three.js/WebGL, GLSL e Web Audio API**, e convida quem assiste a levar a mesma ideia para o
próprio projeto (marca, produto, evento, portfólio, museu, escola...).

- `dezert-horse-reel.mp4` — vídeo final (H.264 + AAC, loudness −14 LUFS)
- `capa.png` — sugestão de capa/thumbnail
- `src/` — scripts que geraram o vídeo (captura do site real + trilha + pós-produção glitch)

## Roteiro

Tudo o que aparece foi capturado do site ao vivo (https://dezerthorse.github.io/cavalo/).
A trilha é "Realmente Óbvio" a 152 BPM, e cada corte cai no tempo. Os trechos de código na tela são linhas reais
do `index.htm`, com os valores mudando ao vivo conforme o controle se move.

| Tempo | Legenda | Código na tela (abaixo do painel do site) | Som |
|---|---|---|---|
| 0:00 | UM SITE PODE SER / MAIS QUE UMA PÁGINA. | — | a música começa abafada e se abre |
| 0:03 | ESTE VIROU UMA / EXPERIÊNCIA INTERATIVA. + HTML · CSS · JAVASCRIPT · THREE.JS · WEBGL · GLSL · WEB AUDIO | `<div id="canvas-container">`, `import * as THREE` | impacto: as cores do site acendem |
| 0:06 | JAVASCRIPT LIGA / O TROTE À MÚSICA. | `bgMusic.playbackRate = 0.15` → `2.00` | varispeed |
| 0:09 | WEBGL MOSTRA / O ESQUELETO 3D. | `wireMaterial.opacity` | bitcrush |
| 0:12 | A WEB AUDIO API / DISTORCE O SOM. | `distortionNode.curve = makeDistortionCurve(400)` | overdrive (a mesma curva do site) |
| 0:15 | A LENTE DA CÂMERA / VIRA FILTRO DE ÁUDIO. | `camera.fov`, `fovFilterLow.frequency` | filtros HP/LP (as mesmas fórmulas do site) |
| 0:19 | 10 FREQUÊNCIAS. / CADA UMA COM / SUA COR E SEU SOM. + FREQ 01/10 → 10/10 | `changeTrack(i)`, `--primary-color` | trecho real de cada uma das 10 frequências, um por tempo |
| 0:24 | GLSL + THREE.JS: / 3D DIRETO NO NAVEGADOR. | shader das estrelas, `horseModel.material` | tape-stop e beat-repeat |
| 0:27 | E O SEU PROJETO? / MARCA. PRODUTO. EVENTO. / PORTFÓLIO. MUSEU. ESCOLA. / TAMBÉM PODE VIRAR / UMA EXPERIÊNCIA. | — | tape-stop antes do cartão final |
| 0:31 | EXPERIÊNCIAS INTERATIVAS NA WEB · VEJA FUNCIONANDO: dezerthorse.github.io/cavalo · FALE COM @GANWALK | — | a música volta a se fechar |

O último plano volta ao plano de abertura (cavalo ao longe, som abafado), então o vídeo emenda sem corte quando repete.
As legendas ficam fora das zonas cobertas pela interface das plataformas.

## Texto para postar

**Instagram Reels / TikTok**

> um site pode ser mais que uma página. 🐎
> este aqui virou uma experiência interativa feita com HTML, CSS, JavaScript, Three.js, GLSL e Web Audio API: o trote muda o tempo da música, a lente vira filtro de áudio, e são 10 frequências, cada uma com sua cor e seu som.
> veja funcionando: dezerthorse.github.io/cavalo
> marca, produto, evento, portfólio, museu, escola: o seu projeto também pode virar uma experiência. chama no direct.
>
> #creativecoding #threejs #webgl #webaudio #javascript #experienciainterativa #webdesign #glitchart #interactivedesign #netart

**YouTube Shorts**

- Título: `Um site que vira experiência interativa 🐎 (HTML + JS + WebGL + Web Audio) #shorts`
- Descrição: `JavaScript liga o trote à música, a Web Audio API distorce e filtra o som, e Three.js/GLSL desenham o deserto direto no navegador. Veja funcionando: https://dezerthorse.github.io/cavalo/ · Quer uma experiência assim pro seu projeto? Fale com @ganwalk.`

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
