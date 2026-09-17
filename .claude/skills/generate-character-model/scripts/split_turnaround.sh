#!/usr/bin/env bash
# 三面図(front/side/back が1枚に並んだ画像)を、API/UIに渡せる個別画像へ切り出す。
#
# なぜ必要か: 複数のビューが1枚に結合された画像をそのまま image-to-3D に入れると、
# 並んだ被写体がすべて1つのメッシュとして生成されてしまう(パンダが3頭並んだ
# メッシュになる)。必ず1体ずつに切り出してから渡すこと。
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: split_turnaround.sh <input-image> <output-dir> [panels]

  input-image  front/side/back が横に並んだ1枚の画像
  output-dir   切り出した画像の保存先
  panels       パネル数(既定: 3)

出力: <output-dir>/ref-front.png, ref-side.png, ref-back.png
      (panels が 3 以外の場合は ref-1.png, ref-2.png, ... )

注意: 上下の余白(タイトルや注釈)は --margin-top / --margin-bottom で調整する。
      切り出し後は必ず目視で確認すること(ラベルや隣のパネルが混入しやすい)。
EOF
}

if [[ $# -lt 2 ]]; then usage; exit 1; fi

INPUT="$1"
OUTDIR="$2"
PANELS="${3:-3}"

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick(magick)が必要。brew install imagemagick" >&2
  exit 1
fi
if [[ ! -f "$INPUT" ]]; then
  echo "画像が見つからない: $INPUT" >&2
  exit 1
fi

mkdir -p "$OUTDIR"

# magick identify は末尾に改行を付けないため、read がEOFで非ゼロを返す。
# set -e で落ちないよう明示的に区切って読む。
W=$(magick identify -format "%w" "$INPUT")
H=$(magick identify -format "%h" "$INPUT")
echo "入力: ${W}x${H}, パネル数: ${PANELS}"

# 上下の余白を1割ずつ落とす(タイトル・キャプション対策の既定値)
MT=$(( H / 10 ))
MH=$(( H - MT * 2 ))
PW=$(( W / PANELS ))
# パネル境界の枠線を避けるため左右を少し内側に寄せる
INSET=$(( PW / 40 ))
CW=$(( PW - INSET * 2 ))

NAMES=(front side back)
for ((i = 0; i < PANELS; i++)); do
  X=$(( PW * i + INSET ))
  if [[ $PANELS -eq 3 ]]; then
    NAME="ref-${NAMES[$i]}.png"
  else
    NAME="ref-$((i + 1)).png"
  fi
  magick "$INPUT" -crop "${CW}x${MH}+${X}+${MT}" +repage "$OUTDIR/$NAME"
  echo "  -> $OUTDIR/$NAME (${CW}x${MH})"
done

echo
echo "切り出した画像を目視で確認すること。ラベルや隣のパネルが写り込んでいたら"
echo "スクリプト内の MT / INSET を調整して再実行する。"
