#!/bin/bash
# usage: sn_dl.sh <target_path> <image_url> [referer]
OUT="$1"; URL="$2"; REF="${3:-https://baike.baidu.com/}"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
mkdir -p "$(dirname "$OUT")"
curl -s -L --ssl-no-revoke -m 60 -A "$UA" -H "Referer: $REF" -o "$OUT" "$URL"
SZ=$(stat -c%s "$OUT" 2>/dev/null || echo 0)
if [ "$SZ" -lt 5120 ]; then echo "FAIL size=$SZ $OUT"; rm -f "$OUT"; exit 1; fi
python -c "
import sys
from PIL import Image
try:
    im=Image.open(r'''$OUT'''); im.load()
    print('OK', im.size, im.format)
except Exception as e:
    print('BAD', e); sys.exit(2)
" || { rm -f "$OUT"; exit 1; }
