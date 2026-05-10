"""
Gera dois SVGs com as estatísticas do GitHub:
  - github_stats.svg  → commits, stars, PRs, issues, repos, seguidores
  - top_langs.svg     → linguagens mais usadas (barra de progresso)

Executado automaticamente pelo GitHub Actions (.github/workflows/update-stats.yml)
"""

import os
import sys
import requests

USERNAME = "FelipeCard0so"
TOKEN    = os.environ.get("GITHUB_TOKEN")

# ── Paleta ─────────────────────────────────────────────────────────────────────
GOLD    = "#d4a017"
GOLD2   = "#f0c040"
BG      = "#0d1117"
TEXT    = "#a8b2d8"
WHITE   = "#ffffff"
BORDER  = "#21262d"


# ── Busca os dados via GraphQL ──────────────────────────────────────────────────
def fetch_stats():
    if not TOKEN:
        print("ERRO: variável GITHUB_TOKEN não encontrada.")
        sys.exit(1)

    headers = {
        "Authorization": f"bearer {TOKEN}",
        "Content-Type":  "application/json",
    }

    query = """
    query($username: String!) {
      user(login: $username) {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
      }
    }
    """

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers,
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"ERRO na API: {resp.status_code} — {resp.text}")
        sys.exit(1)

    data = resp.json()
    if "errors" in data:
        print(f"ERRO GraphQL: {data['errors']}")
        sys.exit(1)

    user  = data["data"]["user"]
    repos = user["repositories"]["nodes"]

    stats = {
        "stars":     sum(r["stargazerCount"] for r in repos),
        "commits":   user["contributionsCollection"]["totalCommitContributions"],
        "prs":       user["contributionsCollection"]["totalPullRequestContributions"],
        "issues":    user["contributionsCollection"]["totalIssueContributions"],
        "repos":     user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
    }

    # Agrega tamanho de linguagens entre todos os repos
    lang_map = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name  = edge["node"]["name"]
            color = edge["node"]["color"] or "#888888"
            size  = edge["size"]
            if name not in lang_map:
                lang_map[name] = {"size": 0, "color": color}
            lang_map[name]["size"] += size

    total = sum(v["size"] for v in lang_map.values()) or 1
    langs = sorted(
        [
            {"name": k, "color": v["color"], "pct": round(v["size"] / total * 100, 1)}
            for k, v in lang_map.items()
        ],
        key=lambda x: x["pct"],
        reverse=True,
    )[:6]

    return stats, langs


# ── Gera SVG: Stats Card ────────────────────────────────────────────────────────
def make_stats_svg(stats):
    items = [
        ("*", "Stars",        str(stats["stars"])),
        ("#", "Commits",      str(stats["commits"])),
        ("~", "Pull Requests",str(stats["prs"])),
        ("!", "Issues",       str(stats["issues"])),
        ("@", "Repositórios", str(stats["repos"])),
        ("+", "Seguidores",   str(stats["followers"])),
    ]

    # Ícones SVG simples para cada item
    icons = {
        "*": "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
        "#": "M9 3H7v4H3v2h4v10h2V9h4V7H9V3zm8 8h-2v2h-2v2h2v4h2v-4h2v-2h-2v-2z",
        "~": "M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3",
        "!": "M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 100-16 8 8 0 000 16zm-1-5h2v2h-2v-2zm0-8h2v6h-2V7z",
        "@": "M3 3h18v2H3V3zm0 4h18v2H3V7zm0 4h12v2H3v-2zm0 4h12v2H3v-2zm0 4h18v2H3v-2z",
        "+": "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z",
    }

    cells = []
    for i, (key, label, value) in enumerate(items):
        col = i % 3
        row = i // 3
        cx  = 55  + col * 135
        cy  = 85  + row * 60
        path = icons[key]

        cells.append(f"""
  <!-- {label} -->
  <g transform="translate({cx - 20},{cy - 22}) scale(0.75)">
    <path d="{path}" fill="{GOLD}" />
  </g>
  <text x="{cx + 4}" y="{cy - 8}" font-size="18" fill="{WHITE}"
        font-family="'Courier New',monospace" font-weight="bold">{value}</text>
  <text x="{cx + 4}" y="{cy + 10}" font-size="11" fill="{TEXT}"
        font-family="'Courier New',monospace">{label}</text>""")

    return f"""<svg width="495" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="{GOLD}"  stop-opacity="1"/>
      <stop offset="100%" stop-color="{GOLD2}" stop-opacity="1"/>
    </linearGradient>
  </defs>

  <rect width="495" height="200" rx="10" fill="{BG}"/>
  <rect x="1" y="1" width="493" height="198" rx="10" fill="none"
        stroke="{GOLD}" stroke-width="0.8" stroke-opacity="0.4"/>
  <rect width="495" height="3" rx="1.5" fill="url(#g1)"/>

  <text x="25" y="40" font-size="15" fill="{GOLD}"
        font-family="'Courier New',monospace" font-weight="bold">
    Felipe Cardoso — GitHub Stats
  </text>
  <line x1="25" y1="52" x2="470" y2="52"
        stroke="{GOLD}" stroke-width="0.5" stroke-opacity="0.35"/>

  {"".join(cells)}
</svg>"""


# ── Gera SVG: Top Languages Card ────────────────────────────────────────────────
def make_langs_svg(langs):
    bars = []
    y = 78
    for lang in langs:
        bar_fill  = lang["color"] if lang["color"] else GOLD
        bar_width = max(int(lang["pct"] / 100 * 420), 6)

        bars.append(f"""
  <text x="25" y="{y}" font-size="12" fill="{TEXT}"
        font-family="'Courier New',monospace">{lang['name']}</text>
  <text x="465" y="{y}" font-size="12" fill="{GOLD}"
        font-family="'Courier New',monospace" text-anchor="end">{lang['pct']}%</text>
  <rect x="25" y="{y + 6}" width="440" height="8" rx="4" fill="{BORDER}"/>
  <rect x="25" y="{y + 6}" width="{bar_width}" height="8" rx="4" fill="{bar_fill}"/>""")
        y += 34

    height = 58 + len(langs) * 34 + 18

    return f"""<svg width="495" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="{GOLD}"  stop-opacity="1"/>
      <stop offset="100%" stop-color="{GOLD2}" stop-opacity="1"/>
    </linearGradient>
  </defs>

  <rect width="495" height="{height}" rx="10" fill="{BG}"/>
  <rect x="1" y="1" width="493" height="{height - 2}" rx="10" fill="none"
        stroke="{GOLD}" stroke-width="0.8" stroke-opacity="0.4"/>
  <rect width="495" height="3" rx="1.5" fill="url(#g2)"/>

  <text x="25" y="40" font-size="15" fill="{GOLD}"
        font-family="'Courier New',monospace" font-weight="bold">
    Linguagens Mais Usadas
  </text>
  <line x1="25" y1="52" x2="470" y2="52"
        stroke="{GOLD}" stroke-width="0.5" stroke-opacity="0.35"/>

  {"".join(bars)}
</svg>"""


# ── Main ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Buscando dados de @{USERNAME}...")
    stats, langs = fetch_stats()

    print(f"  Stars: {stats['stars']}  Commits: {stats['commits']}  "
          f"PRs: {stats['prs']}  Issues: {stats['issues']}  "
          f"Repos: {stats['repos']}  Seguidores: {stats['followers']}")
    print(f"  Linguagens: {[l['name'] for l in langs]}")

    with open("github_stats.svg", "w", encoding="utf-8") as f:
        f.write(make_stats_svg(stats))
    print("✅ github_stats.svg gerado")

    with open("top_langs.svg", "w", encoding="utf-8") as f:
        f.write(make_langs_svg(langs))
    print("✅ top_langs.svg gerado")
