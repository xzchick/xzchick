#!/usr/bin/env python3
"""Generate the ENVY profile panels, project cards, buttons and dividers as SVGs.

Reads my-settings/envy-panels.json and live data from the GitHub GraphQL API.
Needs GITHUB_TOKEN in the environment. Standard library only.
"""
import datetime as dt
import json
import math
import os
import sys
import textwrap
import urllib.request
from xml.sax.saxutils import escape

W, H = 720, 320
BG = "#050713"
INK = "#f2f4ff"
MUTED = "#b9c3df"
CYAN = "#35e8ff"
CYAN_SOFT = "#6ceaff"
PINK = "#ff3db4"
LAVENDER = "#ac8cff"
VIOLET = "#8547e8"
GRID = "#1a1f3d"
# Theme colors for language bars, most-used first
LANG_COLORS = [PINK, CYAN, LAVENDER, VIOLET, "#9bf7ff", "#5a6290"]
FONT = 'font-family="Arial, Helvetica, sans-serif"'
MONO = 'font-family="Menlo, Consolas, \'Courier New\', monospace"'
REDUCED = "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    following { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        name description stargazerCount pushedAt
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "envy-panels"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def frame(title, desc, body, w=W, h=H, rx=20, css=""):
    """Wrap content in the shared ENVY card background and neon edge."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title description">
  <title id="title">{escape(title)}</title>
  <desc id="description">{escape(desc)}</desc>
  <defs>
    <linearGradient id="edge"><stop stop-color="{PINK}" stop-opacity=".55"/><stop offset=".5" stop-color="{LAVENDER}" stop-opacity=".2"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".65"/></linearGradient>
    <linearGradient id="neon"><stop stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
    <radialGradient id="cloud"><stop stop-color="#0d5666" stop-opacity=".45"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <radialGradient id="pink"><stop stop-color="#a71c7d" stop-opacity=".2"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <clipPath id="clip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{rx}"/></clipPath>
  </defs>
  <style>.signal{{animation:pulse 7s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:.95}}}}{css}{REDUCED}</style>
  <g clip-path="url(#clip)">
    <rect width="{w}" height="{h}" fill="{BG}"/>
    <ellipse cx="{w - 80}" cy="{h // 2}" rx="{min(260, w * .6):.0f}" ry="200" fill="url(#cloud)"/>
    <ellipse cx="90" cy="{h - 10}" rx="{min(320, w * .7):.0f}" ry="210" fill="url(#pink)"/>
    <g fill="#a8c7ed" opacity=".3"><circle cx="{w * .62:.0f}" cy="26" r="1"/><circle cx="{w * .78:.0f}" cy="{h - 24}" r="1"/><circle cx="{w - 30}" cy="43" r="1.2"/><circle cx="{w * .55:.0f}" cy="{h - 18}" r=".8"/></g>
{body}
  </g>
  <rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
"""


def card(title, kicker, desc, body, w=W, h=H, css=""):
    """A framed panel with the ENVY kicker, title and accent rule."""
    header = f"""    <g {FONT}>
      <text x="34" y="43" font-size="14" letter-spacing="2.6" font-weight="600" fill="{CYAN_SOFT}">{escape(kicker)}</text>
      <text x="32" y="80" font-size="28" letter-spacing="1" font-weight="700" fill="{INK}">{escape(title)}</text>
    </g>
    <path d="M34 96h55" stroke="{PINK}" stroke-width="2"/>
    <path d="M95 96h24" stroke="{LAVENDER}" stroke-opacity=".4" stroke-width="2"/>
"""
    return frame(title, desc, header + body, w, h, css=css)


def saturate(value, median):
    """Map a count onto 0..1 with diminishing returns; `median` scores 0.5."""
    return 1 - 0.5 ** (value / median)


def score_panel(user):
    cc = user["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    stats = [
        ("Commits", commits, 250, 3),
        ("Pull requests", cc["totalPullRequestContributions"], 40, 2),
        ("Issues", cc["totalIssueContributions"], 20, 1),
        ("Reviews", cc["totalPullRequestReviewContributions"], 10, 1),
        ("Stars earned", stars, 30, 2),
        ("Followers", user["followers"]["totalCount"], 15, 1),
    ]
    total_weight = sum(s[3] for s in stats)
    score = round(100 * sum(saturate(v, m) * w for _, v, m, w in stats) / total_weight)
    grades = [(90, "S"), (80, "A+"), (70, "A"), (60, "A-"), (50, "B+"), (40, "B"), (30, "B-"), (20, "C+")]
    grade = next((g for cut, g in grades if score >= cut), "C")

    cx, cy, r = 580, 192, 74
    circ = 2 * math.pi * r
    arc = max(circ * score / 100, 0.1)
    css = f".ring{{animation:fill 1.8s cubic-bezier(.2,.8,.2,1) both}}@keyframes fill{{from{{stroke-dashoffset:{arc:.1f}}}to{{stroke-dashoffset:0}}}}"
    rows = []
    for i, (label, value, *_rest) in enumerate(stats):
        y = 140 + i * 28
        rows.append(
            f'<text x="34" y="{y}" font-size="16" fill="{MUTED}">{label}</text>'
            f'<text x="330" y="{y}" font-size="17" font-weight="700" fill="{INK}" text-anchor="end">{value:,}</text>'
        )
    body = f"""    <g {FONT}>
      {''.join(rows)}
    </g>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GRID}" stroke-width="12"/>
    <circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#neon)" stroke-width="12" stroke-linecap="round"
      stroke-dasharray="{arc:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>
    <circle class="signal" cx="{cx}" cy="{cy}" r="{r + 16}" fill="none" stroke="{CYAN}" stroke-opacity=".25"/>
    <g {FONT} text-anchor="middle">
      <text x="{cx}" y="{cy + 14}" font-size="46" font-weight="700" fill="{INK}">{grade}</text>
      <text x="{cx}" y="{cy + 40}" font-size="14" letter-spacing="1.5" fill="{CYAN_SOFT}">{score} / 100</text>
    </g>
    <text x="34" y="{H - 14}" font-size="11" fill="{MUTED}" opacity=".6" {FONT}>Past 12 months · ENVY formula, not an official GitHub rank</text>"""
    desc = f"ENVY GitHub score {grade}, {score} out of 100, from commits, pull requests, issues, reviews, stars and followers."
    return card("GitHub Score", "SIGNAL STRENGTH", desc, body, css=css)


def stack_panel(user, tools):
    sizes = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] = sizes.get(edge["node"]["name"], 0) + edge["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    rest = total - sum(s for _, s in top)
    if rest > 0:
        top.append(("Other", rest))

    bar_x, bar_w, bar_y = 34, W - 68, 128
    segs, legend, x = [], [], bar_x
    for i, (name, size) in enumerate(top):
        w = bar_w * size / total
        color = LANG_COLORS[i % len(LANG_COLORS)]
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w, 2):.1f}" height="12" fill="{color}"/>')
        x += w
        lx, ly = 34 + (i % 3) * 220, 172 + (i // 3) * 26
        legend.append(
            f'<circle cx="{lx + 6}" cy="{ly - 5}" r="5" fill="{color}"/>'
            f'<text x="{lx + 20}" y="{ly}" font-size="15" fill="{INK}">{escape(name)}'
            f'<tspan dx="6" fill="{MUTED}">{100 * size / total:.1f}%</tspan></text>'
        )

    chips, cx, cy = [], 34, 238
    for tool in tools:
        cw = len(tool) * 8 + 26
        if cx + cw > W - 34:
            cx, cy = 34, cy + 36
        chips.append(
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="26" rx="13" fill="#0b1030" stroke="{LAVENDER}" stroke-opacity=".45"/>'
            f'<text x="{cx + cw / 2}" y="{cy + 18}" font-size="13" fill="{CYAN_SOFT}" text-anchor="middle">{escape(tool)}</text>'
        )
        cx += cw + 8

    body = f"""    <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="12" rx="6"/></clipPath>
    <g clip-path="url(#bar)">{''.join(segs)}</g>
    <g {FONT}>{''.join(legend)}{''.join(chips)}</g>"""
    names = ", ".join(n for n, _ in top)
    desc = f"Languages across my repositories ({names}) and the tools I build with: {', '.join(tools)}."
    return card("Tech Stack", "TOOLS OF THE TRADE", desc, body)


def activity_panel(user, days=30):
    cal = user["contributionsCollection"]["contributionCalendar"]
    all_days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    recent = all_days[-days:]
    counts = [d["contributionCount"] for d in recent]
    peak = max(counts) or 1

    streak = 0
    # Today may not have contributions yet; don't break the streak for it
    for i, d in enumerate(reversed(all_days)):
        if d["contributionCount"]:
            streak += 1
        elif i:
            break
    best = max(all_days, key=lambda d: d["contributionCount"])

    x0, x1, y0, y1 = 34, 470, 118, 270
    step = (x1 - x0) / (len(counts) - 1)
    pts = [(x0 + i * step, y1 - (y1 - y0) * c / peak) for i, c in enumerate(counts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{x0},{y1} L{line.replace(' ', ' L')} L{x1},{y1} Z"
    grid = "".join(
        f'<path d="M{x0} {y1 - (y1 - y0) * f:.1f}H{x1}" stroke="{GRID}" stroke-dasharray="3 5"/>' for f in (0, .5, 1)
    )
    lx, ly = pts[-1]
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) + 1
    css = f".draw{{animation:draw 2.4s ease-out both}}@keyframes draw{{from{{stroke-dashoffset:{length:.0f}}}to{{stroke-dashoffset:0}}}}"
    first = dt.date.fromisoformat(recent[0]["date"]).strftime("%b %-d")
    last = dt.date.fromisoformat(recent[-1]["date"]).strftime("%b %-d")
    best_day = dt.date.fromisoformat(best["date"]).strftime("%b %-d")

    stats = [
        (f"{cal['totalContributions']:,}", "contributions this year", PINK),
        (f"{sum(counts):,}", f"in the last {days} days", CYAN_SOFT),
        (f"{streak}", "day streak", LAVENDER),
        (f"{best['contributionCount']}", f"best day · {best_day}", INK),
    ]
    stat_svg = "".join(
        f'<text x="512" y="{132 + i * 44}" font-size="24" font-weight="700" fill="{color}">{value}</text>'
        f'<text x="512" y="{150 + i * 44}" font-size="12" fill="{MUTED}">{label}</text>'
        for i, (value, label, color) in enumerate(stats)
    )
    body = f"""    <defs><linearGradient id="fill" x2="0" y2="1"><stop stop-color="{PINK}" stop-opacity=".35"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient></defs>
    {grid}
    <path d="{area}" fill="url(#fill)"/>
    <polyline class="draw" points="{line}" fill="none" stroke="url(#neon)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{length:.0f}"/>
    <circle class="signal" cx="{lx:.1f}" cy="{ly:.1f}" r="9" fill="{CYAN}" fill-opacity=".3"/>
    <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="#9bf7ff"/>
    <g {FONT}>
      <text x="{x0}" y="{y1 + 22}" font-size="12" fill="{MUTED}">{first}</text>
      <text x="{x1}" y="{y1 + 22}" font-size="12" fill="{MUTED}" text-anchor="end">{last}</text>
      <text x="{x0 - 4}" y="{y0 - 6}" font-size="11" fill="{MUTED}" opacity=".7">{peak}/day</text>
      {stat_svg}
    </g>"""
    desc = f"{sum(counts)} contributions in the last {days} days, {cal['totalContributions']} this year, {streak} day streak."
    return card("Contribution Activity", "FREQUENCY", desc, body, css=css)


def building_panel(user, projects):
    pushed = {r["name"]: r["pushedAt"] for r in user["repositories"]["nodes"]}
    rows = []
    for i, p in enumerate(projects[:3]):
        y = 132 + i * 60
        when = pushed.get(p["repo"])
        when = dt.datetime.fromisoformat(when.replace("Z", "+00:00")).strftime("%b %-d") if when else ""
        active = p["status"].upper() == "ACTIVE"
        color = CYAN if active else PINK
        pill_w = len(p["status"]) * 7.5 + 22
        rows.append(f"""    <circle {'class="signal" ' if active else ''}cx="40" cy="{y + 8}" r="5" fill="{color}"/>
    <g {FONT}>
      <text x="58" y="{y + 14}" font-size="19" font-weight="700" fill="{INK}">{escape(p['name'])}</text>
      <text x="58" y="{y + 38}" font-size="14" fill="{MUTED}">{escape(p['note'])}</text>
      <rect x="{W - 34 - pill_w:.0f}" y="{y - 4}" width="{pill_w:.0f}" height="24" rx="12" fill="none" stroke="{color}" stroke-opacity=".6"/>
      <text x="{W - 34 - pill_w / 2:.0f}" y="{y + 12}" font-size="11" letter-spacing="1.2" font-weight="600" fill="{color}" text-anchor="middle">{escape(p['status'].upper())}</text>
      <text x="{W - 34}" y="{y + 38}" font-size="12" fill="{MUTED}" opacity=".7" text-anchor="end">{'last push ' + when if when else ''}</text>
    </g>""")
    desc = "Currently building: " + "; ".join(f"{p['name']} ({p['status']})" for p in projects[:3]) + "."
    return card("Currently Building", "ON THE WORKBENCH", desc, "\n".join(rows))


# Line icons drawn on a 24×24 grid
ICONS = {
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "terminal": '<rect x="2.5" y="4" width="19" height="16" rx="3"/><path d="M7 9l3 3-3 3M12.5 15H17"/>',
    "recovery": '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4.5h4.5"/><path d="M12 8v4l3 2"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "video": '<rect x="2.5" y="6" width="13" height="12" rx="2"/><path d="M15.5 10l6-3.5v11l-6-3.5"/>',
    "repo": '<path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v15H7.5A2.5 2.5 0 0 0 5 19.5zM5 19.5A2.5 2.5 0 0 0 7.5 22H19v-5"/>',
    "star": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z"/>',
    "people": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
    "follow": '<circle cx="10" cy="8" r="3.5"/><path d="M3.5 20a6.5 6.5 0 0 1 13 0"/><path d="M19 8v6M16 11h6"/>',
    "hash": '<path d="M10 3 8 21M16 3l-2 18M4 8.5h17M3 15.5h17"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r=".9" fill="currentColor"/>',
    "tiktok": '<path d="M14 3v12a4 4 0 1 1-4-4"/><path d="M14 3c.6 3 2.6 5 6 5.3"/>',
    "x": '<path d="M4 4l16 16M20 4L4 20"/>',
    "twitch": '<path d="M4 3h16v11l-4 4h-4l-3 3v-3H4z"/><path d="M10.5 7.5v4.5M15 7.5v4.5"/>',
    "pulse": '<path d="M2 12h4l3-7 4 14 3-7h6"/>',
    "radar": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6.4-6.4"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>',
    "tunnel": '<path d="M3 20v-8a9 9 0 0 1 18 0v8"/><path d="M7.5 20v-7a4.5 4.5 0 0 1 9 0v7"/><path d="M2 20h20"/><circle cx="12" cy="16.5" r="1.2" fill="currentColor"/>',
    "link": '<path d="M10 14a4.2 4.2 0 0 0 6 0l3-3a4.2 4.2 0 0 0-6-6l-1 1"/><path d="M14 10a4.2 4.2 0 0 0-6 0l-3 3a4.2 4.2 0 0 0 6 6l1-1"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "cipher": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7.5 8.5h3M7.5 12h9M13.5 15.5h3M7.5 15.5h3M13.5 8.5h3"/>',
    "book": '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5zM4 19.5A1.5 1.5 0 0 0 5.5 21H20"/><path d="M9 8h7M9 11.5h5"/>',
    "grid": '<rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><path d="M14 17.5l2.2 2.2 4.3-4.4"/>',
    "fingerprint": '<path d="M6.5 18.5A9 9 0 0 1 5 12a7 7 0 0 1 14 0v1"/><path d="M9 20a12 12 0 0 1-1-5v-3a4 4 0 0 1 8 0v2.5"/><path d="M12 12v3.5a8 8 0 0 0 1.5 4.5"/><path d="M19 16.5a14 14 0 0 1-.5 3"/>',
    "orbit": '<circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-25 12 12)"/><circle cx="20" cy="8.2" r="1.3" fill="currentColor"/>',
    "scope": '<circle cx="12" cy="12" r="8.5"/><path d="M12 1.5v5M12 17.5v5M1.5 12h5M17.5 12h5"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/>',
    "crystal": '<circle cx="12" cy="10" r="7"/><path d="M6.5 21h11M8 17.5l-1.5 3.5M16 17.5l1.5 3.5"/><path d="M9 8.5a3.5 3.5 0 0 1 3-2.5"/>',
    "branch": '<circle cx="6" cy="5" r="2.2"/><circle cx="6" cy="19" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 7.2v9.6M18 10.2c0 4-6 3.5-11 6.6"/>',
    "box": '<path d="M12 2.5l8.5 4.7v9.6L12 21.5l-8.5-4.7V7.2z"/><path d="M3.5 7.2 12 12l8.5-4.8M12 12v9.5"/><path d="M8 4.8l8.5 4.8"/>',
}

ACCENTS = {"pink": PINK, "cyan": CYAN, "lavender": LAVENDER, "violet": "#b07cff"}


def _tw(text, size, bold=False):
    """Rough rendered width of Arial text, for layout."""
    return len(text) * size * (0.6 if bold else 0.54)


def constellation(groups):
    """The opening animation: every app as a glowing node orbiting the ENVY core,
    with light flowing out along each link and a comet circling the ring."""
    w, h, cx, cy, rx, ry = 1000, 470, 500, 244, 318, 168
    apps = [(g, a) for g in groups for a in g["apps"]]
    n = len(apps)
    ring = f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0"
    parts = [
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{LAVENDER}" stroke-opacity=".22" stroke-width="1.2"/>',
        f'<ellipse class="spin" cx="{cx}" cy="{cy}" rx="{rx + 26}" ry="{ry + 22}" fill="none" stroke="{CYAN}" stroke-opacity=".18" stroke-dasharray="2 14"/>',
        f'<ellipse class="spin2" cx="{cx}" cy="{cy}" rx="{rx - 70}" ry="{ry - 52}" fill="none" stroke="{PINK}" stroke-opacity=".16" stroke-dasharray="3 18"/>',
    ]
    nodes, labels = [], []
    for i, (g, a) in enumerate(apps):
        ang = math.radians(-90 + (i + .5) * 360 / n)
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        col = ACCENTS.get(g.get("accent"), PINK)
        d = (i * .37) % 4
        parts.append(f'<path class="flow" style="animation-delay:-{d:.2f}s" d="M{cx} {cy}L{x:.1f} {y:.1f}" stroke="{col}" stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="3 11"/>')
        nodes.append(
            f'<g><circle class="halo" style="animation-delay:-{(i * .61) % 5:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{col}" opacity=".18"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{BG}" stroke="{col}" stroke-width="1.6"/>'
            f'{icon(a["icon"], x - 8, y - 8, 16, col, 2)}</g>')
        right = math.cos(ang) > 0.08
        left = math.cos(ang) < -0.08
        anchor = "start" if right else "end" if left else "middle"
        lx = x + (22 if right else -22 if left else 0)
        ly = y + 5 + (0 if (right or left) else (-24 if math.sin(ang) < 0 else 30))
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="14.5" font-weight="700" fill="{INK}" text-anchor="{anchor}">{escape(a["short"])}</text>')
    stars = "".join(
        f'<circle class="tw" style="animation-delay:-{(k * 1.3) % 6:.1f}s" cx="{(k * 137.5) % w:.0f}" cy="{(k * 89.3) % h:.0f}" r="{.7 + (k % 3) * .35:.2f}" fill="#cfe0ff"/>'
        for k in range(46))
    core = f"""<circle class="breathe" cx="{cx}" cy="{cy}" r="74" fill="url(#corefog)"/>
    <circle cx="{cx}" cy="{cy}" r="48" fill="{BG}" stroke="url(#neon)" stroke-width="2"/>
    <circle class="spin3" cx="{cx}" cy="{cy}" r="56" fill="none" stroke="url(#neon)" stroke-opacity=".7" stroke-width="1.5" stroke-dasharray="40 22 8 22"/>
    <text x="{cx}" y="{cy + 9}" font-size="26" font-weight="800" letter-spacing="3" fill="url(#neon)" text-anchor="middle" {FONT}>ENVY</text>"""
    comet = (f'<g><circle r="9" fill="{CYAN}" opacity=".25"/><circle r="3.2" fill="#fff"/>'
             f'<animateMotion dur="14s" repeatCount="indefinite" path="{ring}"/></g>'
             f'<g><circle r="7" fill="{PINK}" opacity=".25"/><circle r="2.6" fill="#fff"/>'
             f'<animateMotion dur="14s" begin="-7s" repeatCount="indefinite" path="{ring}"/></g>')
    legend, lx0 = [], 34
    for g in groups:
        col = ACCENTS.get(g.get("accent"), PINK)
        legend.append(f'<circle cx="{lx0}" cy="{h - 28}" r="5" fill="{col}"/>'
                      f'<text x="{lx0 + 12}" y="{h - 23}" font-size="12.5" letter-spacing="1.8" font-weight="600" fill="{MUTED}">{escape(g["kicker"])}</text>')
        lx0 += 30 + _tw(g["kicker"], 12.5, True) + len(g["kicker"]) * 1.8
    head = (f'<text x="34" y="44" font-size="14" letter-spacing="2.6" font-weight="600" fill="{CYAN_SOFT}">THE ENVY SUITE</text>'
            f'<text x="34" y="70" font-size="13.5" fill="{MUTED}">{n} apps · one installer · macOS · Windows · Linux</text>'
            f'<text x="{w - 34}" y="{h - 23}" font-size="12.5" fill="{MUTED}" text-anchor="end">signed releases · no telemetry</text>')
    body = f"""    <defs><radialGradient id="corefog"><stop stop-color="{PINK}" stop-opacity=".45"/><stop offset=".55" stop-color="{VIOLET}" stop-opacity=".18"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient></defs>
    <g>{stars}</g>
    <g fill="none">{''.join(parts)}</g>
    {comet}
    {core}
    <g>{''.join(nodes)}</g>
    <g {FONT}>{''.join(labels)}{''.join(legend)}{head}</g>"""
    css = (f".flow{{animation:flow 4s linear infinite}}@keyframes flow{{to{{stroke-dashoffset:-56}}}}"
           f".halo{{animation:halo 5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}@keyframes halo{{0%,100%{{opacity:.08;transform:scale(.8)}}50%{{opacity:.42;transform:scale(1.35)}}}}"
           f".spin{{animation:dash 30s linear infinite}}.spin2{{animation:dash 22s linear infinite reverse}}@keyframes dash{{to{{stroke-dashoffset:-400}}}}"
           f".spin3{{animation:rot 18s linear infinite;transform-origin:{cx}px {cy}px}}@keyframes rot{{to{{transform:rotate(360deg)}}}}"
           f".breathe{{animation:breathe 6s ease-in-out infinite;transform-origin:{cx}px {cy}px}}@keyframes breathe{{0%,100%{{opacity:.7;transform:scale(.92)}}50%{{opacity:1;transform:scale(1.12)}}}}"
           f".tw{{animation:tw 6s ease-in-out infinite}}@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.8}}}}")
    names = ", ".join(a["name"] for _g, a in apps)
    return frame("The ENVY suite", f"{n} apps orbiting the ENVY core: {names}.", body, w, h, rx=22, css=css)


def group_label(g, index=0):
    """A slim heading above each row of app tiles."""
    w, h = 1000, 54
    col = ACCENTS.get(g.get("accent"), PINK)
    tx = 66 + _tw(g["title"], 21, True) + 16
    run = w - 34 - _tw(g["blurb"], 13) - 18 - tx
    body = f"""    {icon(g["icon"], 26, 15, 24, col, 2)}
    <text x="62" y="35" font-size="21" font-weight="700" fill="{INK}" {FONT}>{escape(g["title"])}</text>
    <text x="{w - 34}" y="34" font-size="13" fill="{MUTED}" text-anchor="end" {FONT}>{escape(g["blurb"])}</text>
    <path d="M{tx:.0f} 28h{run:.0f}" stroke="{col}" stroke-opacity=".28" stroke-width="1.5"/>
    <g class="travel"><circle cx="{tx:.0f}" cy="28" r="4.5" fill="{col}" opacity=".35"/><circle cx="{tx:.0f}" cy="28" r="1.8" fill="#fff"/></g>"""
    css = (f".travel{{animation:travel 6s ease-in-out {index * 1.1:.1f}s infinite}}"
           f"@keyframes travel{{0%{{transform:translateX(0);opacity:0}}15%,85%{{opacity:1}}100%{{transform:translateX({run:.0f}px);opacity:0}}}}")
    return frame(g["title"], f"{g['title']}: {g['blurb']}", body, w, h, rx=14, css=css)


def app_tile(a, accent_name, index=0):
    """One app in the grid: a glowing icon, its name, one line, and a staggered sheen."""
    w, h = 250, 196
    col = ACCENTS.get(accent_name, PINK)
    lines = textwrap.wrap(a["tagline"], 27)[:3]
    tag = "".join(f'<text x="22" y="{118 + i * 20}" font-size="14.5" fill="{MUTED}">{escape(l)}</text>' for i, l in enumerate(lines))
    name_size = 20 if _tw(a["name"], 20, True) < w - 40 else 17
    body = f"""    <defs>
      <radialGradient id="ig"><stop stop-color="{col}" stop-opacity=".45"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>
      <linearGradient id="sheen"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    </defs>
    <circle class="glow" cx="46" cy="46" r="34" fill="url(#ig)"/>
    <circle cx="46" cy="46" r="24" fill="#0a0e22" stroke="{col}" stroke-opacity=".75" stroke-width="1.5"/>
    <circle class="ring" cx="46" cy="46" r="29" fill="none" stroke="{col}" stroke-opacity=".55" stroke-width="1.2" stroke-dasharray="10 8 2 8"/>
    {icon(a["icon"], 34, 34, 24, col, 1.9)}
    <text x="{w - 20}" y="34" font-size="11" letter-spacing="1.6" font-weight="600" fill="{col}" text-anchor="end" {FONT}>{escape(a.get("badge", ""))}</text>
    <g {FONT}><text x="22" y="96" font-size="{name_size}" font-weight="700" fill="{INK}">{escape(a["name"])}</text>{tag}</g>
    <path d="M22 {h - 18}h34" stroke="{col}" stroke-width="2"/>
    <g class="sheen"><rect x="-120" y="-30" width="90" height="{h + 60}" fill="url(#sheen)" transform="skewX(-18)"/></g>"""
    delay = (index * 0.75) % 12
    css = (f".sheen{{animation:sheen 12s ease-in-out {delay:.2f}s infinite}}"
           f"@keyframes sheen{{0%{{transform:translateX(0)}}18%,100%{{transform:translateX({w + 220}px)}}}}"
           f".ring{{animation:rot 16s linear infinite;transform-origin:46px 46px}}@keyframes rot{{to{{transform:rotate(360deg)}}}}"
           f".glow{{animation:glow 5s ease-in-out -{index * .45:.2f}s infinite}}@keyframes glow{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}")
    return frame(a["name"], f"{a['name']}: {a['tagline']}", body, w, h, rx=18, css=css)


def now_building(items):
    """'Working on': each project with its real milestone track, done steps lit,
    the current step pulsing and a progress bar that fills on a loop."""
    w = 1000
    row_h = 132
    h = 34 + row_h * len(items)
    rows = []
    for i, it in enumerate(items):
        y0 = 52 + i * row_h
        col = ACCENTS.get(it.get("accent"), PINK)
        steps = it["steps"]
        done = sum(1 for s in steps if s.get("done"))
        cur = next((k for k, s in enumerate(steps) if not s.get("done")), None)
        x0, x1 = 60, w - 60
        gap = (x1 - x0) / (len(steps) - 1)
        frac = (done - 1 + (0.5 if cur is not None else 0)) / (len(steps) - 1) if done else 0.15
        pill = it["status"]
        pw = _tw(pill, 11, True) + len(pill) * 1.2 + 24
        rows.append(f"""    <g {FONT}>
      <text x="34" y="{y0}" font-size="20" font-weight="700" fill="{INK}">{escape(it["name"])}</text>
      <text x="{36 + _tw(it["name"], 20, True) + 14:.0f}" y="{y0}" font-size="14" fill="{MUTED}">{escape(it["goal"])}</text>
      <rect x="{w - 34 - pw:.0f}" y="{y0 - 17}" width="{pw:.0f}" height="24" rx="12" fill="none" stroke="{col}" stroke-opacity=".65"/>
      <text x="{w - 34 - pw / 2:.0f}" y="{y0 - 1}" font-size="11" letter-spacing="1.2" font-weight="600" fill="{col}" text-anchor="middle">{escape(pill)}</text>
      <text x="{w - 34}" y="{y0 + 92}" font-size="12.5" fill="{MUTED}" text-anchor="end">{done} of {len(steps)} done</text>
    </g>
    <path d="M{x0} {y0 + 38}H{x1}" stroke="{GRID}" stroke-width="4" stroke-linecap="round"/>
    <path class="fill{i}" d="M{x0} {y0 + 38}H{x0 + (x1 - x0) * frac:.0f}" stroke="{col}" stroke-width="4" stroke-linecap="round"/>""")
        for k, s in enumerate(steps):
            x = x0 + k * gap
            if s.get("done"):
                dot = f'<circle cx="{x:.0f}" cy="{y0 + 38}" r="8" fill="{col}"/><path d="M{x - 3.5:.1f} {y0 + 38}l2.4 2.6 4.6-5" fill="none" stroke="{BG}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            elif k == cur:
                dot = (f'<circle class="now" cx="{x:.0f}" cy="{y0 + 38}" r="15" fill="{col}" opacity=".25"/>'
                       f'<circle cx="{x:.0f}" cy="{y0 + 38}" r="8" fill="{BG}" stroke="{col}" stroke-width="2.5"/>')
            else:
                dot = f'<circle cx="{x:.0f}" cy="{y0 + 38}" r="7" fill="{BG}" stroke="{MUTED}" stroke-opacity=".45" stroke-width="1.5"/>'
            fill = INK if s.get("done") or k == cur else MUTED
            op = "1" if s.get("done") or k == cur else ".6"
            lab = "".join(f'<tspan x="{x:.0f}" dy="{0 if j == 0 else 15}">{escape(t)}</tspan>' for j, t in enumerate(textwrap.wrap(s["label"], 15)[:2]))
            rows.append(f'    {dot}<text y="{y0 + 68}" font-size="12.5" fill="{fill}" opacity="{op}" text-anchor="middle" {FONT}>{lab}</text>')
    css = "".join(
        f".fill{i}{{stroke-dasharray:1000;animation:fill 7s ease-out {i * .8:.1f}s infinite}}" for i in range(len(items)))
    css += ("@keyframes fill{0%{stroke-dashoffset:1000}45%,100%{stroke-dashoffset:0}}"
            ".now{animation:now 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
            "@keyframes now{0%,100%{opacity:.1;transform:scale(.7)}50%{opacity:.45;transform:scale(1.25)}}")
    desc = "Working on: " + "; ".join(
        f"{it['name']} — {it['goal']} ({sum(1 for s in it['steps'] if s.get('done'))} of {len(it['steps'])} steps done)" for it in items) + "."
    return frame("Working On", desc, "\n".join(rows), w, h, css=css)


def icon(name, x, y, size=24, color=CYAN, width=1.8):
    return (
        f'<g transform="translate({x} {y}) scale({size / 24:.3f})" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
        f'{ICONS[name].replace("currentColor", color)}</g>'
    )


def stats_strip(user):
    w, h = 1000, 104
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    cells = [
        ("repo", user["repositories"]["totalCount"], "PUBLIC REPOS", PINK),
        ("star", stars, "STARS EARNED", LAVENDER),
        ("people", user["followers"]["totalCount"], "FOLLOWERS", CYAN),
        ("follow", user["following"]["totalCount"], "FOLLOWING", PINK),
    ]
    parts = []
    for i, (ic, value, label, color) in enumerate(cells):
        x = i * 250
        if i:
            parts.append(f'<path d="M{x} 26V78" stroke="{GRID}" stroke-width="1.5"/>')
        parts.append(f'<g class="signal" style="animation-delay:{i * 1.7:.1f}s">{icon(ic, x + 40, 37, 30, color)}</g>')
        parts.append(
            f'<text x="{x + 88}" y="55" font-size="30" font-weight="700" fill="{INK}" {FONT}>{value:,}</text>'
            f'<text x="{x + 89}" y="78" font-size="12.5" letter-spacing="1.6" fill="{MUTED}" {FONT}>{label}</text>'
        )
    desc = ", ".join(f"{v} {l.lower()}" for _, v, l, _c in cells) + "."
    return frame("GitHub at a glance", desc, "    " + "".join(parts), w, h, rx=16)


def project_card(p, repo, index=0):
    w, h = 340, 250
    accent = {"pink": PINK, "cyan": CYAN, "lavender": LAVENDER}.get(p.get("accent"), PINK)
    stars = repo["stargazerCount"] if repo else 0
    lang = (repo or {}).get("primaryLanguage") or {}
    if p.get("kicker"):
        meta = (f'<text x="{w - 24}" y="46" font-size="11.5" letter-spacing="1.8" font-weight="600" fill="{accent}" text-anchor="end">'
                f'{escape(p["kicker"])}</text>')
    elif stars:
        meta = f'<text x="{w - 24}" y="47" font-size="15" fill="{INK}" text-anchor="end">★ {stars:,}</text>'
    elif lang:
        meta = (f'<circle cx="{w - 30 - len(lang["name"]) * 7.3:.0f}" cy="42" r="4.5" fill="{accent}"/>'
                f'<text x="{w - 24}" y="47" font-size="13" fill="{MUTED}" text-anchor="end">{escape(lang["name"])}</text>')
    else:
        meta = ""
    lines = textwrap.wrap(p["blurb"], 38)[:3]
    blurb = "".join(
        f'<text x="26" y="{98 + i * 23}" font-size="15" fill="{MUTED}">{escape(line)}</text>' for i, line in enumerate(lines)
    )
    chips, cx = [], 26
    for tag in p.get("tags", [])[:4]:
        cw = len(tag) * 7.4 + 24
        if cx + cw > w - 20:
            break
        chips.append(
            f'<rect x="{cx:.0f}" y="196" width="{cw:.0f}" height="28" rx="14" fill="#0b1030" stroke="{accent}" stroke-opacity=".6"/>'
            f'<text x="{cx + cw / 2:.0f}" y="215" font-size="13" fill="{INK}" text-anchor="middle">{escape(tag)}</text>'
        )
        cx += cw + 8
    body = f"""    {icon(p.get("icon", "terminal"), 24, 26, 30, accent)}
    <g {FONT}>
      <text x="66" y="50" font-size="21" font-weight="700" fill="{INK}">{escape(p["name"])}</text>
      {meta}{blurb}{''.join(chips)}
    </g>
    <path d="M26 72h44" stroke="{accent}" stroke-width="2"/>
    <defs><linearGradient id="sheen"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    <g class="sheen"><rect x="-140" y="-40" width="110" height="{h + 80}" fill="url(#sheen)" transform="skewX(-18)"/></g>"""
    css = (f".sheen{{animation:sheen 9s ease-in-out {index * 1.4:.1f}s infinite}}"
           f"@keyframes sheen{{0%{{transform:translateX(0)}}22%,100%{{transform:translateX({w + 260}px)}}}}")
    return frame(p["name"], p["blurb"], body, w, h, rx=18, css=css)


def heatmap_panel(user):
    w, h = 1000, 300
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    peak = max((d["contributionCount"] for d in days), default=0) or 1
    levels = ["#10153a", VIOLET, LAVENDER, PINK, CYAN]

    x0, y0, step, size = 66, 150, 14, 11
    cells, months, last_month = [], [], None
    for wi, wk in enumerate(cal["weeks"]):
        for d in wk["contributionDays"]:
            date = dt.date.fromisoformat(d["date"])
            c = d["contributionCount"]
            lvl = 0 if not c else min(4, 1 + int(3.999 * c / peak))
            row = (date.weekday() + 1) % 7  # Sunday first, like GitHub
            delay = f' class="lit" style="animation-delay:{(wi * 7 + row) % 23 * .17:.2f}s"' if lvl else ""
            cells.append(f'<rect x="{x0 + wi * step}" y="{y0 + row * step}" width="{size}" height="{size}" rx="2.5" fill="{levels[lvl]}"{delay}/>')
            if date.day <= 7 and row == 0 and date.month != last_month:
                months.append(f'<text x="{x0 + wi * step}" y="{y0 - 10}" font-size="12" fill="{MUTED}">{date.strftime("%b")}</text>')
                last_month = date.month
    weekdays = "".join(
        f'<text x="34" y="{y0 + r * step + 10}" font-size="11" fill="{MUTED}" opacity=".7">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    active = sum(1 for d in days if d["contributionCount"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    stats = [
        (f"{cal['totalContributions']:,}", "contributions this year", PINK),
        (f"{active}", "active days", CYAN_SOFT),
        (f"{longest}", "longest streak (days)", LAVENDER),
    ]
    stat_svg = "".join(
        f'<text x="846" y="{150 + i * 46}" font-size="26" font-weight="700" fill="{color}">{v}</text>'
        f'<text x="846" y="{168 + i * 46}" font-size="12" fill="{MUTED}">{label}</text>'
        for i, (v, label, color) in enumerate(stats)
    )
    legend = "".join(f'<rect x="{x0 + 620 + i * 16}" y="{y0 + 7 * step + 12}" width="11" height="11" rx="2.5" fill="{c}"/>' for i, c in enumerate(levels))
    body = f"""    <g {FONT}>
      {''.join(months)}{weekdays}
      <text x="{x0 + 584}" y="{y0 + 7 * step + 21}" font-size="11" fill="{MUTED}">Less</text>
      <text x="{x0 + 704}" y="{y0 + 7 * step + 21}" font-size="11" fill="{MUTED}">More</text>
      {stat_svg}
    </g>
    {''.join(cells)}{legend}
    <defs>
      <linearGradient id="scan"><stop stop-color="{CYAN}" stop-opacity="0"/><stop offset=".85" stop-color="{CYAN}" stop-opacity=".22"/><stop offset="1" stop-color="#9bf7ff" stop-opacity=".6"/></linearGradient>
      <clipPath id="grid"><rect x="{x0 - 2}" y="{y0 - 2}" width="{len(cal['weeks']) * step + 2}" height="{7 * step + 2}"/></clipPath>
    </defs>
    <g clip-path="url(#grid)"><g class="scan"><rect x="{x0 - 90}" y="{y0 - 2}" width="90" height="{7 * step + 2}" fill="url(#scan)"/></g></g>
    <path d="M826 128V262" stroke="{GRID}" stroke-width="1.5"/>"""
    css = (".lit{animation:twinkle 3.4s ease-in-out infinite}@keyframes twinkle{0%,100%{opacity:1}50%{opacity:.55}}"
           f".scan{{animation:scan 8s linear infinite}}@keyframes scan{{0%{{transform:translateX(0)}}65%,100%{{transform:translateX({len(cal['weeks']) * step + 90}px)}}}}")
    desc = f"{cal['totalContributions']} contributions in the past year across {active} active days; longest streak {longest} days."
    return card("Contribution Activity", "THE PAST YEAR", desc, body, w, h, css=css)


def fetch_events(login, token):
    req = urllib.request.Request(
        f"https://api.github.com/users/{login}/events/public?per_page=50",
        headers={"Authorization": f"bearer {token}", "User-Agent": "envy-panels"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def recent_panel(events, login):
    def short(repo):
        return repo.split("/", 1)[1] if repo.startswith(login + "/") else repo

    items = []
    for e in sorted(events, key=lambda e: e["created_at"], reverse=True):
        repo, p = short(e["repo"]["name"]), e["payload"]
        day = e["created_at"][:10]
        if e["type"] == "PushEvent":
            # Several pushes to one repo on one day read as a single line
            if any(it[0] == ("push", repo, day) for it in items):
                continue
            items.append([("push", repo, day), f"Pushed to {repo}", "repo", day])
        elif e["type"] == "PullRequestEvent" and p.get("action") in ("opened", "closed"):
            merged = p.get("action") == "closed" and p.get("pull_request", {}).get("merged")
            if p.get("action") == "closed" and not merged:
                continue
            items.append([("pr", repo, day), f"{'Merged' if merged else 'Opened'} a pull request in {repo}", "layers", day])
        elif e["type"] == "CreateEvent" and p.get("ref_type") == "repository":
            items.append([("create", repo, day), f"Created {repo}", "star", day])
        elif e["type"] == "ReleaseEvent":
            items.append([("release", repo, day), f"Released {p['release']['tag_name']} of {repo}", "star", day])
        elif e["type"] == "IssuesEvent" and p.get("action") == "opened":
            items.append([("issue", repo, day), f"Opened an issue in {repo}", "search", day])
        elif e["type"] == "WatchEvent":
            items.append([("star", repo, day), f"Starred {repo}", "star", day])
        if len(items) >= 5:
            break

    rows = []
    shown = items[:4]
    for i, (key, text, ic, day) in enumerate(shown):
        if len(text) > 46:
            text = text[:45] + "…"
        y = 138 + i * 44
        color = [PINK, CYAN, LAVENDER, PINK][i]
        rows.append(
            f'<circle cx="44" cy="{y - 5}" r="6" fill="{BG}" stroke="{color}" stroke-width="2"/>'
            f'<text x="66" y="{y}" font-size="16" fill="{INK}">{escape(text)}</text>'
            f'<text x="{W - 34}" y="{y}" font-size="13" fill="{MUTED}" text-anchor="end">{dt.date.fromisoformat(day).strftime("%b %-d")}</text>'
        )
    line = f'<path d="M44 {139}V{133 + (len(shown) - 1) * 44}" stroke="{GRID}" stroke-width="2"/>' if len(shown) > 1 else ""
    body = f"""    {line}
    <g {FONT}>{''.join(rows) or f'<text x="34" y="150" font-size="16" fill="{MUTED}">Quiet on the public channels lately.</text>'}</g>"""
    desc = "Recent public activity: " + "; ".join(
        (f"pushed to {k[1]}" if k[0] == "push" else t) for k, t, _i, _d in shown
    ) + "."
    return card("Recent Activity", "LATEST TRANSMISSIONS", desc, body)


def topics_strip(topics):
    w, gap, ch = 1000, 12, 40
    widths = [len(t["label"]) * 8.4 + 58 for t in topics]
    # Use as few rows as fit, with chips spread evenly across them
    n_rows = 1
    while max(sum(widths[i:i + math.ceil(len(topics) / n_rows)]) + gap * (math.ceil(len(topics) / n_rows) - 1)
              for i in range(0, len(topics), math.ceil(len(topics) / n_rows))) > w - 8:
        n_rows += 1
    per = math.ceil(len(topics) / n_rows)
    rows = []
    for i in range(0, len(topics), per):
        row = list(zip(topics[i:i + per], widths[i:i + per]))
        rows.append((row, sum(cw for _, cw in row) + gap * (len(row) - 1)))
    h = len(rows) * (ch + 12) + 4
    parts = []
    for ri, (items, total) in enumerate(rows):
        x, y = (w - total) / 2, 2 + ri * (ch + 12)
        for t, cw in items:
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="12" fill="{BG}" stroke="url(#chip)" stroke-width="1.5"/>'
                + icon(t["icon"], x + 16, y + 11, 18, PINK if ri % 2 == 0 else CYAN)
                + f'<text x="{x + 44:.1f}" y="{y + 25.5}" font-size="15" fill="{INK}" {FONT}>{escape(t["label"])}</text>'
            )
            x += cw + gap
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">
  <title id="title">{escape(" · ".join(t["label"] for t in topics))}</title>
  <defs><linearGradient id="chip"><stop class="c1" stop-color="{PINK}"/><stop class="c2" offset="1" stop-color="{CYAN}"/></linearGradient></defs>
  <style>.c1{{animation:c1 9s linear infinite}}.c2{{animation:c2 9s linear infinite}}@keyframes c1{{0%,100%{{stop-color:{PINK}}}33%{{stop-color:{LAVENDER}}}66%{{stop-color:{CYAN}}}}}@keyframes c2{{0%,100%{{stop-color:{CYAN}}}33%{{stop-color:{PINK}}}66%{{stop-color:{LAVENDER}}}}}{REDUCED}</style>
  {''.join(parts)}
</svg>
"""


def moon_divider():
    w, h, cy = 1000, 44, 22
    moons = []
    # Crescents lit from the left, then a glowing full moon, then lit from the right
    for i, dx in enumerate((5, 3.5, 2, None, -2, -3.5, -5)):
        x = 500 + (i - 3) * 38
        if dx is None:
            moons.append(
                f'<circle class="signal" cx="{x}" cy="{cy}" r="17" fill="{LAVENDER}" fill-opacity=".18"/>'
                f'<circle cx="{x}" cy="{cy}" r="11" fill="url(#moon)" stroke="{PINK}" stroke-width="1.5"/>'
                f'<circle cx="{x - 3}" cy="{cy - 2}" r="2.2" fill="#8a6ad6" opacity=".6"/><circle cx="{x + 3.5}" cy="{cy + 3}" r="1.5" fill="#8a6ad6" opacity=".5"/>'
            )
        else:
            color = LAVENDER if abs(dx) < 3 else (PINK if i < 3 else CYAN)
            moons.append(
                f'<mask id="m{i}"><circle cx="{x}" cy="{cy}" r="8" fill="#fff"/><circle cx="{x + dx}" cy="{cy - 1}" r="7.5" fill="#000"/></mask>'
                f'<circle cx="{x}" cy="{cy}" r="8" fill="{color}" mask="url(#m{i})"/>'
            )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Moon phase divider">
  <defs>
    <linearGradient id="fadeL"><stop stop-color="{PINK}" stop-opacity="0"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
    <linearGradient id="fadeR"><stop stop-color="{CYAN}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
    <radialGradient id="moon" cx=".4" cy=".35"><stop stop-color="#f2e9ff"/><stop offset="1" stop-color="{LAVENDER}"/></radialGradient>
  </defs>
  <style>.signal{{animation:pulse 7s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
.cl{{animation:cl 6s ease-in infinite}}.cr{{animation:cr 6s ease-out 3s infinite}}
@keyframes cl{{0%{{transform:translateX(0);opacity:0}}10%{{opacity:1}}55%,100%{{transform:translateX(290px);opacity:0}}}}
@keyframes cr{{0%{{transform:translateX(0);opacity:0}}10%{{opacity:1}}55%,100%{{transform:translateX(290px);opacity:0}}}}
.tw{{animation:pulse 4s ease-in-out infinite}}{REDUCED}</style>
  <path d="M70 {cy}H360" stroke="url(#fadeL)" stroke-width="2"/>
  <path d="M640 {cy}H930" stroke="url(#fadeR)" stroke-width="2"/>
  <g class="cl"><circle cx="70" cy="{cy}" r="6" fill="{PINK}" opacity=".25"/><circle cx="70" cy="{cy}" r="2.5" fill="#ffd1ee"/></g>
  <g class="cr"><circle cx="640" cy="{cy}" r="6" fill="{CYAN}" opacity=".25"/><circle cx="640" cy="{cy}" r="2.5" fill="#d4fbff"/></g>
  <g fill="#c9d9ff">{''.join(f'<circle class="tw" style="animation-delay:{d}s" cx="{x}" cy="{y}" r="{r}"/>' for x, y, r, d in ((180, 9, 1, 0), (285, 35, .8, 1.3), (330, 8, 1.1, 2.4), (690, 34, 1, .7), (770, 10, .8, 1.9), (860, 31, 1.1, 3)))}</g>
  {''.join(moons)}
</svg>
"""


def typing_banner(phrases, prompt="envy@veil:~$ "):
    """A terminal line that types each phrase, holds it, then erases it."""
    w, h, size = 1000, 64, 20
    cw = size * 0.6  # monospace advance
    n = len(phrases)
    x_prompt = (w - (len(prompt) + max(len(p) for p in phrases)) * cw) / 2
    x_text = x_prompt + len(prompt) * cw

    # Shared discrete timeline: (time 0..1, phrase index, visible chars)
    keys = []
    for i, phrase in enumerate(phrases):
        start, span, L = i / n, 1 / n, len(phrase)
        keys += [(start + 0.45 * span * k / L, i, k) for k in range(L + 1)]
        keys += [(start + 0.8 * span + 0.12 * span * (L - k) / L, i, k) for k in range(L, -1, -1)]
    keys.append((1, None, 0))
    times = ";".join(f"{t:.5f}" for t, _, _ in keys)
    dur = f"{n * 5}s"

    clips, texts = [], []
    for i, phrase in enumerate(phrases):
        widths = ";".join(f"{k * cw:.1f}" if j == i else "0" for _, j, k in keys)
        clips.append(
            f'<clipPath id="t{i}"><rect x="{x_text:.1f}" y="10" height="44" width="0">'
            f'<animate attributeName="width" values="{widths}" keyTimes="{times}" dur="{dur}" calcMode="discrete" repeatCount="indefinite"/></rect></clipPath>'
        )
        texts.append(f'<text x="{x_text:.1f}" y="39" clip-path="url(#t{i})">{escape(phrase)}</text>')
    cursor_x = ";".join(f"{x_text + k * cw:.1f}" for _, _, k in keys)
    body = f"""    <defs>{''.join(clips)}</defs>
    <g {MONO} font-size="{size}">
      <text x="{x_prompt:.1f}" y="39" fill="{PINK}">{escape(prompt)}</text>
      <g class="typed" fill="{INK}">{''.join(texts)}</g>
      <text class="static" x="{x_text:.1f}" y="39" fill="{INK}">{escape(phrases[0])}</text>
    </g>
    <rect class="cur" x="{x_text:.1f}" y="22" width="{cw - 1:.1f}" height="23" fill="{CYAN}" opacity=".85">
      <animate attributeName="x" values="{cursor_x}" keyTimes="{times}" dur="{dur}" calcMode="discrete" repeatCount="indefinite"/>
    </rect>"""
    css = (".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}.static{display:none}"
           "@media(prefers-reduced-motion:reduce){.typed{display:none}.static{display:inline}}")
    return frame(" · ".join(phrases), "Typing: " + " / ".join(phrases), body, w, h, rx=14, css=css)


def section_banner(sec):
    """A neon section heading with a flickering glow and a travelling light."""
    w, h = 1000, 76
    accent = {"pink": PINK, "cyan": CYAN, "lavender": LAVENDER}.get(sec.get("accent"), PINK)
    title, tw = sec["title"], len(sec["title"]) * 15.5
    line_x = 74 + tw + 24
    body = f"""    <defs><filter id="glow" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="5"/></filter></defs>
    <g class="flicker" filter="url(#glow)">{icon(sec["icon"], 28, 23, 30, accent, 2.6)}
      <text x="74" y="48" font-size="27" font-weight="700" fill="{accent}" {FONT}>{escape(title)}</text></g>
    {icon(sec["icon"], 28, 23, 30, accent)}
    <text x="74" y="48" font-size="27" font-weight="700" letter-spacing=".4" fill="{INK}" {FONT}>{escape(title)}</text>
    <text x="{w - 30}" y="47" font-size="12.5" letter-spacing="2.4" font-weight="600" fill="{accent}" text-anchor="end" {FONT}>{escape(sec.get("kicker", ""))}</text>
    <path d="M{line_x:.0f} 39H{w - 40 - len(sec.get('kicker', '')) * 9.6:.0f}" stroke="{accent}" stroke-opacity=".25" stroke-width="1.5"/>
    <g class="travel"><circle cx="{line_x:.0f}" cy="39" r="5" fill="{accent}" opacity=".3"/><circle cx="{line_x:.0f}" cy="39" r="2" fill="#fff"/></g>"""
    run = w - 40 - len(sec.get("kicker", "")) * 9.6 - line_x
    css = (".flicker{animation:flicker 6s linear infinite}"
           "@keyframes flicker{0%,18%,22%,62%,64%,100%{opacity:.85}20%,63%{opacity:.25}40%{opacity:1}}"
           f".travel{{animation:travel 5s ease-in-out infinite}}@keyframes travel{{0%{{transform:translateX(0);opacity:0}}15%{{opacity:1}}85%{{opacity:1}}100%{{transform:translateX({run:.0f}px);opacity:0}}}}")
    return frame(title, f"{title} — {sec.get('kicker', '')}", body, w, h, rx=16, css=css)


def skyline_strip(skyline_svg, crop=(800, 628, 480, 200)):
    """Frame the most recent corner of the 3D contribution city as a wide strip."""
    w, h = 1000, 417
    root_end = skyline_svg.index(">", skyline_svg.index("<svg")) + 1
    inner = (f'<svg x="2" y="2" width="{w - 4}" height="{h - 4}" viewBox="{" ".join(map(str, crop))}" '
             f'preserveAspectRatio="xMidYMid slice">' + skyline_svg[root_end:])
    label = (f'<g {FONT}><text x="34" y="43" font-size="14" letter-spacing="2.6" font-weight="600" fill="{CYAN_SOFT}">CONTRIBUTION CITY</text>'
             f'<text x="34" y="66" font-size="13" fill="{MUTED}">My most recent weeks, rebuilt daily</text></g>')
    return frame("Contribution City", "The newest corner of my 3D contribution skyline.", "    " + inner + label, w, h)


def social_button(s):
    w, h = 180, 56
    color = {"pink": PINK, "cyan": CYAN, "lavender": LAVENDER}.get(s.get("accent"), PINK)
    body = (icon(s["icon"], 22, 16, 24, color)
            + f'\n    <text x="58" y="34" font-size="16" font-weight="600" fill="{INK}" {FONT}>{escape(s["name"])}</text>')
    return frame(s["name"], f"Find me on {s['name']}", "    " + body, w, h, rx=14)


def static_panels(cfg):
    """Panels drawn from the config alone (no GitHub data): the constellation,
    the app grid and the Working On track. `--static` renders just these."""
    groups = cfg.get("apps", [])
    out = {}
    if groups:
        out["envy-constellation.svg"] = constellation(groups)
        k = 0
        for gi, g in enumerate(groups):
            out[f"envy-group-{g['id']}.svg"] = group_label(g, gi)
            for a in g["apps"]:
                out[f"envy-app-{a['repo']}.svg"] = app_tile(a, g.get("accent"), k)
                k += 1
    if cfg.get("working"):
        out["envy-working.svg"] = now_building(cfg["working"])
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if "--static" in sys.argv:
        with open(os.path.join(root, "my-settings", "envy-panels.json")) as f:
            cfg = json.load(f)
        out = os.path.join(root, cfg.get("outputDir", "profile-assets"))
        for name, svg in static_panels(cfg).items():
            with open(os.path.join(out, name), "w") as f:
                f.write(svg)
            print(f"wrote {name}")
        return
    with open(os.path.join(root, "my-settings", "envy-panels.json")) as f:
        cfg = json.load(f)
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    user = fetch(cfg["username"], token)

    out = os.path.join(root, cfg.get("outputDir", "profile-assets"))
    panels = {
        "envy-score.svg": score_panel(user),
        "envy-stack.svg": stack_panel(user, cfg.get("stack", [])),
        "envy-activity.svg": activity_panel(user),
        "envy-building.svg": building_panel(user, cfg.get("building", [])),
        "envy-stats.svg": stats_strip(user),
        "envy-heatmap.svg": heatmap_panel(user),
        "envy-recent.svg": recent_panel(fetch_events(cfg["username"], token), cfg["username"]),
        "envy-topics.svg": topics_strip(cfg.get("topics", [])),
        "envy-divider.svg": moon_divider(),
        "envy-typing.svg": typing_banner(cfg.get("typing", ["building with a little neon"])),
    }
    skyline = os.path.join(root, "profile-3d-contrib", "profile-envy-3d.svg")
    if os.path.exists(skyline):
        with open(skyline) as f:
            panels["envy-skyline.svg"] = skyline_strip(f.read())
    for sec in cfg.get("sections", []):
        panels[f"envy-section-{sec['id']}.svg"] = section_banner(sec)
    repos = {r["name"]: r for r in user["repositories"]["nodes"]}
    for p in cfg.get("featured", []):
        panels[f"envy-project-{p['repo']}.svg"] = project_card(p, repos.get(p["repo"]), len(panels))
    for s in cfg.get("social", []):
        panels[f"envy-social-{s['name'].lower().replace(' ', '-')}.svg"] = social_button(s)
    panels.update(static_panels(cfg))
    for name, svg in panels.items():
        with open(os.path.join(out, name), "w") as f:
            f.write(svg)
        print(f"wrote {os.path.join(cfg.get('outputDir', 'profile-assets'), name)}")


if __name__ == "__main__":
    main()
