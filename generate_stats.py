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
        ("star",      "Stars",         str(stats["stars"])),
        ("commits",   "Commits",       str(stats["commits"])),
        ("prs",       "Pull Requests", str(stats["prs"])),
        ("issues",    "Issues",        str(stats["issues"])),
        ("repos",     "Repositórios",  str(stats["repos"])),
        ("followers", "Seguidores",    str(stats["followers"])),
    ]

    # Ícones SVG para cada métrica
    icon_paths = {
        "star":      "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
        "commits":   "M9 3H7v4H3v2h4v10h2V9h4V7H9V3zm8 8h-2v2h-2v2h2v4h2v-4h2v-2h-2v-2z",
        "prs":       "M6 3a3 3 0 110 6 3 3 0 010-6zm12 0a3 3 0 110 6 3 3 0 010-6zM6 7a1 1 0 100-2 1 1 0 000 2zm12 0a1 1 0 100-2 1 1 0 000 2zm-1 3v7l-2-2-2 2V10H17zM7 10v2a5 5 0 005 5h1v2h-1a7 7 0 01-7-7v-2h2z",
        "issues":    "M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 100-16 8 8 0 000 16zm-1-5h2v2h-2v-2zm0-8h2v6h-2V7z",
        "repos":     "M3 3h18v2H3V3zm0 4h18v2H3V7zm0 4h12v2H3v-2zm0 4h12v2H3v-2zm0 4h18v2H3v-2z",
        "followers": "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z",
    }

    cells = []
    for i, (key, label, value) in enumerate(items):
        col = i % 3
        row = i // 3
        cx  = 70  + col * 150
        cy  = 105 + row * 75
        path = icon_paths[key]

        cells.append(f"""
  <g transform="translate({cx - 26},{cy - 28}) scale(0.9)">
    <path d="{path}" fill="{GOLD}" />
  </g>
  <text x="{cx + 6}" y="{cy - 6}" font-size="24" fill="{WHITE}"
        font-family="'Courier New',monospace" font-weight="bold">{value}</text>
  <text x="{cx + 6}" y="{cy + 16}" font-size="14" fill="{TEXT}"
        font-family="'Courier New',monospace">{label}</text>""")

    return f"""<svg width="520" height="230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="{GOLD}"  stop-opacity="1"/>
      <stop offset="100%" stop-color="{GOLD2}" stop-opacity="1"/>
    </linearGradient>
  </defs>

  <rect width="520" height="230" rx="12" fill="{BG}"/>
  <rect x="1" y="1" width="518" height="228" rx="12" fill="none"
        stroke="{GOLD}" stroke-width="1" stroke-opacity="0.5"/>
  <rect width="520" height="4" rx="2" fill="url(#g1)"/>

  <text x="28" y="50" font-size="18" fill="{GOLD}"
        font-family="'Courier New',monospace" font-weight="bold">
    Felipe Cardoso — GitHub Stats
  </text>
  <line x1="28" y1="64" x2="492" y2="64"
        stroke="{GOLD}" stroke-width="0.6" stroke-opacity="0.4"/>

  {"".join(cells)}
</svg>"""


# ── Gera SVG: Top Languages Card ────────────────────────────────────────────────
def make_langs_svg(langs):
    bars = []
    y = 90
    for lang in langs:
        bar_fill  = lang["color"] if lang["color"] else GOLD
        bar_width = max(int(lang["pct"] / 100 * 430), 8)

        bars.append(f"""
  <text x="28" y="{y}" font-size="17" fill="{TEXT}"
        font-family="'Courier New',monospace">{lang['name']}</text>
  <text x="488" y="{y}" font-size="17" fill="{GOLD}"
        font-family="'Courier New',monospace" text-anchor="end">{lang['pct']}%</text>
  <rect x="28" y="{y + 8}" width="460" height="10" rx="5" fill="{BORDER}"/>
  <rect x="28" y="{y + 8}" width="{bar_width}" height="10" rx="5" fill="{bar_fill}"/>""")
        y += 42

    height = 68 + len(langs) * 42 + 20

    return f"""<svg width="520" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="{GOLD}"  stop-opacity="1"/>
      <stop offset="100%" stop-color="{GOLD2}" stop-opacity="1"/>
    </linearGradient>
  </defs>

  <rect width="520" height="{height}" rx="12" fill="{BG}"/>
  <rect x="1" y="1" width="518" height="{height - 2}" rx="12" fill="none"
        stroke="{GOLD}" stroke-width="1" stroke-opacity="0.5"/>
  <rect width="520" height="4" rx="2" fill="url(#g2)"/>

  <text x="28" y="50" font-size="18" fill="{GOLD}"
        font-family="'Courier New',monospace" font-weight="bold">
    Linguagens Mais Usadas
  </text>
  <line x1="28" y1="64" x2="492" y2="64"
        stroke="{GOLD}" stroke-width="0.6" stroke-opacity="0.4"/>

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
