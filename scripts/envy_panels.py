#!/usr/bin/env python3
"""Generate the ENVY profile panels (score, stack, activity, building) as SVGs.

Reads my-settings/envy-panels.json and live data from the GitHub GraphQL API.
Needs GITHUB_TOKEN in the environment. Standard library only.
"""
import datetime as dt
import json
import math
import os
import sys
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

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        name stargazerCount pushedAt
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


def card(title, kicker, desc, body):
    """Wrap panel content in the shared ENVY card frame."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title description">
  <title id="title">{escape(title)}</title>
  <desc id="description">{escape(desc)}</desc>
  <defs>
    <linearGradient id="edge"><stop stop-color="{PINK}" stop-opacity=".55"/><stop offset=".5" stop-color="{LAVENDER}" stop-opacity=".2"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".65"/></linearGradient>
    <linearGradient id="neon"><stop stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
    <radialGradient id="cloud"><stop stop-color="#0d5666" stop-opacity=".45"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <radialGradient id="pink"><stop stop-color="#a71c7d" stop-opacity=".2"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <clipPath id="clip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20"/></clipPath>
  </defs>
  <style>.signal{{animation:pulse 7s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:.95}}}}@media(prefers-reduced-motion:reduce){{.signal{{animation:none}}}}</style>
  <g clip-path="url(#clip)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <ellipse cx="{W - 80}" cy="{H // 2}" rx="260" ry="200" fill="url(#cloud)"/>
    <ellipse cx="90" cy="{H - 10}" rx="320" ry="210" fill="url(#pink)"/>
    <g fill="#a8c7ed" opacity=".3"><circle cx="445" cy="26" r="1"/><circle cx="562" cy="{H - 24}" r="1"/><circle cx="690" cy="43" r="1.2"/><circle cx="398" cy="{H - 18}" r=".8"/></g>
    <g {FONT}>
      <text x="34" y="43" font-size="14" letter-spacing="2.6" font-weight="600" fill="{CYAN_SOFT}">{escape(kicker)}</text>
      <text x="32" y="80" font-size="28" letter-spacing="1" font-weight="700" fill="{INK}">{escape(title)}</text>
    </g>
    <path d="M34 96h55" stroke="{PINK}" stroke-width="2"/>
    <path d="M95 96h24" stroke="{LAVENDER}" stroke-opacity=".4" stroke-width="2"/>
{body}
  </g>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="20" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
"""


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
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#neon)" stroke-width="12" stroke-linecap="round"
      stroke-dasharray="{circ * score / 100:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>
    <circle class="signal" cx="{cx}" cy="{cy}" r="{r + 16}" fill="none" stroke="{CYAN}" stroke-opacity=".25"/>
    <g {FONT} text-anchor="middle">
      <text x="{cx}" y="{cy + 14}" font-size="46" font-weight="700" fill="{INK}">{grade}</text>
      <text x="{cx}" y="{cy + 40}" font-size="14" letter-spacing="1.5" fill="{CYAN_SOFT}">{score} / 100</text>
    </g>
    <text x="34" y="{H - 14}" font-size="11" fill="{MUTED}" opacity=".6" {FONT}>Past 12 months · ENVY formula, not an official GitHub rank</text>"""
    desc = f"ENVY GitHub score {grade}, {score} out of 100, from commits, pull requests, issues, reviews, stars and followers."
    return card("GitHub Score", "02 / SIGNAL STRENGTH", desc, body)


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
    return card("Tech Stack", "03 / TOOLS OF THE TRADE", desc, body)


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
    <polyline points="{line}" fill="none" stroke="url(#neon)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
    <circle class="signal" cx="{lx:.1f}" cy="{ly:.1f}" r="9" fill="{CYAN}" fill-opacity=".3"/>
    <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="#9bf7ff"/>
    <g {FONT}>
      <text x="{x0}" y="{y1 + 22}" font-size="12" fill="{MUTED}">{first}</text>
      <text x="{x1}" y="{y1 + 22}" font-size="12" fill="{MUTED}" text-anchor="end">{last}</text>
      <text x="{x0 - 4}" y="{y0 - 6}" font-size="11" fill="{MUTED}" opacity=".7">{peak}/day</text>
      {stat_svg}
    </g>"""
    desc = f"{sum(counts)} contributions in the last {days} days, {cal['totalContributions']} this year, {streak} day streak."
    return card("Contribution Activity", "04 / FREQUENCY", desc, body)


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
    return card("Currently Building", "05 / ON THE WORKBENCH", desc, "\n".join(rows))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    }
    for name, svg in panels.items():
        with open(os.path.join(out, name), "w") as f:
            f.write(svg)
        print(f"wrote {os.path.join(cfg.get('outputDir', 'profile-assets'), name)}")


if __name__ == "__main__":
    main()
