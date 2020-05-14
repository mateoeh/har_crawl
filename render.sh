#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./render.sh <target directory>"
    exit 1
fi

mkdir -p ~/.pandoc/templates
if [ ! -f "$HOME/.pandoc/templates/GitHub.html5" ]; then
    curl https://raw.githubusercontent.com/tajmone/pandoc-goodies/master/templates/html5/github/GitHub.html5 \
        -o "$HOME/.pandoc/templates/GitHub.html5"
fi
find $1 -name '*.md' -exec \
    sh -c \
'echo "$1" && '\
'pandoc -so "${1%.md}.html" "$1" '\
'--metadata title="${1%.md}.html" '\
'-V title:"" '\
'--template="GitHub.html5"'\
    _ {} \;
