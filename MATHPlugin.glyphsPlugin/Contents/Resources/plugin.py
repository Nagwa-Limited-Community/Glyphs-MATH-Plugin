# Copyright 2021 Nagwa Limited

import traceback

import objc
import vanilla
import AppKit

from functools import cached_property

from fontTools.ttLib import TTFont
from GlyphsApp import (
    DOCUMENTEXPORTED,
    DOCUMENTOPENED,
    DRAWBACKGROUND,
    EDIT_MENU,
    GLYPH_MENU,
    VIEW_MENU,
    Glyphs,
    GSAnchor,
    GSGlyphReference,
    Message,
    GSCallbackHandler,
    GSMetricsTypexHeight,
)
from GlyphsApp.drawingTools import restore, save, translate
from GlyphsApp.plugins import GeneralPlugin

NAME = "OpenType MATH Plug-in"

PLUGIN_ID = "com.nagwa.MATHPlugin"
CONSTANTS_ID = PLUGIN_ID + ".constants"
STATUS_ID = PLUGIN_ID + ".status"

EXTENDED_SHAPE_ID = PLUGIN_ID + ".extendedShape"

VARIANTS_ID = PLUGIN_ID + ".variants"
V_VARIANTS_ID = "vVariants"
H_VARIANTS_ID = "hVariants"
V_ASSEMBLY_ID = "vAssembly"
H_ASSEMBLY_ID = "hAssembly"

ITALIC_CORRECTION_ANCHOR = "math.ic"
TOP_ACCENT_ANCHOR = "math.ta"

KERN_TOP_RIGHT_ANCHOR = "math.tr"
KERN_TOP_LEFT_ANCHOR = "math.tl"
KERN_BOTTOM_RIGHT_ANCHOR = "math.br"
KERN_BOTTOM_LEFT_ANCHOR = "math.bl"

MATH_CONSTANTS_GENERAL = [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
    "MathLeading",
    "AxisHeight",
    "AccentBaseHeight",
    "FlattenedAccentBaseHeight",
    "MinConnectorOverlap",
]

MATH_CONSTANTS_SCRIPTS = [
    "SubscriptShiftDown",
    "SubscriptTopMax",
    "SubscriptBaselineDropMin",
    "SuperscriptShiftUp",
    "SuperscriptShiftUpCramped",
    "SuperscriptBottomMin",
    "SuperscriptBaselineDropMax",
    "SubSuperscriptGapMin",
    "SuperscriptBottomMaxWithSubscript",
    "SpaceAfterScript",
]

MATH_CONSTANTS_LIMITS = [
    "UpperLimitGapMin",
    "UpperLimitBaselineRiseMin",
    "LowerLimitGapMin",
    "LowerLimitBaselineDropMin",
]

MATH_CONSTANTS_STACKS = [
    "StackTopShiftUp",
    "StackTopDisplayStyleShiftUp",
    "StackBottomShiftDown",
    "StackBottomDisplayStyleShiftDown",
    "StackGapMin",
    "StackDisplayStyleGapMin",
    "StretchStackTopShiftUp",
    "StretchStackBottomShiftDown",
    "StretchStackGapAboveMin",
    "StretchStackGapBelowMin",
]

MATH_CONSTANTS_FRACTIONS = [
    "FractionNumeratorShiftUp",
    "FractionNumeratorDisplayStyleShiftUp",
    "FractionDenominatorShiftDown",
    "FractionDenominatorDisplayStyleShiftDown",
    "FractionNumeratorGapMin",
    "FractionNumDisplayStyleGapMin",
    "FractionRuleThickness",
    "FractionDenominatorGapMin",
    "FractionDenomDisplayStyleGapMin",
    "SkewedFractionHorizontalGap",
    "SkewedFractionVerticalGap",
]

MATH_CONSTANTS_BARS = [
    "OverbarVerticalGap",
    "OverbarRuleThickness",
    "OverbarExtraAscender",
    "UnderbarVerticalGap",
    "UnderbarRuleThickness",
    "UnderbarExtraDescender",
]

MATH_CONSTANTS_RADICALS = [
    "RadicalVerticalGap",
    "RadicalDisplayStyleVerticalGap",
    "RadicalRuleThickness",
    "RadicalExtraAscender",
    "RadicalKernBeforeDegree",
    "RadicalKernAfterDegree",
    "RadicalDegreeBottomRaisePercent",
]

CONSTANT_UNSIGNED = [
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
    "MinConnectorOverlap",
]

CONSTANT_INTEGERS = CONSTANT_UNSIGNED + [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "RadicalDegreeBottomRaisePercent",
]

MATH_CONSTANTS = (
    MATH_CONSTANTS_GENERAL
    + MATH_CONSTANTS_SCRIPTS
    + MATH_CONSTANTS_LIMITS
    + MATH_CONSTANTS_STACKS
    + MATH_CONSTANTS_FRACTIONS
    + MATH_CONSTANTS_BARS
    + MATH_CONSTANTS_RADICALS
)

MATH_CONSTANTS_TOOLTIPS = {
    "ScriptPercentScaleDown": "Percentage of scaling down for level 1 superscripts and subscripts. Suggested value: 80%.",
    "ScriptScriptPercentScaleDown": "Percentage of scaling down for level 2 (scriptScript) superscripts and subscripts. Suggested value: 60%.",
    "DelimitedSubFormulaMinHeight": "Minimum height required for a delimited expression (contained within parentheses, etc.) to be treated as a sub-formula. Suggested value: normal line height × 1.5.",
    "DisplayOperatorMinHeight": "Minimum height of n-ary operators (such as integral and summation) for formulas in display mode (that is, appearing as standalone page elements, not embedded inline within text).",
    "MathLeading": "White space to be left between math formulas to ensure proper line spacing. For example, for applications that treat line gap as a part of line ascender, formulas with ink going above (typoAscender + typoLineGap - MathLeading) or with ink going below typoDescender will result in increasing line height.",
    "AxisHeight": "Axis height of the font.\nIn math typesetting, the term axis refers to a horizontal reference line used for positioning elements in a formula. The math axis is similar to but distinct from the baseline for regular text layout. For example, in a simple equation, a minus symbol or fraction rule would be on the axis, but a string for a variable name would be set on a baseline that is offset from the axis. The axisHeight value determines the amount of that offset.",
    "AccentBaseHeight": "Maximum (ink) height of accent base that does not require raising the accents. Suggested: x‑height of the font plus any possible overshots.",
    "FlattenedAccentBaseHeight": "Maximum (ink) height of accent base that does not require flattening the accents. Suggested: cap height of the font.",
    "SubscriptShiftDown": "The standard shift down applied to subscript elements. Positive for moving in the downward direction. Suggested: subscriptYOffset.",
    "SubscriptTopMax": "Maximum allowed height of the (ink) top of subscripts that does not require moving subscripts further down. Suggested: 4/5 x- height.",
    "SubscriptBaselineDropMin": "Minimum allowed drop of the baseline of subscripts relative to the (ink) bottom of the base. Checked for bases that are treated as a box or extended shape. Positive for subscript baseline dropped below the base bottom.",
    "SuperscriptShiftUp": "Standard shift up applied to superscript elements. Suggested: superscriptYOffset.",
    "SuperscriptShiftUpCramped": "Standard shift of superscripts relative to the base, in cramped style.",
    "SuperscriptBottomMin": "Minimum allowed height of the (ink) bottom of superscripts that does not require moving subscripts further up. Suggested: ¼ x-height.",
    "SuperscriptBaselineDropMax": "Maximum allowed drop of the baseline of superscripts relative to the (ink) top of the base. Checked for bases that are treated as a box or extended shape. Positive for superscript baseline below the base top.",
    "SubSuperscriptGapMin": "Minimum gap between the superscript and subscript ink. Suggested: 4 × default rule thickness.",
    "SuperscriptBottomMaxWithSubscript": "The maximum level to which the (ink) bottom of superscript can be pushed to increase the gap between superscript and subscript, before subscript starts being moved down. Suggested: 4/5 x-height.",
    "SpaceAfterScript": "Extra white space to be added after each subscript and superscript. Suggested: 0.5 pt for a 12 pt font. (Note that, in some math layout implementations, a constant value, such as 0.5 pt, may be used for all text sizes. Some implementations may use a constant ratio of text size, such as 1/24 of em.)",
    "UpperLimitGapMin": "Minimum gap between the (ink) bottom of the upper limit, and the (ink) top of the base operator.",
    "UpperLimitBaselineRiseMin": "Minimum distance between baseline of upper limit and (ink) top of the base operator.",
    "LowerLimitGapMin": "Minimum gap between (ink) top of the lower limit, and (ink) bottom of the base operator.",
    "LowerLimitBaselineDropMin": "Minimum distance between baseline of the lower limit and (ink) bottom of the base operator.",
    "StackTopShiftUp": "Standard shift up applied to the top element of a stack.",
    "StackTopDisplayStyleShiftUp": "Standard shift up applied to the top element of a stack in display style.",
    "StackBottomShiftDown": "Standard shift down applied to the bottom element of a stack. Positive for moving in the downward direction.",
    "StackBottomDisplayStyleShiftDown": "Standard shift down applied to the bottom element of a stack in display style. Positive for moving in the downward direction.",
    "StackGapMin": "Minimum gap between (ink) bottom of the top element of a stack, and the (ink) top of the bottom element. Suggested: 3 × default rule thickness.",
    "StackDisplayStyleGapMin": "Minimum gap between (ink) bottom of the top element of a stack, and the (ink) top of the bottom element in display style. Suggested: 7 × default rule thickness.",
    "StretchStackTopShiftUp": "Standard shift up applied to the top element of the stretch stack.",
    "StretchStackBottomShiftDown": "Standard shift down applied to the bottom element of the stretch stack. Positive for moving in the downward direction.",
    "StretchStackGapAboveMin": "Minimum gap between the ink of the stretched element, and the (ink) bottom of the element above. Suggested: same value as upperLimitGapMin.",
    "StretchStackGapBelowMin": "Minimum gap between the ink of the stretched element, and the (ink) top of the element below. Suggested: same value as lowerLimitGapMin.",
    "FractionNumeratorShiftUp": "Standard shift up applied to the numerator.",
    "FractionNumeratorDisplayStyleShiftUp": "Standard shift up applied to the numerator in display style. Suggested: same value as stackTopDisplayStyleShiftUp.",
    "FractionDenominatorShiftDown": "Standard shift down applied to the denominator. Positive for moving in the downward direction.",
    "FractionDenominatorDisplayStyleShiftDown": "Standard shift down applied to the denominator in display style. Positive for moving in the downward direction. Suggested: same value as stackBottomDisplayStyleShiftDown.",
    "FractionNumeratorGapMin": "Minimum tolerated gap between the (ink) bottom of the numerator and the ink of the fraction bar. Suggested: default rule thickness.",
    "FractionNumDisplayStyleGapMin": "Minimum tolerated gap between the (ink) bottom of the numerator and the ink of the fraction bar in display style. Suggested: 3 × default rule thickness.",
    "FractionRuleThickness": "Thickness of the fraction bar. Suggested: default rule thickness.",
    "FractionDenominatorGapMin": "Minimum tolerated gap between the (ink) top of the denominator and the ink of the fraction bar. Suggested: default rule thickness.",
    "FractionDenomDisplayStyleGapMin": "Minimum tolerated gap between the (ink) top of the denominator and the ink of the fraction bar in display style. Suggested: 3 × default rule thickness.",
    "SkewedFractionHorizontalGap": "Horizontal distance between the top and bottom elements of a skewed fraction.",
    "SkewedFractionVerticalGap": "Vertical distance between the ink of the top and bottom elements of a skewed fraction.",
    "OverbarVerticalGap": "Distance between the overbar and the (ink) top of he base. Suggested: 3 × default rule thickness.",
    "OverbarRuleThickness": "Thickness of overbar. Suggested: default rule thickness.",
    "OverbarExtraAscender": "Extra white space reserved above the overbar. Suggested: default rule thickness.",
    "UnderbarVerticalGap": "Distance between underbar and (ink) bottom of the base. Suggested: 3 × default rule thickness.",
    "UnderbarRuleThickness": "Thickness of underbar. Suggested: default rule thickness.",
    "UnderbarExtraDescender": "Extra white space reserved below the underbar. Always positive. Suggested: default rule thickness.",
    "RadicalVerticalGap": "Space between the (ink) top of the expression and the bar over it. Suggested: 1¼ default rule thickness.",
    "RadicalDisplayStyleVerticalGap": "Space between the (ink) top of the expression and the bar over it. Suggested: default rule thickness + ¼ x-height.",
    "RadicalRuleThickness": "Thickness of the radical rule. This is the thickness of the rule in designed or constructed radical signs. Suggested: default rule thickness.",
    "RadicalExtraAscender": "Extra white space reserved above the radical. Suggested: same value as radicalRuleThickness.",
    "RadicalKernBeforeDegree": "Extra horizontal kern before the degree of a radical, if such is present. Suggested: 5/18 of em.",
    "RadicalKernAfterDegree": "Negative kern after the degree of a radical, if such is present. Suggested: −10/18 of em.",
    "RadicalDegreeBottomRaisePercent": "Height of the bottom of the radical degree, if such is present, in proportion to the ascender of the radical sign. Suggested: 60%.",
    "MinConnectorOverlap": "Minimum overlap of connecting glyphs during glyph construction, in design units.",
}

# Plain TeX accents, used to show to accent cloud
SAMPLE_MATH_ACCENTS = [
    "0300",  # \grave
    "0301",  # \acute
    "0302",  # \hat
    "0303",  # \tilde
    "0304",  # \bar
    "0306",  # \breve
    "0307",  # \dot
    "0308",  # \ddot
    "030C",  # \check
    "20D7",  # \vec
]


def _getMetrics(layer):
    size = layer.bounds.size
    return size.width, size.height


def _bboxWidth(layer):
    return layer.bounds.size.width


def _bboxHeight(layer):
    return layer.bounds.size.height


def _message(message):
    Message(message, NAME)


def __GSGlyphReference__str__(self):
    return self.glyph.name


GSGlyphReference.__str__ = objc.python_method(__GSGlyphReference__str__)


def __GSGlyphReference__eq__(self, other):
    return self.glyph.name == other.glyph.name


GSGlyphReference.__eq__ = objc.python_method(__GSGlyphReference__eq__)

pluginBundle = None
path = __file__[: __file__.rfind("Contents/Resources/")]
pluginBundle = AppKit.NSBundle.bundleWithPath_(path)

"""
    when you add more `NSLocalizedString()`, run this from the command line (with the Resources folder as current folder)
    genstrings -u -q -o en.lproj plugin.py

    (requires macOS and Xcode installed.)
    For now, it needs the `def NSLocalizedString()` be changed to something like `def NSLocalizedStringXX()` to not confuse genstrings

    then sync all the new keys with the localized files.
"""


def NSLocalizedString(string, comment):
    return pluginBundle.localizedStringForKey_value_table_(string, string, None)


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
            (10, 10, -10, -10),
            [NSLocalizedString("Vertical", ""), NSLocalizedString("Horizontal", "")],
        )

        self.emptyRow = {"g": "", "s": 0, "e": 0, "f": False}

        for i, tab in enumerate(window.tabs):
            vBox = vanilla.TextBox("auto", NSLocalizedString("Variants:", ""))
            vButton = vanilla.Button("auto", "🪄", callback=self.guessVariantsCallback)
            vButton.getNSButton().setTag_(i)
            setattr(self, f"vButton{i}", vButton)
            tab.vStack = vanilla.HorizontalStackView(
                "auto", [{"view": vBox}, {"view": vButton, "width": 24}]
            )

            tab.vEdit = vanilla.EditText(
                "auto", continuous=False, callback=self.editTextCallback
            )
            tab.vEdit.getNSTextField().setTag_(i)

            aBox = vanilla.TextBox("auto", NSLocalizedString("Assembly:", ""))
            aButton = vanilla.Button("auto", "🪄", callback=self.guessAssemblyCallback)
            aButton.getNSButton().setTag_(i)
            setattr(self, f"aButton{i}", aButton)
            tab.aStack = vanilla.HorizontalStackView(
                "auto", [{"view": aBox}, {"view": aButton, "width": 24}]
            )

            prev = vanilla.Button("auto", "⬅️", callback=self.prevCallback)
            next = vanilla.Button("auto", "➡️", callback=self.nextCallback)
            prev.bind("[", ["command"])
            next.bind("]", ["command"])
            setattr(self, f"prev{i}", prev)
            setattr(self, f"next{i}", next)
            tab.prevNext = vanilla.HorizontalStackView("auto", [prev, next])

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

            rules = [
                "V:|-[vStack]-[vEdit(40)]-[aStack]-[aList]-[check]-[prevNext]-|",
                f"H:|-[vStack({width})]-|",
                "H:|-[vEdit]-|",
                f"H:|-[aStack({width})]-|",
                "H:|-[aList]-|",
                "H:|-[check]-|",
                "H:|-[prevNext]-|",
            ]
            tab.addAutoPosSizeRules(rules)

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

        window.tabs = vanilla.Tabs((10, 10, -10, -10), tabs.keys())
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
                box.edit.getNSTextField().setTag_(MATH_CONSTANTS.index(c))
                box.edit.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])

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
                        "H:[label]-[edit(40)]-[button(24)]",
                        "V:|[button]|",
                    ]
                )
                constraints = []
                constraints.append(
                    box.label._nsObject.centerYAnchor().constraintEqualToAnchor_(
                        box.button._nsObject.centerYAnchor()
                    )
                )
                constraints.append(
                    box.edit._nsObject.centerYAnchor().constraintEqualToAnchor_(
                        box.button._nsObject.centerYAnchor()
                    )
                )
                constraint = box.label._nsObject.leadingAnchor().constraintGreaterThanOrEqualToAnchor_constant_(
                    box._nsObject.leadingAnchor(), 20
                )
                constraint.setPriority_(500)
                box.label._nsObject.setContentHuggingPriority_forOrientation_(
                    499, AppKit.NSLayoutConstraintOrientationHorizontal
                )
                constraints.append(constraint)
                constraints.append(
                    box.edit._nsObject.centerXAnchor().constraintEqualToAnchor_(
                        box._nsObject.centerXAnchor()
                    )
                )
                AppKit.NSLayoutConstraint.activateConstraints_(constraints)
                rules.append(f"H:|[{c}]|")
                setattr(tab, f"{c}", box)
            tab.addAutoPosSizeRules(rules)

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


def dashedLine(pt1, pt2, width):
    path = AppKit.NSBezierPath.bezierPath()
    path.setLineWidth_(width)
    path.setLineDash_count_phase_((width * 2, width * 2), 2, 0)
    path.moveToPoint_(pt1)
    path.lineToPoint_(pt2)
    path.stroke()


class MATHPlugin(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.name = NAME

    @objc.python_method
    def start(self):
        self.defaults = Glyphs.defaults

        Glyphs.addCallback(self.export_, DOCUMENTEXPORTED)
        Glyphs.addCallback(self.open_, DOCUMENTOPENED)
        Glyphs.addCallback(self.draw_, DRAWBACKGROUND)
        GSCallbackHandler.addCallback_forOperation_(self, "GSPrepareLayerCallback")

        menuItem = self.newMenuItem_(
            NSLocalizedString("Show MATH Italic Correction", ""), self.toggleShowIC_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Show MATH Top Accent Position", ""), self.toggleShowTA_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Show MATH Cut-ins", ""), self.toggleShowMK_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Show MATH Variants", ""), self.toggleShowGV_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Show MATH Assembly", ""), self.toggleShowGA_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Edit MATH Variants…", ""), self.editGlyph_, False
        )
        menuItem.setKeyEquivalentModifierMask_(
            AppKit.NSCommandKeyMask | AppKit.NSShiftKeyMask
        )
        menuItem.setKeyEquivalent_("x")
        Glyphs.menu[GLYPH_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            NSLocalizedString("Edit MATH Constants…", ""), self.editFont_, False
        )
        menuItem.setKeyEquivalentModifierMask_(
            AppKit.NSCommandKeyMask | AppKit.NSAlternateKeyMask
        )
        menuItem.setKeyEquivalent_("x")
        Glyphs.menu[EDIT_MENU].append(menuItem)

    @objc.python_method
    def __del__(self):
        Glyphs.removeCallback(self.export_)
        Glyphs.removeCallback(self.open_)
        Glyphs.removeCallback(self.draw_)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

    def notification_(self, message):
        Glyphs.showNotification(self.name, message)

    def validateMenuItem_(self, menuItem):
        if menuItem.identifier() == "editFont:":
            return Glyphs.font is not None
        return Glyphs.font is not None and Glyphs.font.selectedLayers

    @objc.python_method
    def newMenuItem_(self, title, action, setState=True):
        menuItem = AppKit.NSMenuItem.new()
        menuItem.setTitle_(title)
        menuItem.setAction_(action)
        menuItem.setTarget_(self)
        if setState:
            self.setMenuItemState_(menuItem)
        return menuItem

    @objc.python_method
    def setMenuItemState_(self, menuItem, state=None):
        key = f"{PLUGIN_ID}.{menuItem.identifier()}"
        if state is None:
            state = self.defaults.get(key, AppKit.NSOnState)
        self.defaults[key] = state
        menuItem.setState_(state)

    def toggleShowIC_(self, menuItem):
        newState = AppKit.NSOnState
        state = menuItem.state()
        if state == AppKit.NSOnState:
            newState = AppKit.NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowTA_(self, menuItem):
        newState = AppKit.NSOnState
        state = menuItem.state()
        if state == AppKit.NSOnState:
            newState = AppKit.NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowMK_(self, menuItem):
        newState = AppKit.NSOnState
        state = menuItem.state()
        if state == AppKit.NSOnState:
            newState = AppKit.NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowGV_(self, menuItem):
        newState = AppKit.NSOnState
        state = menuItem.state()
        if state == AppKit.NSOnState:
            newState = AppKit.NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowGA_(self, menuItem):
        newState = AppKit.NSOnState
        state = menuItem.state()
        if state == AppKit.NSOnState:
            newState = AppKit.NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def editFont_(self, menuItem):
        try:
            master = Glyphs.font.selectedFontMaster
            window = ConstantsWindow(master)
            window.open()
        except:
            _message(f"Editing failed:\n{traceback.format_exc()}")

    def editGlyph_(self, menuItem):
        try:
            layer = Glyphs.font.selectedLayers[0]
            window = VariantsWindow(layer)
            window.open()
        except:
            _message(f"Editing failed:\n{traceback.format_exc()}")

    @objc.python_method
    def draw_(self, layer, options):
        try:
            scale = 1 / options["Scale"]

            if self.defaults[f"{PLUGIN_ID}.toggleShowIC:"]:
                self.drawAnchors(layer, ITALIC_CORRECTION_ANCHOR, scale)
            if self.defaults[f"{PLUGIN_ID}.toggleShowTA:"]:
                self.drawAnchors(layer, TOP_ACCENT_ANCHOR, scale)

            if self.defaults[f"{PLUGIN_ID}.toggleShowMK:"]:
                self.drawMathKern(layer, scale)

            showGV = self.defaults[f"{PLUGIN_ID}.toggleShowGV:"]
            showGA = self.defaults[f"{PLUGIN_ID}.toggleShowGA:"]
            if showGV or showGA:
                layerData = layer.userData.get(VARIANTS_ID, {})
                glyphData = layer.parent.userData.get(VARIANTS_ID, {})
                if layerData or glyphData:
                    assembly = layerData.get(V_ASSEMBLY_ID, []) if showGA else []
                    variants = glyphData.get(V_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        self.drawVariants(variants, assembly, layer, scale, True)

                    assembly = layerData.get(H_ASSEMBLY_ID, []) if showGA else []
                    variants = glyphData.get(H_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        self.drawVariants(variants, assembly, layer, scale, False)
        except:
            _message(f"Drawing MATH data failed:\n{traceback.format_exc()}")

    @objc.python_method
    def drawAnchors(self, layer, name, width):
        save()
        master = layer.master
        if anchor := layer.anchors[name]:
            line = AppKit.NSBezierPath.bezierPath()
            line.moveToPoint_((anchor.position.x, master.descender))
            line.lineToPoint_((anchor.position.x, master.ascender))
            line.setLineWidth_(width)
            if anchor.name == ITALIC_CORRECTION_ANCHOR:
                AppKit.NSColor.blueColor().set()
            elif anchor.name == TOP_ACCENT_ANCHOR:
                AppKit.NSColor.magentaColor().set()
                if anchor.selected:
                    self.drawAccent(layer, anchor)
            line.stroke()
        restore()

    @staticmethod
    def drawAccent(layer, anchor):
        save()
        master = layer.master
        font = master.font

        constants = master.userData.get(CONSTANTS_ID, {})
        accentBase = constants.get("AccentBaseHeight", master.xHeight)

        height = layer.bounds.origin.y + layer.bounds.size.height
        dy = height - min(height, accentBase)

        AppKit.NSColor.colorWithDeviceWhite_alpha_(0, 0.2).set()
        for name in SAMPLE_MATH_ACCENTS:
            if glyph := font.glyphs[name]:
                aLayer = glyph.layers[master.id]
                aAnchor = aLayer.anchors[anchor.name]
                if aAnchor is None:
                    continue

                dx = anchor.position.x - aAnchor.position.x
                Transform = AppKit.NSAffineTransform.alloc().init()
                Transform.translateXBy_yBy_(dx, dy)

                path = aLayer.completeBezierPath
                path.transformUsingAffineTransform_(Transform)
                path.fill()
        restore()

    @staticmethod
    def drawMathKern(layer, width):
        save()
        bounds = layer.bounds
        master = layer.master
        for name in (
            KERN_TOP_RIGHT_ANCHOR,
            KERN_TOP_LEFT_ANCHOR,
            KERN_BOTTOM_RIGHT_ANCHOR,
            KERN_BOTTOM_LEFT_ANCHOR,
        ):
            points = []
            for anchor in layer.anchors:
                if anchor.name == name or anchor.name.startswith(name + "."):
                    points.append(anchor.position)
            points = sorted(points, key=lambda pt: pt.y)

            line = AppKit.NSBezierPath.bezierPath()
            line.setLineWidth_(width * 2)
            if name == KERN_TOP_RIGHT_ANCHOR:
                AppKit.NSColor.greenColor().set()
            elif name == KERN_TOP_LEFT_ANCHOR:
                AppKit.NSColor.blueColor().set()
            elif name == KERN_BOTTOM_RIGHT_ANCHOR:
                AppKit.NSColor.cyanColor().set()
            elif name == KERN_BOTTOM_LEFT_ANCHOR:
                AppKit.NSColor.redColor().set()
            for i, pt in enumerate(points):
                if i == 0:
                    y = min(bounds.origin.y, master.descender)
                    dashedLine((pt.x, y), pt, width * 2)
                    line.moveToPoint_(pt)
                if i < len(points) - 1:
                    line.lineToPoint_(pt)
                    line.lineToPoint_((points[i + 1].x, pt.y))
                else:
                    y = max(bounds.origin.y + bounds.size.height, master.ascender)
                    dashedLine((pt.x, points[i - 1].y), (pt.x, y), width * 2)
            line.stroke()
        restore()

    @staticmethod
    def drawVariants(variants, assembly, layer, width, vertical):
        save()
        font = layer.parent.parent

        def gl(obj):
            if isinstance(obj, GSGlyphReference):
                return obj.glyph
            return font.glyphs[obj]

        if vertical:
            AppKit.NSColor.greenColor().set()
        else:
            AppKit.NSColor.blueColor().set()

        x = layer.width
        y = 0
        for variant in variants:
            save()
            translate(x, y)
            variantLayer = gl(variant).layers[layer.layerId]
            path = variantLayer.completeBezierPath
            path.setLineWidth_(width)
            path.stroke()
            x += variantLayer.width
            restore()

        if not assembly:
            restore()
            return

        minOverlap = layer.master.userData.get(CONSTANTS_ID, {}).get(
            "MinConnectorOverlap", 0
        )

        # Draw assembly.

        # First at the maximum size (applying only MinConnectorOverlap)
        if vertical:
            # Vertically center the assembly
            h = sum(gl(a[0]).layers[layer.layerId].bounds.size.height for a in assembly)
            h -= (len(assembly) - 1) * minOverlap
            d = layer.bounds.size.height - h
            y = layer.bounds.origin.y + d / 2

        for gRef, _, _, _ in assembly:
            save()
            translate(x, y)
            partLayer = gl(gRef).layers[layer.layerId]
            path = partLayer.completeBezierPath
            path.setLineWidth_(width)
            path.stroke()

            w, h = _getMetrics(partLayer)
            if vertical:
                y += _bboxHeight(partLayer) - minOverlap
            else:
                x += _bboxWidth(partLayer) - minOverlap
            restore()

        # Then at the minimum size
        if vertical:
            # Vertically center the assembly
            x += partLayer.width
            h = 0
            prev = 0
            for gRef, _, start, end in assembly:
                overlap = max(min(start, prev), minOverlap)
                prev = end
                partLayer = gl(gRef).layers[layer.layerId]
                h += _bboxHeight(partLayer) - overlap
            d = layer.bounds.size.height - h
            y = layer.bounds.origin.y + d / 2
        else:
            x += minOverlap * 2

        prev = 0
        for gRef, _, start, end in assembly:
            save()
            overlap = max(min(start, prev), minOverlap)
            prev = end

            partLayer = gl(gRef).layers[layer.layerId]
            w, h = _getMetrics(partLayer)
            if vertical:
                y -= overlap
            else:
                x -= overlap

            translate(x, y)
            if vertical:
                y += h
            else:
                x += w

            path = partLayer.completeBezierPath
            path.setLineWidth_(width)
            path.stroke()
            restore()

        restore()

    @objc.python_method
    def open_(self, notification):
        """Load glyph names in GSGlyph.userData into GSGlyphReference so they
        track glyph renames."""
        try:
            doc = notification.object()
            font = doc.font

            try:
                ttFont = TTFont(
                    doc.filePath,
                    fontNumber=font.tempData.get("TTCFontIndex", 0),
                    lazy=True,
                    recalcBBoxes=False,
                )
            except Exception as ex:
                pass
            else:
                try:
                    self.importMathTable(font, ttFont)
                except Exception as ex:
                    raise ex
                finally:
                    ttFont.close()
                    # Mark font/all glyphs as unchanged
                    for glyph in font.glyphs:
                        glyph.undoManager().removeAllActions()
                        glyph.updateChangeCount_(AppKit.NSChangeCleared)
                    font.undoManager().removeAllActions()
                    font.parent.updateChangeCount_(AppKit.NSChangeCleared)

            def gn(n):
                if isinstance(n, GSGlyphReference):
                    return n
                return GSGlyphReference(font.glyphs[n])

            for glyph in font.glyphs:
                if varData := glyph.userData.get(VARIANTS_ID):
                    # We used to save the assemblies per-glyph, but we now store it per layer,
                    # so we migrate old data here.
                    layerData = {
                        k: v
                        for k, v in varData.items()
                        if k in (H_ASSEMBLY_ID, V_ASSEMBLY_ID)
                    }
                    if layerData:
                        for master in font.masters:
                            layer = glyph.layers[master.id]
                            layer.userData[VARIANTS_ID] = layerData
                        glyph.userData[VARIANTS_ID] = {
                            k: v
                            for k, v in varData.items()
                            if k in (H_VARIANTS_ID, V_VARIANTS_ID)
                        }

                # Convert glyph names in userData to GSGlyphReference
                varData = glyph.userData.get(VARIANTS_ID, {})
                for id in (V_VARIANTS_ID, H_VARIANTS_ID):
                    if names := varData.get(id):
                        varData[id] = [gn(n) for n in names]
                for layer in glyph.layers:
                    varData = layer.userData.get(VARIANTS_ID, {})
                    for id in (V_ASSEMBLY_ID, H_ASSEMBLY_ID):
                        if assembly := varData.get(id):
                            varData[id] = [(gn(a[0]), *a[1:]) for a in assembly]
            font.tempData[STATUS_ID] = True
        except AppKit.MPMissingGlyph as e:
            _message(f"Opening failed:\n{e}")
        except:
            _message(f"Opening failed:\n{traceback.format_exc()}")

    @staticmethod
    def importMathTable(font, ttFont):
        if "MATH" not in ttFont:
            return

        from fontTools.ttLib.tables import otTables

        master = font.masters[0]
        userData = master.userData

        table = ttFont["MATH"].table

        if table.Version != 0x00010000:
            return

        def get_glyph(gName):
            if gName in font.glyphs:
                return font.glyphs[gName]
            glyphOrder = ttFont.getGlyphOrder()
            if gName in glyphOrder:
                return font.glyphs[glyphOrder.index(gName)]
            return None

        constants = {}
        if table.MathConstants:
            for constant in MATH_CONSTANTS:
                if (value := getattr(table.MathConstants, constant, None)) is not None:
                    if isinstance(value, otTables.MathValueRecord):
                        value = value.Value
                    constants[constant] = value

        if info := table.MathGlyphInfo:
            if italic := info.MathItalicsCorrectionInfo:
                for name, value in zip(
                    italic.Coverage.glyphs, italic.ItalicsCorrection
                ):
                    layer = get_glyph(name).layers[master.id]
                    layer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                    layer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                        layer.width + value.Value,
                        0,
                    )

            if accent := info.MathTopAccentAttachment:
                for name, value in zip(
                    accent.TopAccentCoverage.glyphs, accent.TopAccentAttachment
                ):
                    layer = get_glyph(name).layers[master.id]
                    layer.anchors[TOP_ACCENT_ANCHOR] = GSAnchor()
                    layer.anchors[TOP_ACCENT_ANCHOR].position = (value.Value, 0)

            if extended := info.ExtendedShapeCoverage:
                for name in extended.glyphs:
                    get_glyph(name).userData[EXTENDED_SHAPE_ID] = True

            if kernInfo := info.MathKernInfo:
                for name, value in zip(
                    kernInfo.MathKernCoverage.glyphs, kernInfo.MathKernInfoRecords
                ):
                    layer = get_glyph(name).layers[master.id]

                    def _kern_to_xy(kern, top):
                        heights = [h.Value for h in kern.CorrectionHeight]
                        last = master.ascender
                        if heights and heights[-1] >= master.ascender:
                            last = heights[-1] + 100
                        elif not heights:
                            last = master.ascender if top else master.descender
                        heights.append(last)
                        values = [k.Value for k in kern.KernValue]
                        return zip(values, heights)

                    if kern := value.TopRightMathKern:
                        for i, (x, y) in enumerate(_kern_to_xy(kern, True)):
                            aName = f"{KERN_TOP_RIGHT_ANCHOR}.{i}"
                            layer.anchors[aName] = GSAnchor("", (x + layer.width, y))

                    if kern := value.BottomRightMathKern:
                        for i, (x, y) in enumerate(_kern_to_xy(kern, False)):
                            aName = f"{KERN_BOTTOM_RIGHT_ANCHOR}.{i}"
                            layer.anchors[aName] = GSAnchor("", (x + layer.width, y))

                    if kern := value.TopLeftMathKern:
                        for i, (x, y) in enumerate(_kern_to_xy(kern, True)):
                            aName = f"{KERN_TOP_LEFT_ANCHOR}.{i}"
                            layer.anchors[aName] = GSAnchor("", (-x, y))

                    if kern := value.BottomLeftMathKern:
                        for i, (x, y) in enumerate(_kern_to_xy(kern, False)):
                            aName = f"{KERN_BOTTOM_LEFT_ANCHOR}.{i}"
                            layer.anchors[aName] = GSAnchor("", (-x, y))

        if variants := table.MathVariants:
            constants["MinConnectorOverlap"] = variants.MinConnectorOverlap

            if vVariants := variants.VertGlyphCoverage:
                for name, value in zip(
                    vVariants.glyphs, variants.VertGlyphConstruction
                ):
                    glyph = get_glyph(name)
                    varData = glyph.userData.get(VARIANTS_ID, {})
                    if records := value.MathGlyphVariantRecord:
                        varData[V_VARIANTS_ID] = [
                            get_glyph(v.VariantGlyph).name for v in records
                        ]
                    glyph.userData[VARIANTS_ID] = dict(varData)

                    layer = glyph.layers[master.id]
                    if assembly := value.GlyphAssembly:
                        varData[V_ASSEMBLY_ID] = [
                            [
                                get_glyph(p.glyph).name,
                                p.PartFlags,
                                p.StartConnectorLength,
                                p.EndConnectorLength,
                            ]
                            for p in assembly.PartRecords
                        ]
                        if ic := assembly.ItalicsCorrection:
                            part = varData[V_ASSEMBLY_ID][-1]
                            partLayer = get_glyph(part[0]).layers[master.id]
                            partLayer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                            partLayer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                                partLayer.width + ic.Value,
                                0,
                            )
                    layer.userData[VARIANTS_ID] = dict(varData)

            if hVariants := variants.HorizGlyphCoverage:
                for name, value in zip(
                    hVariants.glyphs, variants.HorizGlyphConstruction
                ):
                    glyph = get_glyph(name)
                    varData = glyph.userData.get(VARIANTS_ID, {})
                    if records := value.MathGlyphVariantRecord:
                        varData[H_VARIANTS_ID] = [
                            get_glyph(v.VariantGlyph).name for v in records
                        ]
                    glyph.userData[VARIANTS_ID] = dict(varData)

                    layer = glyph.layers[master.id]
                    varData = layer.userData.get(VARIANTS_ID, {})
                    if assembly := value.GlyphAssembly:
                        varData[H_ASSEMBLY_ID] = [
                            [
                                get_glyph(p.glyph).name,
                                p.PartFlags,
                                p.StartConnectorLength,
                                p.EndConnectorLength,
                            ]
                            for p in assembly.PartRecords
                        ]
                        if ic := assembly.ItalicsCorrection:
                            part = varData[H_ASSEMBLY_ID][-1]
                            partLayer = get_glyph(part[0]).layers[master.id]
                            partLayer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                            partLayer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                                partLayer.width + ic.Value,
                                0,
                            )
                    layer.userData[VARIANTS_ID] = dict(varData)

        if constants:
            userData[CONSTANTS_ID] = constants

    @objc.python_method
    def export_(self, notification):
        try:
            info = notification.object()
            instance = info["instance"]
            path = info["fontFilePath"]

            if not instance.font.tempData[STATUS_ID]:
                _message(f"Export failed:\nloading math data failed")
                return

            font = instance.interpolatedFont

            with TTFont(path) as ttFont:
                self.buildMathTable(font, ttFont)
                if "MATH" in ttFont:
                    ttFont.save(path)
                    self.notification_("MATH table exported successfully")
        except:
            _message(f"Export failed:\n{traceback.format_exc()}")

    @staticmethod
    def buildMathTable(font, ttFont):
        instance = font.instances[0]
        master = font.masters[0]

        constants = dict(master.userData.get(CONSTANTS_ID, {}))
        min_connector_overlap = constants.pop("MinConnectorOverlap", 0)

        if (
            font.customParameters["Don't use Production Names"]
            or instance.customParameters["Don't use Production Names"]
        ):
            productionMap = {g.name: g.name for g in font.glyphs}
        else:
            productionMap = {g.name: g.productionName or g.name for g in font.glyphs}

        italic = {}
        accent = {}
        kerning = {}
        extended = set()
        kerning_sides = {
            KERN_TOP_RIGHT_ANCHOR: "TopRight",
            KERN_TOP_LEFT_ANCHOR: "TopLeft",
            KERN_BOTTOM_RIGHT_ANCHOR: "BottomRight",
            KERN_BOTTOM_LEFT_ANCHOR: "BottomLeft",
        }
        for glyph in font.glyphs:
            name = productionMap[glyph.name]
            layer = glyph.layers[0]
            kerns = {}
            for anchor in layer.anchors:
                if anchor.name == ITALIC_CORRECTION_ANCHOR:
                    italic[name] = anchor.position.x - layer.width
                elif anchor.name == TOP_ACCENT_ANCHOR:
                    accent[name] = anchor.position.x
                else:
                    for aName in kerning_sides.keys():
                        if anchor.name.startswith(aName):
                            side = kerning_sides[aName]
                            pt = anchor.position
                            if side.endswith("Right"):
                                pt.x -= layer.width
                            elif side.endswith("Left"):
                                pt.x = -pt.x
                            kerns.setdefault(side, []).append(pt)
            if kerns:
                kerning[name] = {}
                for side, pts in kerns.items():
                    pts = sorted(pts, key=lambda pt: pt.y)
                    correctionHeights = [pt.y for pt in pts[:-1]]
                    kernValues = [pt.x for pt in pts]
                    kerning[name][side] = (correctionHeights, kernValues)
            if glyph.userData[EXTENDED_SHAPE_ID]:
                extended.add(name)

        vVariants = {}
        hVariants = {}
        vAssemblies = {}
        hAssemblies = {}
        for glyph in font.glyphs:
            name = productionMap[glyph.name]
            varData = glyph.userData.get(VARIANTS_ID, {})
            if vVars := varData.get(V_VARIANTS_ID):
                vVars = [str(n) for n in vVars]
                vVariants[name] = [
                    (n, _bboxHeight(font.glyphs[n].layers[0])) for n in vVars
                ]
                if glyph.userData[EXTENDED_SHAPE_ID]:
                    extended.update(str(v) for v in vVars)
            if hVars := varData.get(H_VARIANTS_ID):
                hVars = [str(n) for n in hVars]
                hVariants[name] = [
                    (n, _bboxWidth(font.glyphs[n].layers[0])) for n in hVars
                ]

            layer = glyph.layers[master.id]
            varData = layer.userData.get(VARIANTS_ID, {})
            if vAssembly := varData.get(V_ASSEMBLY_ID):
                vAssemblies[name] = [
                    [
                        (str(part[0]), *part[1:], _bboxHeight(part[0].glyph.layers[0]))
                        for part in vAssembly
                    ],
                    italic.pop(str(vAssembly[-1][0]), 0),
                ]
            if hAssembly := varData.get(H_ASSEMBLY_ID):
                hAssemblies[name] = [
                    [
                        (str(part[0]), *part[1:], _bboxWidth(part[0].glyph.layers[0]))
                        for part in hAssembly
                    ],
                    italic.pop(str(hAssembly[-1][0]), 0),
                ]

        if not any(
            [
                constants,
                italic,
                accent,
                vVariants,
                hVariants,
                vAssemblies,
                hAssemblies,
                kerning,
                extended,
            ]
        ):
            return

        from fontTools.otlLib.builder import buildMathTable

        buildMathTable(
            ttFont,
            constants=constants,
            italicsCorrections=italic,
            topAccentAttachments=accent,
            extendedShapes=extended,
            mathKerns=kerning,
            minConnectorOverlap=min_connector_overlap,
            vertGlyphVariants=vVariants,
            horizGlyphVariants=hVariants,
            vertGlyphAssembly=vAssemblies,
            horizGlyphAssembly=hAssemblies,
        )

    @objc.typedSelector(b"c32@:@@@o^@")
    def interpolateLayer_glyph_interpolation_error_(
        self, layer, glyph, interpolation, error
    ):
        # Interpolate start and end connector lengths of assemblies
        if varData := layer.userData.get(VARIANTS_ID, {}):
            if hAssembly := varData.get(H_ASSEMBLY_ID):
                for i, _ in enumerate(hAssembly):
                    start = 0
                    end = 0
                    for masterId, factor in interpolation.items():
                        masterAssembly = (
                            glyph.layers[masterId]
                            .userData.get(VARIANTS_ID, {})
                            .get(H_ASSEMBLY_ID, [])
                        )
                        if i < len(masterAssembly):
                            start += masterAssembly[i][2] * factor
                            end += masterAssembly[i][3] * factor
                    hAssembly[i] = (hAssembly[i][0], hAssembly[i][1], start, end)
            if vAssembly := varData.get(V_ASSEMBLY_ID):
                for i, _ in enumerate(vAssembly):
                    start = 0
                    end = 0
                    for masterId, factor in interpolation.items():
                        masterAssembly = (
                            glyph.layers[masterId]
                            .userData.get(VARIANTS_ID, {})
                            .get(V_ASSEMBLY_ID, [])
                        )
                        if i < len(masterAssembly):
                            start += masterAssembly[i][2] * factor
                            end += masterAssembly[i][3] * factor
                    vAssembly[i] = (vAssembly[i][0], vAssembly[i][1], start, end)
        return (True, None)

    @objc.typedSelector(b"c32@:@@@o^@")
    def interpolateMaster_font_interpolation_error_(
        self, master, font, interpolation, error
    ):
        # Interpolate math constants
        constants = {}
        for c in MATH_CONSTANTS:
            value = 0
            for masterId, factor in interpolation.items():
                userData = font.masters[masterId].userData.get(CONSTANTS_ID, {})
                if v := userData.get(c):
                    value += v * factor
            constants[c] = round(value)
        master.userData[CONSTANTS_ID] = dict(constants)

        return (True, None)
