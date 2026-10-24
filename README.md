# 大模型入门教材 LaTeX 项目

由《大模型入门路线教材_20261016.docx》转换，保留教材原文内容；这是格式迁移，未对技术论述做事实校订。

## 编译

安装 TeX Live 2024 或更新版本，在项目目录运行：

```sh
latexmk -xelatex main.tex
```

输出为 `build/main.pdf`。也可在 Overleaf 上传本项目，选择 XeLaTeX 编译器和 `main.tex` 主文件。正常编辑、编译无需 Python 或 Pandoc。

## 文件

- `main.tex`：主文件、宏包及章节入口。
- `preamble.tex`：公共排版设置，由主文件载入。
- `chapters/ch01.tex` 至 `ch09.tex`：九章正文，每章可独立编辑。
- `chapters/frontmatter-*.tex`：原封面说明及前言。
- `chapters/appendix.tex`：附录与术语表。
- `assets/media/`：原文件全部 23 个图片资源。SVG 与其 PNG 配对版本均保留，编译使用 Word 内嵌的 PNG 版本，共 13 处图像。
- `source.json`：原文经 Pandoc 提取的中间表示，供追溯和重新生成。
- `tools/build_source.py`：从中间表示重新生成 TeX，依赖 Python 与 Pandoc 3.6 或更新版本。重新生成会覆盖手工修改的 TeX 文件。

重新生成命令：

```sh
python tools/build_source.py
```

Pandoc 不在 PATH 时，通过 `PANDOC` 环境变量指定可执行文件。

## 转换说明

正文、表格与数学公式为可编辑的 LaTeX；原插图保留为图片。原目录的 Word 页码被自动目录替代，章、节编号由 LaTeX 生成。原参考资料链接保留在对应小节，未另造 BibTeX 条目。去除了链接的 Word 下划线，保留可点击链接；少量 Unicode 上下标转换成数学排版，以避免缺字。页眉页脚和分页由 LaTeX 重新排版，页码与 Word 不同。
