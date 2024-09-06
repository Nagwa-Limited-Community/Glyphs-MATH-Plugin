import AppKit
import traceback
import vanilla

from functools import cached_property
from GlyphsApp import GSGlyphReference, GSMetricsTypexHeight, Message
from OpenTypeMathPlugin import NSLocalizedString
from OpenTypeMathPlugin.constants import (
    CONSTANTS_ID,
    CONSTANT_UNSIGNED,
    EXTENDED_SHAPE_ID,
    H_ASSEMBLY_ID,
    H_VARIANTS_ID,
    MATH_CONSTANTS,
    MATH_CONSTANTS_BARS,
    MATH_CONSTANTS_FRACTIONS,
    MATH_CONSTANTS_GENERAL,
    MATH_CONSTANTS_LIMITS,
    MATH_CONSTANTS_RADICALS,
    MATH_CONSTANTS_SCRIPTS,
    MATH_CONSTANTS_STACKS,
    MATH_CONSTANTS_TOOLTIPS,
    NAME,
    VARIANTS_ID,
    V_ASSEMBLY_ID,
    V_VARIANTS_ID,
)


def _message(message):
    Message(message, NAME)


class VariantsWindow:
    def __init__(self, layer):
        self.layer = layer
        self.glyph = glyph = layer.parent
        width, height = 650, 400
        title = NSLocalizedString(
            "MATH Variants for ‘{glyphName}’ from {familyName}", ""
        )
        title = title.format(glyphName=glyph.name, familyName=glyph.parent.familyName)
        self.window = window = vanilla.Window(
            (width, height),
            title,
        )
        window.tabs = vanilla.Tabs(
            "auto",
            [NSLocalizedString("Vertical", ""), NSLocalizedString("Horizontal", "")],
        )

        self.emptyRow = {"g": "", "s": 0, "e": 0, "f": False}

        for i, tab in enumerate(window.tabs):
            tab.vLabel = vanilla.TextBox("auto", NSLocalizedString("Variants:", ""))
            tab.vButton = vanilla.Button(
                "auto", "🪄", callback=self.guessVariantsCallback
            )
            tab.vButton.getNSButton().setTag_(i)

            tab.vEdit = vanilla.EditText(
                "auto", continuous=False, callback=self.editTextCallback
            )
            tab.vEdit.getNSTextField().setTag_(i)

            tab.aLabel = vanilla.TextBox("auto", NSLocalizedString("Assembly:", ""))
            tab.aButton = vanilla.Button(
                "auto", "🪄", callback=self.guessAssemblyCallback
            )
            tab.aButton.getNSButton().setTag_(i)

            tab.prev = vanilla.Button("auto", "⬅️", callback=self.prevCallback)
            tab.next = vanilla.Button("auto", "➡️", callback=self.nextCallback)
            tab.prev.bind("[", ["command"])
            tab.next.bind("]", ["command"])

            tab.aList = vanilla.List(
                "auto",
                [],
                columnDescriptions=[
                    {"key": "g", "title": NSLocalizedString("Glyph", "")},
                    {"key": "s", "title": NSLocalizedString("Start Connector", "")},
                    {"key": "e", "title": NSLocalizedString("End Connector", "")},
                    {
                        "key": "f",
                        "title": NSLocalizedString("Extender", ""),
                        "cell": vanilla.CheckBoxListCell(),
                    },
                ],
                allowsSorting=False,
                drawVerticalLines=True,
                enableDelete=True,
                editCallback=self.listEditCallback,
                doubleClickCallback=self.listDoubleClickCallback,
            )
            tab.aList.getNSTableView().setTag_(i)

            tab.check = vanilla.CheckBox(
                "auto",
                NSLocalizedString("Extended shape", ""),
                callback=self.checkBoxCallback,
            )
            tab.check.show(i == 0)

            if i == 0:
                rules = [
                    "V:[aList]-[check(22)]-4-[prev]-|",
                    "V:[check]-4-[next]",
                    "H:|-[check]-|",
                ]
            else:
                rules = ["V:[aList]-[prev]-|", "V:[aList]-[next]"]
            rules.extend(
                [
                    "V:|[vButton]-6-[vEdit(40)]-[aButton]-6-[aList]",
                    "V:[vLabel]-6-[vEdit]",
                    "H:|-[vLabel]-[vButton(26)]-|",
                    f"H:|-[vEdit({width})]-|",
                    "H:|-[aLabel]-[aButton(26)]-|",
                    "V:[aLabel]-6-[aList]",
                    "H:|-[aList]-|",
                    "H:|-[prev]-4-[next(==prev)]-|",
                ]
            )
            tab.addAutoPosSizeRules(rules)

        rules = [
            "V:|-[tabs]-|",
            "H:|-[tabs]-|",
        ]
        window.addAutoPosSizeRules(rules)

        if varData := glyph.userData[VARIANTS_ID]:
            if vVars := varData.get(V_VARIANTS_ID):
                window.tabs[0].vEdit.set(" ".join(str(v) for v in vVars))
            if hVars := varData.get(H_VARIANTS_ID):
                window.tabs[1].vEdit.set(" ".join(str(v) for v in hVars))

        if varData := layer.userData[VARIANTS_ID]:
            if vAssembly := varData.get(V_ASSEMBLY_ID):
                items = []
                for part in vAssembly:
                    part = list(part)
                    part[0] = str(part[0])
                    part[1] = bool(part[1])
                    items.append(dict(zip(("g", "f", "s", "e"), part)))
                window.tabs[0].aList.set(items)
            if hAssembly := varData.get(H_ASSEMBLY_ID):
                items = []
                for part in hAssembly:
                    part = list(part)
                    part[0] = str(part[0])
                    part[1] = bool(part[1])
                    items.append(dict(zip(("g", "f", "s", "e"), part)))
                window.tabs[1].aList.set(items)

        if extended := glyph.userData[EXTENDED_SHAPE_ID]:
            window.tabs[0].check.set(bool(extended))

    def open(self):
        self.window.open()

    def glyphRef(self, name):
        try:
            return GSGlyphReference(self.glyph.parent.glyphs[name])
        except:
            _message(traceback.format_exc())

    def openGlyph(self, glyph):
        posSize = self.window.getPosSize()
        selected = self.window.tabs.get()
        self.window.close()
        window = VariantsWindow(glyph.layers[self.layer.associatedMasterId])
        window.window.setPosSize(posSize)
        window.window.tabs.set(selected)
        window.open()

    def nextCallback(self, sender):
        try:
            font = self.glyph.parent
            glyphOrder = [g.name for g in font.glyphs]
            index = glyphOrder.index(self.glyph.name)
            if index < len(glyphOrder) - 1:
                self.openGlyph(font.glyphs[index + 1])
        except:
            _message(traceback.format_exc())

    def prevCallback(self, sender):
        try:
            font = self.glyph.parent
            glyphOrder = [g.name for g in font.glyphs]
            index = glyphOrder.index(self.glyph.name)
            if index > 0:
                self.openGlyph(font.glyphs[index - 1])
        except:
            _message(traceback.format_exc())

    def guessVariantsCallback(self, sender):
        try:
            tag = sender.getNSButton().tag()
            glyph = self.glyph
            font = glyph.parent
            name = glyph.name

            alternates = [g.name for g in font.glyphs if g.name.startswith(name + ".")]
            if not alternates:
                return

            suffixes = ["size", "s"]
            varId = H_VARIANTS_ID if tag else V_VARIANTS_ID
            if varId == V_VARIANTS_ID:
                suffixes += ["disp", "display"]

            for suffix in suffixes:
                prefix = f"{name}.{suffix}"
                n_prefix = len(prefix)
                variants = []
                for alternate in alternates:
                    if alternate.startswith(prefix) and alternate[n_prefix:].isdigit():
                        variants.append(alternate)
                    elif alternate == prefix:
                        variants.append(alternate)
                if variants:
                    tab = self.window.tabs[tag]
                    tab.vEdit.set(" ".join([name] + variants))
                    self.editTextCallback(tab.vEdit)
                    return
        except:
            _message(traceback.format_exc())

    def guessAssembly(self, vertical):
        glyph = self.glyph
        font = glyph.parent
        name = glyph.name

        for l, r, t, b, m, e in [
            ["lft", "rgt", "top", "bot", "mid", "ext"],
            ["left", "right", "top", "bottom", "middle", "extension"],
            ["l", "r", "t", "b", "m", "x"],
        ]:
            if (ext := font.glyphs[f"{name}.{e}"]) is None:
                continue

            mid = font.glyphs[f"{name}.{m}"]
            if vertical:
                top = font.glyphs[f"{name}.{t}"]
                bot = font.glyphs[f"{name}.{b}"]
                if not top and not bot:
                    continue
                if bot and not top:
                    parts = [bot, ext]
                elif top and not bot:
                    parts = [ext, top]
                elif mid:
                    parts = [bot, ext, mid, ext, top]
                else:
                    parts = [bot, ext, top]
            else:
                lft = font.glyphs[f"{name}.{l}"]
                rgt = font.glyphs[f"{name}.{r}"]
                if not lft and not rgt:
                    continue
                if lft and not rgt:
                    parts = [lft, ext]
                elif rgt and not lft:
                    parts = [ext, rgt]
                elif mid:
                    parts = [lft, ext, mid, ext, rgt]
                else:
                    parts = [lft, ext, rgt]

            return parts

    def guessAssemblyCallback(self, sender):
        try:
            tag = sender.getNSButton().tag()

            assemblyId = H_ASSEMBLY_ID if tag else V_ASSEMBLY_ID
            vertical = assemblyId == V_ASSEMBLY_ID
            if (parts := self.guessAssembly(vertical)) is None:
                # Fallback using legacy encoded assembly parts
                glyph = self.glyph
                font = glyph.parent
                name = glyph.name
                unicode = glyph.unicode

                names = []
                if name == "parenleft" or unicode == "0028":
                    names = ["239D", "239C", "239B"]
                elif name == "parenright" or unicode == "0029":
                    names = ["23A0", "239F", "239E"]
                elif name == "bracketleft" or unicode == "005B":
                    names = ["23A3", "23A2", "23A1"]
                elif name == "bracketright" or unicode == "005D":
                    names = ["23A6", "23A5", "23A4"]
                elif name == "braceleft" or unicode == "007B":
                    names = ["23A9", "23AA", "23A8", "23AA", "23A7"]
                elif name == "braceright" or unicode == "007D":
                    names = ["23AD", "23AA", "23AC", "23AA", "23AB"]
                elif name == "integral" or unicode == "222B":
                    names = ["2321", "23AE", "2320"]
                elif name == "radical" or unicode == "221A":
                    names = ["23B7", "2502", "250C"]
                elif unicode == "23B0":
                    names = ["23AD", "23AA", "23A7"]
                elif unicode == "23B1":
                    names = ["23A9", "23AA", "23AB"]
                elif unicode in {
                    "007C",
                    "2016",
                    "2223",
                    "2225",
                    "2980",
                    "0305",
                    "0332",
                }:
                    names = [name, name]

                parts = [font.glyphs[n] for n in names]
                if not all(parts):
                    return

            if not parts:
                return

            tab = self.window.tabs[tag]
            items = []
            for i, part in enumerate(parts):
                ext = bool(i % 2)
                layer = part.layers[self.layer.associatedMasterId]
                # Guess start and end connector lengths.
                #
                # This is rather crude. The idea is to find the line segments in the
                # respective direction (vertical or horizontal) that are at the
                # respective end (top/bottom, right/left).
                # If the line segments are in pairs, we assume these are straight stems
                # ans then take the length of the shortest of those segments.
                #
                # The first (top or left) part is skipped for start connector length,
                # ditto for the last (bottom or right) part for end connector length.
                start = end = 0
                for shape in layer.shapes:
                    path = shape.bezierPath
                    if vertical:
                        # Find vertical lines
                        lines = [
                            s.bounds
                            for s in path.segments()
                            if int(s.bounds.size.height)
                            and not int(s.bounds.size.width)
                        ]
                        # Find lines at top and bottom
                        starts = [
                            l for l in lines if l.origin.y == layer.bounds.origin.y
                        ]
                        ends = [
                            l
                            for l in lines
                            if (l.origin.y + l.size.height)
                            == (layer.bounds.origin.y + layer.bounds.size.height)
                        ]
                        if i != 0 and len(starts) and (len(starts) % 2) == 0:
                            start = min(a.size.height for a in starts)
                        if (i < len(parts) - 1) and len(ends) and (len(ends) % 2) == 0:
                            end = min(a.size.height for a in ends)
                    else:
                        # Find horizontal lines
                        lines = [
                            s.bounds
                            for s in path.segments()
                            if int(s.bounds.size.width)
                            and not int(s.bounds.size.height)
                        ]
                        # Find lines at left and right
                        starts = [
                            l for l in lines if l.origin.x == layer.bounds.origin.x
                        ]
                        ends = [
                            l
                            for l in lines
                            if (l.origin.x + l.size.width)
                            == (layer.bounds.origin.x + layer.bounds.size.width)
                        ]
                        if i != 0 and len(starts) and (len(starts) % 2) == 0:
                            start = min(a.size.width for a in starts)
                        if (i < len(parts) - 1) and len(ends) and (len(ends) % 2) == 0:
                            end = min(a.size.width for a in ends)

                items.append({"g": part.name, "f": ext, "s": start, "e": end})
            tab.aList.set(items)
            self.listEditCallback(tab.aList)
            return
        except:
            _message(traceback.format_exc())

    def editTextCallback(self, sender):
        try:
            new = sender.get().strip()

            glyph = self.glyph
            tag = sender.getNSTextField().tag()
            varData = glyph.userData.get(VARIANTS_ID, {})
            variantsId = H_VARIANTS_ID if tag else V_VARIANTS_ID

            if var := varData.get(variantsId):
                if " ".join(str(v) for v in var) == new:
                    return

            if new:
                varData = {k: list(v) for k, v in varData.items()}
                var = [self.glyphRef(n) for n in new.split()]
                varData[variantsId] = var
            elif variantsId in varData:
                del varData[variantsId]
            if varData:
                glyph.userData[VARIANTS_ID] = dict(varData)
            elif VARIANTS_ID in glyph.userData:
                del glyph.userData[VARIANTS_ID]
        except:
            _message(traceback.format_exc())

    def listEditCallback(self, sender):
        try:
            new = [
                (
                    self.glyphRef(item["g"]),
                    int(item["f"]),
                    int(item["s"]),
                    int(item["e"]),
                )
                for item in sender.get()
                if item != self.emptyRow
            ]

            layer = self.layer
            tag = sender.getNSTableView().tag()
            varData = layer.userData.get(VARIANTS_ID, {})
            assemblyId = H_ASSEMBLY_ID if tag else V_ASSEMBLY_ID

            if varData.get(assemblyId) == new:
                return
            if new:
                varData = {k: list(v) for k, v in varData.items()}
                varData[assemblyId] = new
            elif assemblyId in varData:
                del varData[assemblyId]
            layer.userData[VARIANTS_ID] = dict(varData)
        except:
            _message(traceback.format_exc())

    def listDoubleClickCallback(self, sender):
        try:
            table = sender.getNSTableView()
            column = table.clickedColumn()
            row = table.clickedRow()
            if row < 0 and column < 0:
                items = sender.get()
                items.append(self.emptyRow)
                sender.set(items)
                row = len(items) - 1
            table._startEditingColumn_row_event_(column, row, None)
        except:
            _message(traceback.format_exc())

    def checkBoxCallback(self, sender):
        try:
            glyph = self.glyph
            glyph.userData[EXTENDED_SHAPE_ID] = sender.get()
            if not sender.get():
                del glyph.userData[EXTENDED_SHAPE_ID]
        except:
            _message(traceback.format_exc())


class ConstantsWindow:
    def __init__(self, master):
        self.master = master
        if CONSTANTS_ID not in master.userData:
            constants = {}
        else:
            constants = dict(master.userData[CONSTANTS_ID])
        self.constants = constants

        width, height = 650, 400
        title = NSLocalizedString(
            "MATH Constants for master ‘{masterName}’ from {familyName}", ""
        )
        title = title.format(masterName=master.name, familyName=master.font.familyName)
        self.window = window = vanilla.Window(
            (width, height),
            title,
        )
        tabs = {
            NSLocalizedString("General", ""): MATH_CONSTANTS_GENERAL,
            NSLocalizedString("Sub/Superscript", ""): MATH_CONSTANTS_SCRIPTS,
            NSLocalizedString("Limits", ""): MATH_CONSTANTS_LIMITS,
            NSLocalizedString("Stacks", ""): MATH_CONSTANTS_STACKS,
            NSLocalizedString("Fractions", ""): MATH_CONSTANTS_FRACTIONS,
            NSLocalizedString("Over/Underbar", ""): MATH_CONSTANTS_BARS,
            NSLocalizedString("Radicals", ""): MATH_CONSTANTS_RADICALS,
        }

        uFormatter = AppKit.NSNumberFormatter.new()
        uFormatter.setAllowsFloats_(False)
        uFormatter.setMinimum_(0)
        uFormatter.setMaximum_(0xFFFF)

        sFormatter = AppKit.NSNumberFormatter.new()
        sFormatter.setAllowsFloats_(False)
        sFormatter.setMinimum_(-0x7FFF)
        sFormatter.setMaximum_(0x7FFF)

        window.tabs = vanilla.Tabs("auto", tabs.keys())
        for i, name in enumerate(tabs.keys()):
            tab = window.tabs[i]
            rules = ["V:|" + "".join(f"[{c}]" for c in tabs[name]) + "|"]
            for c in tabs[name]:
                box = vanilla.Box("auto", borderWidth=0)
                box.label = vanilla.TextBox("auto", c)
                box.label.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])

                box.edit = vanilla.EditText(
                    "auto",
                    constants.get(c, None),
                    callback=self.editTextCallback,
                    formatter=uFormatter if c in CONSTANT_UNSIGNED else sFormatter,
                    placeholder="0",
                )
                box.edit.setToolTip(MATH_CONSTANTS_TOOLTIPS[c])
                box.edit.getNSTextField().setTag_(MATH_CONSTANTS.index(c))

                box.button = vanilla.Button(
                    "auto",
                    "🪄",
                    callback=self.guessCallback,
                )
                box.button.getNSButton().setToolTip_(
                    NSLocalizedString("Guess value", "")
                )
                box.button.getNSButton().setTag_(MATH_CONSTANTS.index(c))

                box.addAutoPosSizeRules(
                    [
                        "H:[label]-[edit(60)]-[button(24)]",
                        "V:|[button]|",
                    ]
                )
                box.label._nsObject.centerYAnchor().constraintEqualToAnchor_(
                    box.button._nsObject.centerYAnchor()
                ).setActive_(True)

                box.edit._nsObject.centerYAnchor().constraintEqualToAnchor_(
                    box.button._nsObject.centerYAnchor()
                ).setActive_(True)

                box.edit._nsObject.centerXAnchor().constraintEqualToAnchor_(
                    box._nsObject.centerXAnchor()
                ).setActive_(True)

                rules.append(f"H:|[{c}]|")
                setattr(tab, f"{c}", box)
            tab.addAutoPosSizeRules(rules)

        rules = [
            "V:|-[tabs]-|",
            "H:|-[tabs]-|",
        ]
        window.addAutoPosSizeRules(rules)

    def open(self):
        self.window.open()

    @cached_property
    def defaultRuleThickness(self):
        master = self.master
        font = master.font

        value = None

        # "minus" thickness
        if glyph := font.glyphs["−"]:
            value = value = glyph.layers[master.id].bounds.size.height

        # "underscore" thickness
        if not value and (glyph := font.glyphs["_"]):
            value = glyph.layers[master.id].bounds.size.height

        # "overline" thickness
        if not value and (glyph := font.glyphs["\u0305"]):
            value = glyph.layers[master.id].bounds.size.height

        if not value:
            value = master.customParameters["yStrikeoutSize"]
        return value

    def ruleThickness(self):
        if rule := self.getConstant("FractionRuleThickness"):
            return rule
        return self.defaultRuleThickness

    def getConstant(self, constant, force=False):
        master = self.master
        font = master.font

        if not force and constant in self.constants:
            return self.constants[constant]

        value = None
        if constant == "ScriptPercentScaleDown":
            value = 80
        elif constant == "ScriptScriptPercentScaleDown":
            value = 60
        elif constant == "DelimitedSubFormulaMinHeight":
            value = (master.ascender - master.descender) * 1.5
        elif constant == "DisplayOperatorMinHeight":
            # display "integral" height
            if (glyph := font.glyphs["∫"]) is not None:
                if varData := glyph.userData[VARIANTS_ID]:
                    if vVars := varData.get(V_VARIANTS_ID):
                        value = vVars[1].glyph.layers[master.id].bounds.size.height
        elif constant == "MathLeading":
            if (value := master.customParameters["typoLineGap"]) is None:
                value = master.customParameters["hheaLineGap"]
        elif constant == "AxisHeight":
            # "minus" midline
            if (glyph := font.glyphs["−"]) is not None:
                bounds = glyph.layers[master.id].bounds
                value = bounds.origin.y + bounds.size.height / 2
        elif constant == "AccentBaseHeight":
            for metric in font.metrics:
                if metric.type == GSMetricsTypexHeight and metric.filter is None:
                    metricValue = master.metricValues[metric.id]
                    value = metricValue.position + metricValue.overshoot
                    break
            if not value:
                value = master.xHeight
        elif constant == "FlattenedAccentBaseHeight":
            value = master.capHeight
        elif constant == "SubscriptShiftDown":
            value = master.customParameters["subscriptYOffset"]
        elif constant == "SubscriptTopMax":
            value = master.xHeight * 4 / 5
        elif constant == "SubscriptBaselineDropMin":
            if (value := self.getConstant("SubscriptShiftDown")) is not None:
                value *= 3 / 4
        elif constant == "SuperscriptShiftUp":
            value = master.customParameters["superscriptYOffset"]
        elif constant == "SuperscriptShiftUpCramped":
            if (value := self.getConstant("SuperscriptShiftUp")) is not None:
                value *= 3 / 4
        elif constant == "SuperscriptBottomMin":
            value = master.xHeight / 4
        elif constant == "SuperscriptBaselineDropMax":
            if (v := self.getConstant("SuperscriptShiftUp")) is not None:
                value = master.capHeight - v
        elif constant == "SubSuperscriptGapMin":
            if rule := self.ruleThickness():
                value = rule * 4
        elif constant == "SuperscriptBottomMaxWithSubscript":
            value = master.xHeight * 4 / 5
        elif constant == "SpaceAfterScript":
            value = font.upm / 24
        elif constant == "UpperLimitGapMin":
            if rule := self.ruleThickness():
                value = rule * 2
        elif constant == "UpperLimitBaselineRiseMin":
            value = -master.descender * 3 / 4
        elif constant == "LowerLimitGapMin":
            value = self.getConstant("UpperLimitGapMin")
        elif constant == "LowerLimitBaselineDropMin":
            value = master.ascender * 3 / 4
        elif constant == "StackTopShiftUp":
            value = master.xHeight
        elif constant == "StackTopDisplayStyleShiftUp":
            value = master.xHeight * 3 / 2
        elif constant == "StackBottomShiftDown":
            value = master.capHeight * 2 / 3
        elif constant == "StackBottomDisplayStyleShiftDown":
            value = master.capHeight
        elif constant == "StackGapMin":
            if rule := self.ruleThickness():
                value = rule * 3
        elif constant == "StackDisplayStyleGapMin":
            if rule := self.ruleThickness():
                value = rule * 7
        elif constant == "StretchStackTopShiftUp":
            value = self.getConstant("UpperLimitBaselineRiseMin")
        elif constant == "StretchStackBottomShiftDown":
            value = self.getConstant("LowerLimitBaselineDropMin")
        elif constant == "StretchStackGapAboveMin":
            value = self.getConstant("UpperLimitGapMin")
        elif constant == "StretchStackGapBelowMin":
            value = self.getConstant("LowerLimitGapMin")
        elif constant == "FractionNumeratorShiftUp":
            value = self.getConstant("StackTopShiftUp")
        elif constant == "FractionNumeratorDisplayStyleShiftUp":
            value = self.getConstant("StackTopDisplayStyleShiftUp")
        elif constant == "FractionDenominatorShiftDown":
            value = self.getConstant("StackBottomShiftDown")
        elif constant == "FractionDenominatorDisplayStyleShiftDown":
            value = self.getConstant("StackBottomDisplayStyleShiftDown")
        elif constant == "FractionNumeratorGapMin":
            value = self.ruleThickness()
        elif constant == "FractionNumDisplayStyleGapMin":
            if rule := self.ruleThickness():
                value = rule * 3
        elif constant == "FractionRuleThickness":
            value = self.defaultRuleThickness
        elif constant == "FractionDenominatorGapMin":
            value = self.ruleThickness()
        elif constant == "FractionDenomDisplayStyleGapMin":
            if rule := self.ruleThickness():
                value = rule * 3
        elif constant == "SkewedFractionHorizontalGap":
            # TODO
            pass
        elif constant == "SkewedFractionVerticalGap":
            # TODO
            pass
        elif constant == "OverbarVerticalGap":
            if rule := self.ruleThickness():
                value = rule * 3
        elif constant == "OverbarRuleThickness":
            value = self.ruleThickness()
        elif constant == "OverbarExtraAscender":
            value = self.ruleThickness()
        elif constant == "UnderbarVerticalGap":
            if rule := self.ruleThickness():
                value = rule * 3
        elif constant == "UnderbarRuleThickness":
            value = self.ruleThickness()
        elif constant == "UnderbarExtraDescender":
            value = self.ruleThickness()
        elif constant == "RadicalVerticalGap":
            if rule := self.ruleThickness():
                value = rule * 5 / 4
        elif constant == "RadicalDisplayStyleVerticalGap":
            if rule := self.ruleThickness():
                value = rule + master.xHeight / 4
        elif constant == "RadicalRuleThickness":
            value = self.ruleThickness()
        elif constant == "RadicalExtraAscender":
            if (value := self.getConstant("RadicalRuleThickness")) is None:
                value = self.getConstant("FractionRuleThickness")
        elif constant == "RadicalKernBeforeDegree":
            value = font.upm * 5 / 18
        elif constant == "RadicalKernAfterDegree":
            value = -font.upm * 10 / 18
        elif constant == "RadicalDegreeBottomRaisePercent":
            value = 60
        elif constant == "MinConnectorOverlap":
            value = 0.05 * font.upm

        if value is not None:
            value = round(value)
        return value

    def guessCallback(self, sender):
        constant = MATH_CONSTANTS[sender.getNSButton().tag()]
        if (value := self.getConstant(constant, force=True)) is not None:
            for tab in self.window.tabs:
                box = getattr(tab, constant, None)
                if box is not None:
                    box.edit.set(value)
                    self.editTextCallback(box.edit)

    def editTextCallback(self, sender):
        constants = self.constants
        value = sender.get()
        if value is not None:
            value = int(round(value))
        tag = sender.getNSTextField().tag()

        constant = MATH_CONSTANTS[tag]
        if constants.get(constant) == value:
            return

        if value is not None:
            constants[constant] = value
        elif constant in constants:
            del constants[constant]

        if constants:
            self.master.userData[CONSTANTS_ID] = constants
        elif CONSTANTS_ID in self.master.userData:
            del self.master.userData[CONSTANTS_ID]
