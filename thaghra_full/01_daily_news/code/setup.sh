#!/usr/bin/env bash
# يثبت خطوط ثغرة (Readex Pro + IBM Plex Mono)
set -e
d="$(mktemp -d)"; cd "$d"
git clone --depth 1 --filter=blob:none --sparse https://github.com/google/fonts.git gf
cd gf && git sparse-checkout set ofl/readexpro ofl/ibmplexmono
mkdir -p ~/.fonts && cp ofl/readexpro/*.ttf ofl/ibmplexmono/IBMPlexMono-Medium.ttf ~/.fonts/ && fc-cache -f
fc-list | grep -i readex
