"""Generate report/report.tex from the Markdown report using standard LaTeX packages.

Run this, then compile report/report.tex twice with pdflatex.
"""

from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
md = (root / "report/report.md").read_text()
trans = str.maketrans(
    {"—": "-", "–": "-", "→": "->", "≥": ">=", "≤": "<=", "’": "'", "‘": "'", "“": '"', "”": '"'}
)


def esc(s):
    s = s.translate(trans)
    return "".join(
        {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
            "<": r"\textless{}",
            ">": r"\textgreater{}",
        }.get(c, c)
        for c in s
    )


def inline(s):
    parts = re.split(r"(\[[^\]]+\]\(https?://[^)]+\)|`[^`]+`|\*\*[^*]+\*\*)", s)
    out = []
    for p in parts:
        if p.startswith("`"):
            t = esc(p[1:-1]).replace("/", r"/\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
            out.append(r"\texttt{" + t + "}")
        elif p.startswith("**"):
            out.append(r"\textbf{" + esc(p[2:-2]) + "}")
        elif p.startswith("["):
            m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", p)
            out.append(r"\href{" + m[2] + "}{" + esc(m[1]) + "}")
        else:
            out.append(esc(p))
    return "".join(out)


header = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=1.8cm]{geometry}
\usepackage{array,tabularx,booktabs}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage[colorlinks=true,urlcolor=blue!50!black,linkcolor=black]{hyperref}
\hypersetup{pdftitle={CS3081 Cloud Computing Mini Project},pdfauthor={Lokesh Yadav, 230101039}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\emergencystretch}{3em}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
\titleformat{\section}{\large\bfseries}{}{0pt}{}
\titlespacing*{\section}{0pt}{11pt}{5pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small CS3081 - Cloud Computing}
\fancyhead[R]{\small Lokesh Yadav - 230101039}
\fancyfoot[C]{\small\thepage}
\setlength{\headheight}{14pt}
\begin{document}
"""
lines = md.splitlines()
body = []
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        i += 1
        continue
    if line.startswith("# "):
        body += [r"\begin{center}{\LARGE\bfseries " + inline(line[2:]) + r"}\end{center}"]
        i += 1
        continue
    if line.startswith("## "):
        body += [r"\section{" + inline(line[3:]) + "}"]
        i += 1
        continue
    if line.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([s.strip() for s in lines[i].strip("|").split("|")])
            i += 1
        n = len(rows[0])
        body.append(
            r"\begin{center}\small\begin{tabularx}{\linewidth}{@{}"
            + (">{\\raggedright\\arraybackslash}X" * n)
            + r"@{}}\toprule"
        )
        body.append(" & ".join(r"\textbf{" + inline(c) + "}" for c in rows[0]) + r" \\ \midrule")
        for row in rows[2:]:
            body.append(" & ".join(inline(c) for c in row) + r" \\")
        body.append(r"\bottomrule\end{tabularx}\end{center}")
        continue
    para = []
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|")):
        if lines[i].endswith("  "):
            para.append(inline(lines[i].strip()) + r"\\")
            i += 1
        else:
            para.append(inline(lines[i]))
            i += 1
    body.append(" ".join(para) + "\n")
(root / "report/report.tex").write_text(header + "\n\n".join(body) + "\n\\end{document}\n")
