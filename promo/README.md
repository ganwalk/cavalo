# Reel: sites interativos sob medida

Vídeo vertical (1080×1920, 30 fps, 34,7 s) para Instagram Reels, TikTok e YouTube Shorts. Mostra o site
https://dezerthorse.github.io/cavalo/ funcionando, controle por controle, e oferece o mesmo tipo de site para outros
produtos: um produto que gira na tela, uma exposição que reage ao toque, uma marca com som próprio.

- `dezert-horse-reel.mp4`: vídeo final (H.264 + AAC, loudness −14 LUFS)
- `capa.png`: sugestão de capa
- `src/`: scripts que geraram o vídeo (captura do site real, trilha e pós-produção glitch)

## Roteiro

Todas as imagens foram capturadas do site ao vivo. A trilha é "Realmente Óbvio" a 152 BPM e cada corte cai no tempo.
Abaixo do painel de controle do site aparece um painel com as linhas do `index.htm` que aquele controle executa, com os
valores mudando junto com o slider.

| Tempo | Legenda | Som |
|---|---|---|
| 0:00 | O SEU SITE PODE SER / MAIS QUE SÓ UM SITE. (o último "SITE" com glitch animado) | a música começa abafada e se abre |
| 0:03 | EXPERIÊNCIAS INTERATIVAS / DE IMAGEM E SOM. | impacto, as cores do site acendem |
| 0:06 | SEU PROJETO GANHA / MOVIMENTO E RITMO, | a música acelera e desacelera junto |
| 0:09 | COM AS CORES, A TRILHA / E O JEITO DA SUA MARCA. | bitcrush |
| 0:12 | SEU PÚBLICO MEXE / E A MÚSICA RESPONDE. | overdrive (a mesma curva do site) |
| 0:15 | UM AJUSTE NA LENTE / MUDA TODO O CLIMA. | filtros (as mesmas fórmulas do site) |
| 0:19 | 10 FREQUÊNCIAS, / CADA UMA COM SUA / PRÓPRIA COR. (contador FREQ 01/10 a 10/10) | um trecho de cada frequência por tempo |
| 0:24 | FUNCIONA NO CELULAR, / É SÓ ARRASTAR O DEDO. | tape-stop e beat-repeat |
| 0:27 | DÁ PRA FAZER ISSO / PARA UM PRODUTO / QUE GIRA NA TELA, / UMA EXPOSIÇÃO QUE / REAGE AO TOQUE / OU UMA MARCA / COM SOM PRÓPRIO. | tape-stop antes do cartão final |
| 0:31 | SITES INTERATIVOS SOB MEDIDA · VEJA ESTE PROJETO COMPLETO: dezerthorse.github.io/cavalo · FALE COM @GANWALK | a música volta a se fechar |

O último plano volta ao plano de abertura (cavalo ao longe, som abafado), então o vídeo emenda sem corte quando repete.

## Texto para postar

**Instagram Reels / TikTok**

> neste site, o trote do cavalo controla o tempo da música, a lente da câmera abafa o som e cada uma das 10 frequências tem sua cor.
> veja ao vivo: dezerthorse.github.io/cavalo
> dá pra fazer o mesmo para um produto que gira na tela, uma exposição que reage ao toque ou uma marca com som próprio. me chama no direct.
>
> #siteinterativo #webdesign #creativecoding #3d #design #motiondesign #glitchart #interactivedesign

**YouTube Shorts**

- Título: `Um site onde o trote do cavalo controla a música #shorts`
- Descrição: `Cada controle deste site muda a imagem e o som ao mesmo tempo. Veja ao vivo: https://dezerthorse.github.io/cavalo/ · Sites interativos sob medida para produtos, exposições e marcas: fale com @ganwalk.`

## Como regenerar

Requer Node + Playwright (Chromium) e Python 3 com `numpy scipy pillow imageio-ffmpeg`.

```sh
cd promo/src
# 1. captura quadro a quadro do site real (tempo virtual, 30 fps)
DPR=2 OUT=frames2 node capture2.js
#    post2.py reaproveita os quadros 190 a 568 (cenas dos sliders) de uma captura feita com
#    `DPR=2 OUT=frames node capture.js`. Para capturar tudo de uma vez, rode capture2.js sem SKIP
#    e ajuste REUSE em post2.py.
# 2. trilha (precisa de audio.f32 e tracks/N.f32, decodificados dos mp3 do site)
python3 audio2.py
# 3. glitch, legendas, painel de código e mux
python3 post2.py dezert-horse-reel.mp4
```
