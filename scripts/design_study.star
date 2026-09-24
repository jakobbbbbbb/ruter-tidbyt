load("render.star", "render")

INK = "#f2f2e8"
MUTED = "#939b98"
AMBER = "#e8b85c"

def label(value, font = "tb-8", color = INK):
    return render.Text(value, font = font, color = color)

def placed(child, left, top):
    return render.Padding(pad = (left, top, 0, 0), child = child)

def route(font, solid = True):
    return render.Box(width = 12, height = 9, color = "#ba3038" if solid else "#000000", child = label("37", font, INK if solid else AMBER))

def main(config):
    design = config.get("design", "focus")
    widgets = []
    if design in ["compact", "mono", "board", "quiet", "two_rows"]:
        font = {"compact": "tom-thumb", "mono": "CG-pixel-3x5-mono", "board": "tb-8", "quiet": "5x8", "two_rows": "6x10"}[design]
        widgets.append(placed(label("COLLETTS GT", "tom-thumb", MUTED), 1, 1))
        count = 2 if design == "two_rows" else 3
        for index in range(count):
            top = 8 + index * (12 if count == 2 else 8)
            number = label(["2m", "8m", "18m"][index], font, AMBER if index == 0 else INK)
            widgets.extend([
                placed(route("CG-pixel-3x5-mono", design != "quiet"), 1, top),
                placed(label("Helsfyr" if design in ["compact", "mono"] else "Helsf.", font), 15, top),
                placed(number, 63 - number.size()[0], top),
            ])
    elif design in ["platform", "platform_mono", "platform_large"]:
        font = {"platform": "tb-8", "platform_mono": "5x8", "platform_large": "6x10"}[design]
        countdown = label("2 min", "6x13", AMBER)
        widgets.extend([
            placed(label("COLLETTS GT", "tom-thumb", MUTED), 1, 0),
            placed(label("1/3", "tom-thumb", MUTED), 51, 0),
            placed(route("tb-8"), 1, 9),
            placed(countdown, 63 - countdown.size()[0], 7),
            placed(label("Helsfyr", font), 1, 22 if design != "platform_large" else 20),
        ])
    elif design in ["focus", "rounded", "large"]:
        font = {"focus": "tb-8", "rounded": "6x10-rounded", "large": "6x13"}[design]
        widgets.extend([
            placed(label("COLLETTS GT", "tom-thumb", MUTED), 1, 0),
            placed(label("1/3", "tom-thumb", MUTED), 51, 0),
            placed(route("tb-8"), 1, 8),
            placed(label("Helsfyr", font), 16, 8),
            placed(label("2", "6x13", AMBER), 1, 19),
            placed(label("min", "tb-8", AMBER), 10, 23),
            placed(label("8m 12:18", "tom-thumb", MUTED), 31, 25),
        ])
    return render.Root(child = render.Stack(children = widgets))
