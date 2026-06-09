# Paper

This directory contains the LaTeX source exported from Overleaf for the Synth Benchmarking Pipeline paper.

## Source of Truth

The tracked source file is `main.tex`. If the Overleaf project later grows to include figures, bibliography files, style files, or additional `.tex` files, place them in this directory and update any relative paths accordingly.

## Local Build

If a TeX distribution is installed locally, build with:

```sh
cd paper
latexmk -pdf main.tex
```

The generated PDF and auxiliary LaTeX build files are intentionally ignored by git.
