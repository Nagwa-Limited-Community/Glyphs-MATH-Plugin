# Copyright 2021 Nagwa Limited

import traceback

import objc
import vanilla
import AppKit

from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
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

KERN_TOP_RIHGT_ANCHOR = "math.tr"
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
    width = layer.width
    height = layer.vertWidth
    if height is None:
        height = layer.bounds.size.height
    return (width, height)


def _valueRecord(v):
    vr = otTables.MathValueRecord()
    vr.Value = int(v)
    return vr


def _message(message):
    Message(message, NAME)


def __GSGlyphReference__str__(self):
    return self.glyph.name


GSGlyphReference.__str__ = objc.python_method(__GSGlyphReference__str__)


def __GSGlyphReference__eq__(self, other):
    return self.glyph.name == other.glyph.name


GSGlyphReference.__eq__ = objc.python_method(__GSGlyphReference__eq__)


class VariantsWindow:
    def __init__(self, glyph):
        self._glyph = glyph
        width, height = 650, 400
        self._window = window = vanilla.Window(
            (width, height),
            f"MATH Variants for ‘{self._glyph.name}’ from {glyph.parent.familyName}",
        )
        window.tabs = vanilla.Tabs((10, 10, -10, -10), ["Vertical", "Horizontal"])

        self._emptyRow = {"g": "", "s": 0, "e": 0, "f": False}

        for i, tab in enumerate(window.tabs):
            vbox = vanilla.TextBox("auto", "Variants:")
            vbutton = vanilla.Button("auto", "🪄", callback=self._guessVariantsCallback)
            vbutton.getNSButton().setTag_(i)
            setattr(self, f"vbutton{i}", vbutton)
            tab.vstack = vanilla.HorizontalStackView(
                "auto", [{"view": vbox}, {"view": vbutton, "width": 24}]
            )

            tab.vedit = vanilla.EditText(
                "auto", continuous=False, callback=self._editTextCallback
            )
            tab.vedit.getNSTextField().setTag_(i)

            abox = vanilla.TextBox("auto", "Assembly:")
            abutton = vanilla.Button("auto", "🪄", callback=self._guessAssemblyCallback)
            abutton.getNSButton().setTag_(i)
            setattr(self, f"abutton{i}", abutton)
            tab.astack = vanilla.HorizontalStackView(
                "auto", [{"view": abox}, {"view": abutton, "width": 24}]
            )

            prev = vanilla.Button("auto", "⬅️", callback=self._prevCallback)
            next = vanilla.Button("auto", "➡️", callback=self._nextCallback)
            prev.bind("[", ["command"])
            next.bind("]", ["command"])
            setattr(self, f"prev{i}", prev)
            setattr(self, f"next{i}", next)
            tab.prevnext = vanilla.HorizontalStackView("auto", [prev, next])

            tab.alist = vanilla.List(
                "auto",
                [],
                columnDescriptions=[
                    {"key": "g", "title": "Glyph"},
                    {
                        "key": "s",
                        "title": "Start Connector",
                    },
                    {
                        "key": "e",
                        "title": "End Connector",
                    },
                    {
                        "key": "f",
                        "title": "Extender",
                        "cell": vanilla.CheckBoxListCell(),
                    },
                ],
                allowsSorting=False,
                drawVerticalLines=True,
                enableDelete=True,
                editCallback=self._listEditCallback,
                doubleClickCallback=self._listDoubleClickCallback,
            )
            tab.alist.getNSTableView().setTag_(i)

            tab.check = vanilla.CheckBox(
                "auto", "Extended shape", callback=self._checkBoxCallback
            )
            tab.check.show(i == 0)

            rules = [
                "V:|-[vstack]-[vedit(40)]-[astack]-[alist]-[check]-[prevnext]-|",
                f"H:|-[vstack({width})]-|",
                "H:|-[vedit]-|",
                f"H:|-[astack({width})]-|",
                "H:|-[alist]-|",
                "H:|-[check]-|",
                "H:|-[prevnext]-|",
            ]
            tab.addAutoPosSizeRules(rules)

        if varData := glyph.userData[VARIANTS_ID]:
            if vvars := varData.get(V_VARIANTS_ID):
                window.tabs[0].vedit.set(" ".join(str(v) for v in vvars))
            if hvars := varData.get(H_VARIANTS_ID):
                window.tabs[1].vedit.set(" ".join(str(v) for v in hvars))
            if vassembly := varData.get(V_ASSEMBLY_ID):
                items = []
                for part in vassembly:
                    part = list(part)
                    part[0] = str(part[0])
                    part[1] = bool(part[1])
                    items.append(dict(zip(("g", "f", "s", "e"), part)))
                window.tabs[0].alist.set(items)
            if hassembly := varData.get(H_ASSEMBLY_ID):
                items = []
                for part in hassembly:
                    part = list(part)
                    part[0] = str(part[0])
                    part[1] = bool(part[1])
                    items.append(dict(zip(("g", "f", "s", "e"), part)))
                window.tabs[1].alist.set(items)
        if exended := glyph.userData[EXTENDED_SHAPE_ID]:
            window.tabs[0].check.set(bool(exended))

    def open(self):
        self._window.open()

    def _glyphRef(self, name):
        try:
            return GSGlyphReference(self._glyph.parent.glyphs[name])
        except:
            _message(traceback.format_exc())

    def _open(self, glyph):
        posSize = self._window.getPosSize()
        selected = self._window.tabs.get()
        self._window.close()
        window = VariantsWindow(glyph)
        window._window.setPosSize(posSize)
        window._window.tabs.set(selected)
        window.open()

    def _nextCallback(self, sender):
        try:
            font = self._glyph.parent
            glyphOrder = [g.name for g in font.glyphs]
            index = glyphOrder.index(self._glyph.name)
            if index < len(glyphOrder) - 1:
                self._open(font.glyphs[index + 1])
        except:
            _message(traceback.format_exc())

    def _prevCallback(self, sender):
        try:
            font = self._glyph.parent
            glyphOrder = [g.name for g in font.glyphs]
            index = glyphOrder.index(self._glyph.name)
            if index > 0:
                self._open(font.glyphs[index - 1])
        except:
            _message(traceback.format_exc())

    def _guessVariantsCallback(self, sender):
        try:
            tag = sender.getNSButton().tag()
            glyph = self._glyph
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
                if variants := [a for a in alternates if a.startswith(prefix)]:
                    tab = self._window.tabs[tag]
                    tab.vedit.set(" ".join([name] + variants))
                    self._editTextCallback(tab.vedit)
                    return
        except:
            _message(traceback.format_exc())

    def _guessAssemblyCallback(self, sender):
        pass

    def _editTextCallback(self, sender):
        try:
            new = sender.get().strip()
            if not new:
                return

            glyph = self._glyph
            tag = sender.getNSTextField().tag()
            varData = glyph.userData.get(VARIANTS_ID, {})
            if var := varData.get(H_VARIANTS_ID if tag else V_VARIANTS_ID):
                if " ".join(str(v) for v in var) == new:
                    return

            varData = {k: list(v) for k, v in varData.items()}
            var = [self._glyphRef(n) for n in new.split()]
            varData[H_VARIANTS_ID if tag else V_VARIANTS_ID] = var
            glyph.userData[VARIANTS_ID] = dict(varData)
        except:
            _message(traceback.format_exc())

    def _listEditCallback(self, sender):
        try:
            new = [
                (
                    self._glyphRef(item["g"]),
                    int(item["f"]),
                    int(item["s"]),
                    int(item["e"]),
                )
                for item in sender.get()
                if item != self._emptyRow
            ]
            if not new:
                return

            glyph = self._glyph
            tag = sender.getNSTableView().tag()
            varData = glyph.userData[VARIANTS_ID]
            if not varData:
                varData = {}
            if varData.get(H_ASSEMBLY_ID if tag else V_ASSEMBLY_ID) == new:
                return
            varData = {k: list(v) for k, v in varData.items()}
            varData[H_ASSEMBLY_ID if tag else V_ASSEMBLY_ID] = new
            glyph.userData[VARIANTS_ID] = dict(varData)
        except:
            _message(traceback.format_exc())

    def _listDoubleClickCallback(self, sender):
        try:
            table = sender.getNSTableView()
            column = table.clickedColumn()
            row = table.clickedRow()
            if row < 0 and column < 0:
                items = sender.get()
                items.append(self._emptyRow)
                sender.set(items)
                row = len(items) - 1
            table._startEditingColumn_row_event_(column, row, None)
        except:
            _message(traceback.format_exc())

    def _checkBoxCallback(self, sender):
        try:
            glyph = self._glyph
            glyph.userData[EXTENDED_SHAPE_ID] = sender.get()
            if not sender.get():
                del glyph.userData[EXTENDED_SHAPE_ID]
        except:
            _message(traceback.format_exc())


class ConstantsWindow:
    def __init__(self, master):
        self._master = master
        if CONSTANTS_ID not in master.userData:
            constants = {}
        else:
            constants = dict(master.userData[CONSTANTS_ID])
        self._constants = constants

        width, height = 650, 400
        self._window = window = vanilla.Window(
            (width, height),
            f"MATH Constants for master ‘{master.name}’ from {master.font.familyName}",
        )
        tabs = {
            "General": MATH_CONSTANTS_GENERAL,
            "Sub/Superscript": MATH_CONSTANTS_SCRIPTS,
            "Limits": MATH_CONSTANTS_LIMITS,
            "Stacks": MATH_CONSTANTS_STACKS,
            "Fractions": MATH_CONSTANTS_FRACTIONS,
            "Over/Underbar": MATH_CONSTANTS_BARS,
            "Radicals": MATH_CONSTANTS_RADICALS,
        }

        uformatter = AppKit.NSNumberFormatter.new()
        uformatter.setAllowsFloats_(False)
        uformatter.setMinimum_(0)
        uformatter.setMaximum_(0xFFFF)

        sformatter = AppKit.NSNumberFormatter.new()
        sformatter.setAllowsFloats_(False)
        sformatter.setMinimum_(-0x7FFF)
        sformatter.setMaximum_(0x7FFF)

        window.tabs = vanilla.Tabs((10, 10, -10, -10), tabs.keys())
        for i, name in enumerate(tabs.keys()):
            tab = window.tabs[i]
            rules = ["V:|" + "".join(f"[{c}]" for c in tabs[name]) + "|"]
            for c in tabs[name]:
                box = vanilla.Box("auto", borderWidth=0)
                box.box = vanilla.TextBox("auto", c, alignment="right")
                box.box.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])

                box.edit = vanilla.EditText(
                    "auto",
                    constants.get(c, None),
                    callback=self._callback,
                    formatter=uformatter if c in CONSTANT_UNSIGNED else sformatter,
                    placeholder="0",
                )
                box.edit.getNSTextField().setTag_(MATH_CONSTANTS.index(c))
                box.edit.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])

                box.button = vanilla.Button(
                    "auto",
                    "🪄",
                    callback=self._guessCallback,
                )
                box.button.getNSButton().setToolTip_("Guess value")
                box.button.getNSButton().setTag_(MATH_CONSTANTS.index(c))

                box.addAutoPosSizeRules(
                    [
                        f"H:|[box({width/2})]-[edit(40)]-[button(24)]-{width/2-64}-|",
                        "V:|[box]|",
                        "V:|[edit(24)]|",
                        "V:|[button(24)]|",
                    ]
                )
                rules.append(f"H:|[{c}]|")
                setattr(tab, f"{c}", box)
            tab.addAutoPosSizeRules(rules)

    def open(self):
        self._window.open()

    def _getConstant(self, constant, force=False):
        master = self._master
        font = master.font

        if not force and constant in self._constants:
            return self._constants[constant]

        value = None
        if constant == "ScriptPercentScaleDown":
            value = 80
        elif constant == "ScriptScriptPercentScaleDown":
            value = 60
        elif constant == "DelimitedSubFormulaMinHeight":
            value = (master.ascender - master.descender) * 1.5
        elif constant == "DisplayOperatorMinHeight":
            # display "summation" height
            if (glyph := font.glyphs["∑"]) is not None:
                if varData := glyph.userData[VARIANTS_ID]:
                    if vvars := varData.get(V_VARIANTS_ID):
                        value = vvars[1].glyph.layers[master.id].bounds.size.height
        elif constant == "MathLeading":
            if (value := master.customParameters["typoLineGap"]) is None:
                value = master.customParameters["hheaLineGap"]
        elif constant == "AxisHeight":
            # "minus" midline
            if (glyph := font.glyphs["−"]) is not None:
                bounds = glyph.layers[master.id].bounds
                value = bounds.origin.y + bounds.size.height / 2
        elif constant == "AccentBaseHeight":
            value = master.xHeight
        elif constant == "FlattenedAccentBaseHeight":
            value = master.capHeight
        elif constant == "SubscriptShiftDown":
            value = master.customParameters["subscriptYOffset"]
        elif constant == "SubscriptTopMax":
            value = master.xHeight * 4 / 5
        elif constant == "SubscriptBaselineDropMin":
            if (value := self._getConstant("SubscriptShiftDown")) is not None:
                value *= 3 / 4
        elif constant == "SuperscriptShiftUp":
            value = master.customParameters["superscriptYOffset"]
        elif constant == "SuperscriptShiftUpCramped":
            if (value := self._getConstant("SuperscriptShiftUp")) is not None:
                value *= 3 / 4
        elif constant == "SuperscriptBottomMin":
            value = master.xHeight / 4
        elif constant == "SuperscriptBaselineDropMax":
            if (v := self._getConstant("SuperscriptShiftUp")) is not None:
                value = master.capHeight - v
        elif constant == "SubSuperscriptGapMin":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 4
        elif constant == "SuperscriptBottomMaxWithSubscript":
            value = master.xHeight * 4 / 5
        elif constant == "SpaceAfterScript":
            value = font.upm / 24
        elif constant == "UpperLimitGapMin":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 2
        elif constant == "UpperLimitBaselineRiseMin":
            value = -master.descender * 3 / 4
        elif constant == "LowerLimitGapMin":
            value = self._getConstant("UpperLimitGapMin")
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
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 3
        elif constant == "StackDisplayStyleGapMin":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 7
        elif constant == "StretchStackTopShiftUp":
            value = self._getConstant("UpperLimitBaselineRiseMin")
        elif constant == "StretchStackBottomShiftDown":
            value = self._getConstant("LowerLimitBaselineDropMin")
        elif constant == "StretchStackGapAboveMin":
            value = self._getConstant("UpperLimitGapMin")
        elif constant == "StretchStackGapBelowMin":
            value = self._getConstant("LowerLimitGapMin")
        elif constant == "FractionNumeratorShiftUp":
            value = self._getConstant("StackTopShiftUp")
        elif constant == "FractionNumeratorDisplayStyleShiftUp":
            value = self._getConstant("StackTopDisplayStyleShiftUp")
        elif constant == "FractionDenominatorShiftDown":
            value = self._getConstant("StackBottomShiftDown")
        elif constant == "FractionDenominatorDisplayStyleShiftDown":
            value = self._getConstant("StackBottomDisplayStyleShiftDown")
        elif constant == "FractionNumeratorGapMin":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "FractionNumDisplayStyleGapMin":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 3
        elif constant == "FractionRuleThickness":
            # "radical" top connecting part
            if (glyph := master.font.glyphs["√"]) is not None:
                layer = glyph.layers[master.id]
                paths = layer.paths
                if len(paths):
                    segments = list(
                        reversed(
                            sorted(paths[0].segments, key=lambda s: s.bounds.origin.x)
                        )
                    )
                    value = segments[0].bounds.size.height
        elif constant == "FractionDenominatorGapMin":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "FractionDenomDisplayStyleGapMin":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 3
        elif constant == "SkewedFractionHorizontalGap":
            # TODO
            pass
        elif constant == "SkewedFractionVerticalGap":
            # TODO
            pass
        elif constant == "OverbarVerticalGap":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 3
        elif constant == "OverbarRuleThickness":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "OverbarExtraAscender":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "UnderbarVerticalGap":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 3
        elif constant == "UnderbarRuleThickness":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "UnderbarExtraDescender":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "RadicalVerticalGap":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule * 5 / 4
        elif constant == "RadicalDisplayStyleVerticalGap":
            if (rule := self._getConstant("FractionRuleThickness")) is not None:
                value = rule + master.xHeight / 4
        elif constant == "RadicalRuleThickness":
            value = self._getConstant("FractionRuleThickness")
        elif constant == "RadicalExtraAscender":
            if (value := self._getConstant("RadicalRuleThickness")) is None:
                value = self._getConstant("FractionRuleThickness")
        elif constant == "RadicalKernBeforeDegree":
            value = font.upm * 5 / 18
        elif constant == "RadicalKernAfterDegree":
            value = -font.upm * 10 / 18
        elif constant == "RadicalDegreeBottomRaisePercent":
            value = 60
        elif constant == "MinConnectorOverlap":
            # TODO
            pass

        return value

    def _guessCallback(self, sender):
        constant = MATH_CONSTANTS[sender.getNSButton().tag()]
        if (value := self._getConstant(constant, force=True)) is not None:
            for tab in self._window.tabs:
                box = getattr(tab, constant, None)
                if box is not None:
                    box.edit.set(value)
                    self._callback(box.edit)

    def _callback(self, sender):
        constants = self._constants
        value = sender.get()
        value = value if value is None else int(value)
        tag = sender.getNSTextField().tag()

        constant = MATH_CONSTANTS[tag]
        if constants.get(constant) == value:
            return

        if value is not None:
            constants[constant] = value
        elif constant in constants:
            del constants[constant]

        if constants:
            self._master.userData[CONSTANTS_ID] = constants
        elif CONSTANTS_ID in self._master.userData:
            del self._master.userData[CONSTANTS_ID]


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

        menuItem = self.newMenuItem_("Show MATH Italic Correction", self.toggleShowIC_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_(
            "Show MATH Top Accent Position", self.toggleShowTA_
        )
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Show MATH Cut-ins", self.toggleShowMK_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Show MATH Variants", self.toggleShowGV_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Show MATH Assembly", self.toggleShowGA_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Edit MATH Variants...", self.editGlyph_, False)
        menuItem.setKeyEquivalentModifierMask_(
            AppKit.NSCommandKeyMask | AppKit.NSShiftKeyMask
        )
        menuItem.setKeyEquivalent_("x")
        Glyphs.menu[GLYPH_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Edit MATH Constants...", self.editFont_, False)
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
            glyph = Glyphs.font.selectedLayers[0].parent
            window = VariantsWindow(glyph)
            window.open()
        except:
            _message(f"Editing failed:\n{traceback.format_exc()}")

    @objc.python_method
    def draw_(self, layer, options):
        try:
            scale = 1 / options["Scale"]

            if self.defaults[f"{PLUGIN_ID}.toggleShowIC:"]:
                self._drawAnchors(layer, ITALIC_CORRECTION_ANCHOR, scale)
            if self.defaults[f"{PLUGIN_ID}.toggleShowTA:"]:
                self._drawAnchors(layer, TOP_ACCENT_ANCHOR, scale)

            if self.defaults[f"{PLUGIN_ID}.toggleShowMK:"]:
                self._drawMathkern(layer, scale)

            showGV = self.defaults[f"{PLUGIN_ID}.toggleShowGV:"]
            showGA = self.defaults[f"{PLUGIN_ID}.toggleShowGA:"]
            if showGV or showGA:
                if userData := layer.parent.userData[VARIANTS_ID]:
                    assembly = userData.get(V_ASSEMBLY_ID, []) if showGA else []
                    variants = userData.get(V_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        self._drawVariants(variants, assembly, layer, scale, True)

                    assembly = userData.get(H_ASSEMBLY_ID, []) if showGA else []
                    variants = userData.get(H_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        self._drawVariants(variants, assembly, layer, scale, False)
        except:
            _message(f"Drawing MATH data failed:\n{traceback.format_exc()}")

    @objc.python_method
    def _drawAnchors(self, layer, name, width):
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
                    self._drawAccent(layer, anchor)
            line.stroke()
        restore()

    @staticmethod
    def _drawAccent(layer, anchor):
        save()
        master = layer.master
        font = master.font

        constants = master.userData.get(CONSTANTS_ID, {})
        accentBase = constants.get("AccentBaseHeight", master.xHeight)

        height = layer.bounds.size.height
        dy = height - min(height, accentBase)

        AppKit.NSColor.colorWithDeviceWhite_alpha_(0, 0.2).set()
        for name in SAMPLE_MATH_ACCENTS:
            if glyph := font.glyphs[name]:
                alayer = glyph.layers[master.id]
                aanchor = alayer.anchors[anchor.name]
                if aanchor is None:
                    continue

                dx = anchor.position.x - aanchor.position.x
                Transform = AppKit.NSAffineTransform.alloc().init()
                Transform.translateXBy_yBy_(dx, dy)

                path = alayer.completeBezierPath
                path.transformUsingAffineTransform_(Transform)
                path.fill()
        restore()

    @staticmethod
    def _drawMathkern(layer, width):
        save()
        master = layer.master
        constants = master.userData.get(CONSTANTS_ID, {})
        for name in (
            KERN_TOP_RIHGT_ANCHOR,
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
            if name == KERN_TOP_RIHGT_ANCHOR:
                AppKit.NSColor.greenColor().set()
            elif name == KERN_TOP_LEFT_ANCHOR:
                AppKit.NSColor.blueColor().set()
            elif name == KERN_BOTTOM_RIGHT_ANCHOR:
                AppKit.NSColor.cyanColor().set()
            elif name == KERN_BOTTOM_LEFT_ANCHOR:
                AppKit.NSColor.redColor().set()
            for i, pt in enumerate(points):
                if i == 0:
                    y = master.descender
                    if name in (KERN_TOP_RIHGT_ANCHOR, KERN_TOP_LEFT_ANCHOR):
                        y = constants.get("SuperscriptBottomMin", 0)
                    line.moveToPoint_((pt.x, min(pt.y, y)))
                line.lineToPoint_((pt.x, pt.y))
                if i < len(points) - 1:
                    line.lineToPoint_((points[i + 1].x, pt.y))
                else:
                    y = 0
                    if name in (KERN_TOP_RIHGT_ANCHOR, KERN_TOP_LEFT_ANCHOR):
                        y = constants.get(
                            "SuperscriptBottomMaxWithSubscript", master.ascender
                        )
                    line.lineToPoint_((pt.x, max(pt.y, y)))
            line.stroke()
        restore()

    @staticmethod
    def _drawVariants(variants, assembly, layer, width, vertical):
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
        translate(layer.width, layer.bounds.origin.y)

        for variant in variants:
            glyph = gl(variant)
            variant_layer = glyph.layers[layer.layerId]
            translate(variant_layer.bounds.origin.x, 0)
            path = variant_layer.completeBezierPath
            path.setLineWidth_(width)
            path.stroke()
            translate(variant_layer.width, 0)

        minoverlap = layer.master.userData.get(CONSTANTS_ID, {}).get(
            "MinConnectorOverlap", 0
        )
        if vertical:
            translate(0, minoverlap)
        else:
            translate(minoverlap, 0)
        for gref, flag, bot, top in assembly:
            if vertical:
                translate(0, -minoverlap)
            else:
                translate(-minoverlap, 0)
            glyph = gl(gref)
            gref_layer = glyph.layers[layer.layerId]
            w, h = _getMetrics(gref_layer)
            if vertical:
                translate(0, -gref_layer.bounds.origin.y)
            else:
                translate(-gref_layer.bounds.origin.x, 0)
            path = gref_layer.completeBezierPath
            path.setLineWidth_(width)
            path.stroke()
            if vertical:
                translate(0, h)
            else:
                translate(w, 0)

        restore()

    @objc.python_method
    def open_(self, notification):
        """Load glyph names in GSGlyph.userData into GSGlyphReference so they
        track glyph renames."""
        try:
            doc = notification.object()
            font = doc.font

            try:
                ttFont = TTFont(doc.filePath)
            except Exception:
                pass
            else:
                try:
                    self._import(font, ttFont)
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
                return GSGlyphReference(font.glyphs[n])

            for glyph in font.glyphs:
                varData = glyph.userData.get(VARIANTS_ID, {})
                for id in (V_VARIANTS_ID, H_VARIANTS_ID):
                    if names := varData.get(id):
                        varData[id] = [gn(n) for n in names]
                for id in (V_ASSEMBLY_ID, H_ASSEMBLY_ID):
                    if assembly := varData.get(id):
                        varData[id] = [(gn(a[0]), *a[1:]) for a in assembly]
            font.tempData[STATUS_ID] = True
        except AppKit.MPMissingGlyph as e:
            _message(f"Opening failed:\n{e}")
        except:
            _message(f"Opening failed:\n{traceback.format_exc()}")

    @staticmethod
    def _import(font, ttFont):
        if "MATH" not in ttFont:
            return

        master = font.masters[0]
        userData = master.userData

        table = ttFont["MATH"].table

        if table.Version != 0x00010000:
            return

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
                    layer = font.glyphs[name].layers[master.id]
                    layer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                    layer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                        layer.width + value.Value,
                        0,
                    )

            if accent := info.MathTopAccentAttachment:
                for name, value in zip(
                    accent.TopAccentCoverage.glyphs, accent.TopAccentAttachment
                ):
                    layer = font.glyphs[name].layers[master.id]
                    layer.anchors[TOP_ACCENT_ANCHOR] = GSAnchor()
                    layer.anchors[TOP_ACCENT_ANCHOR].position = (value.Value, 0)

            if extended := info.ExtendedShapeCoverage:
                for name in extended.glyphs:
                    font.glyphs[name].userData[EXTENDED_SHAPE_ID] = True

            if kerninfo := info.MathKernInfo:
                for name, value in zip(
                    kerninfo.MathKernCoverage.glyphs, kerninfo.MathKernInfoRecords
                ):
                    layer = font.glyphs[name].layers[master.id]

                    if kern := value.TopRightMathKern:
                        heights = kern.CorrectionHeight + [
                            table.MathConstants.SuperscriptBottomMaxWithSubscript
                        ]
                        for i, (x, y) in enumerate(zip(kern.KernValue, heights)):
                            aname = f"{KERN_TOP_RIHGT_ANCHOR}.{i}"
                            layer.anchors[aname] = GSAnchor()
                            layer.anchors[aname].position = (
                                x.Value + layer.width,
                                y.Value,
                            )
                    if kern := value.BottomRightMathKern:
                        heights = [_valueRecord(0)] + kern.CorrectionHeight
                        for i, (x, y) in enumerate(zip(kern.KernValue, heights)):
                            aname = f"{KERN_BOTTOM_RIGHT_ANCHOR}.{i}"
                            layer.anchors[aname] = GSAnchor()
                            layer.anchors[aname].position = (
                                x.Value + layer.width,
                                y.Value,
                            )

                    if kern := value.TopLeftMathKern:
                        heights = kern.CorrectionHeight + [
                            table.MathConstants.SuperscriptBottomMaxWithSubscript
                        ]
                        for i, (x, y) in enumerate(zip(kern.KernValue, heights)):
                            aname = f"{KERN_TOP_LEFT_ANCHOR}.{i}"
                            layer.anchors[aname] = GSAnchor()
                            layer.anchors[aname].position = (-x.Value, y.Value)

                    if kern := value.BottomLeftMathKern:
                        heights = [_valueRecord(0)] + kern.CorrectionHeight
                        for i, (x, y) in enumerate(zip(kern.KernValue, heights)):
                            aname = f"{KERN_BOTTOM_LEFT_ANCHOR}.{i}"
                            layer.anchors[aname] = GSAnchor()
                            layer.anchors[aname].position = (-x.Value, y.Value)

        if variants := table.MathVariants:
            constants["MinConnectorOverlap"] = variants.MinConnectorOverlap

            if vvariants := variants.VertGlyphCoverage:
                for name, value in zip(
                    vvariants.glyphs, variants.VertGlyphConstruction
                ):
                    glyph = font.glyphs[name]
                    varData = glyph.userData.get(VARIANTS_ID, {})
                    if records := value.MathGlyphVariantRecord:
                        varData[V_VARIANTS_ID] = [v.VariantGlyph for v in records]
                    if assembly := value.GlyphAssembly:
                        varData[V_ASSEMBLY_ID] = [
                            [
                                p.glyph,
                                p.PartFlags,
                                p.StartConnectorLength,
                                p.EndConnectorLength,
                            ]
                            for p in assembly.PartRecords
                        ]
                        if ic := assembly.ItalicsCorrection:
                            part = varData[V_ASSEMBLY_ID][-1]
                            layer = font.glyphs[part[0]].layers[master.id]
                            layer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                            layer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                                layer.width + ic.Value,
                                0,
                            )
                    glyph.userData[VARIANTS_ID] = dict(varData)
            if hvariants := variants.HorizGlyphCoverage:
                for name, value in zip(
                    hvariants.glyphs, variants.HorizGlyphConstruction
                ):
                    glyph = font.glyphs[name]
                    varData = glyph.userData.get(VARIANTS_ID, {})
                    if records := value.MathGlyphVariantRecord:
                        varData[H_VARIANTS_ID] = [v.VariantGlyph for v in records]
                    if assembly := value.GlyphAssembly:
                        varData[H_ASSEMBLY_ID] = [
                            [
                                p.glyph,
                                p.PartFlags,
                                p.StartConnectorLength,
                                p.EndConnectorLength,
                            ]
                            for p in assembly.PartRecords
                        ]
                        if ic := assembly.ItalicsCorrection:
                            part = varData[H_ASSEMBLY_ID][-1]
                            layer = font.glyphs[part[0]].layers[master.id]
                            layer.anchors[ITALIC_CORRECTION_ANCHOR] = GSAnchor()
                            layer.anchors[ITALIC_CORRECTION_ANCHOR].position = (
                                layer.width + ic.Value,
                                0,
                            )
                    glyph.userData[VARIANTS_ID] = dict(varData)

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
                self._build(font, ttFont)
                if "MATH" in ttFont:
                    ttFont.save(path)
                    self.notification_("MATH table exported successfully")
        except:
            _message(f"Export failed:\n{traceback.format_exc()}")

    @staticmethod
    def _build(font, ttFont):
        instance = font.instances[0]
        master = font.masters[0]
        userData = master.userData.get(CONSTANTS_ID, {})

        constants = {}
        found = False
        if userData:
            for c in MATH_CONSTANTS:
                # MinConnectorOverlap is used in MathVariants table below.
                if c == "MinConnectorOverlap":
                    continue
                v = userData.get(c, None)
                if v is None:
                    v = 0
                else:
                    found = True
                v = int(v)
                if c in CONSTANT_INTEGERS:
                    constants[c] = v
                else:
                    constants[c] = _valueRecord(v)

        constants = constants if found else {}

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
        for glyph in font.glyphs:
            name = productionMap[glyph.name]
            layer = glyph.layers[0]
            bounds = layer.bounds
            for anchor in layer.anchors:
                if anchor.name == ITALIC_CORRECTION_ANCHOR:
                    italic[name] = _valueRecord(anchor.position.x - layer.width)
                elif anchor.name == TOP_ACCENT_ANCHOR:
                    accent[name] = _valueRecord(anchor.position.x)
                else:
                    for aname in (
                        KERN_TOP_RIHGT_ANCHOR,
                        KERN_TOP_LEFT_ANCHOR,
                        KERN_BOTTOM_RIGHT_ANCHOR,
                        KERN_BOTTOM_LEFT_ANCHOR,
                    ):
                        if anchor.name.startswith(aname):
                            ext = aname.split(".")[1]
                            pt = anchor.position
                            if ext.endswith("r"):
                                pt.x -= layer.width
                            elif ext.endswith("l"):
                                pt.x = -pt.x
                            kerning.setdefault(name, {}).setdefault(ext, []).append(pt)
            if e := glyph.userData[EXTENDED_SHAPE_ID]:
                extended.add(name)

        vvariants = {}
        hvariants = {}
        vassemblies = {}
        hassemblies = {}
        for glyph in font.glyphs:
            name = productionMap[glyph.name]
            varData = glyph.userData.get(VARIANTS_ID, {})
            if vvars := varData.get(V_VARIANTS_ID):
                vvariants[name] = vvars
            if hvars := varData.get(H_VARIANTS_ID):
                hvariants[name] = hvars
            if vassembly := varData.get(V_ASSEMBLY_ID):
                vassemblies[name] = vassembly[:]
                # Last part has italic correction, use it for the assembly.
                if ic := italic.get(str(vassemblies[name][-1][0])):
                    del italic[str(vassemblies[name][-1][0])]
                    vassemblies[name][0] = list(vassemblies[name][0]) + [ic]
            if hassembly := varData.get(H_ASSEMBLY_ID):
                hassemblies[name] = hassembly[:]
                if ic := italic.get(str(hassemblies[name][-1][0])):
                    del italic[str(hassemblies[name][-1][0])]
                    hassemblies[name][0] = list(hassemblies[name][0]) + [ic]

        if not any(
            [
                constants,
                italic,
                accent,
                vvariants,
                hvariants,
                vassemblies,
                hassemblies,
                kerning,
                extended,
            ]
        ):
            return

        ttFont["MATH"] = newTable("MATH")
        ttFont["MATH"].table = table = otTables.MATH()

        table.Version = 0x00010000

        if constants:
            table.MathConstants = otTables.MathConstants()
            for c, v in constants.items():
                setattr(table.MathConstants, c, v)

        glyphOrder = ttFont.getGlyphOrder()
        glyphMap = {n: i for i, n in enumerate(glyphOrder)}

        if italic or accent or extended:
            info = table.MathGlyphInfo = otTables.MathGlyphInfo()
            info.populateDefaults()

        if italic:
            coverage = otl.buildCoverage(italic.keys(), glyphMap)
            ic = info.MathItalicsCorrectionInfo = otTables.MathItalicsCorrectionInfo()
            ic.Coverage = coverage
            ic.ItalicsCorrection = [italic[n] for n in coverage.glyphs]

        if accent:
            coverage = otl.buildCoverage(accent.keys(), glyphMap)
            ta = info.MathTopAccentAttachment = otTables.MathTopAccentAttachment()
            ta.TopAccentCoverage = coverage
            ta.TopAccentAttachment = [accent[n] for n in coverage.glyphs]

        if kerning:
            coverage = otl.buildCoverage(kerning.keys(), glyphMap)
            ki = info.MathKernInfo = otTables.MathKernInfo()
            ki.MathKernCoverage = coverage
            ki.MathKernInfoRecords = records = []
            for glyph in coverage.glyphs:
                record = otTables.MathKernInfoRecord()
                for side in ("tr", "tl", "br", "bl"):
                    if pts := kerning[glyph].get(side):
                        kern = otTables.MathKern()
                        kern.HeightCount = len(pts) - 1
                        kern.CorrectionHeight = [_valueRecord(pt.y) for pt in pts[:-1]]
                        kern.KernValue = [_valueRecord(pt.x) for pt in pts]
                        if side == "tr":
                            record.TopRightMathKern = kern
                        elif side == "tl":
                            record.TopLeftMathKern = kern
                        if side == "br":
                            record.BottomRightMathKern = kern
                        elif side == "bl":
                            record.BottomLeftMathKern = kern
                records.append(record)

        if extended:
            info.ExtendedShapeCoverage = otl.buildCoverage(extended, glyphMap)

        if any([vvariants, hvariants, vassemblies, hassemblies]):
            table.MathVariants = otTables.MathVariants()
            overlap = userData.get("MinConnectorOverlap", 0)
            table.MathVariants.MinConnectorOverlap = overlap

        for vertical, variants, assemblies in (
            (True, vvariants, vassemblies),
            (False, hvariants, hassemblies),
        ):
            if not variants and not assemblies:
                continue
            coverage = list(variants.keys()) + list(assemblies.keys())
            coverage = otl.buildCoverage(coverage, glyphMap)
            constructions = []
            for glyph in coverage.glyphs:
                construction = None
                if glyph in variants:
                    names = [str(g) for g in variants[glyph]]
                    construction = otTables.MathGlyphConstruction()
                    construction.populateDefaults()
                    construction.VariantCount = len(names)
                    construction.MathGlyphVariantRecord = records = []
                    for name in names:
                        width, height = _getMetrics(font.glyphs[name].layers[0])
                        record = otTables.MathGlyphVariantRecord()
                        record.VariantGlyph = productionMap[name]
                        record.AdvanceMeasurement = int(height if vertical else width)
                        records.append(record)
                if glyph in assemblies:
                    if construction is None:
                        construction = otTables.MathGlyphConstruction()
                        construction.populateDefaults()
                    assembly = construction.GlyphAssembly = otTables.GlyphAssembly()
                    assembly.ItalicsCorrection = _valueRecord(0)
                    assembly.PartRecords = records = []
                    for part in assemblies[glyph]:
                        if len(part) > 4:
                            assembly.ItalicsCorrection = part[4]
                        partGlyph = font.glyphs[str(part[0])]
                        width, height = _getMetrics(partGlyph.layers[0])
                        record = otTables.GlyphPartRecord()
                        record.glyph = productionMap[str(part[0])]
                        record.PartFlags = int(part[1])
                        record.StartConnectorLength = int(part[2])
                        record.EndConnectorLength = int(part[3])
                        record.FullAdvance = int(height if vertical else width)
                        records.append(record)
                constructions.append(construction)

            if vertical:
                table.MathVariants.VertGlyphCoverage = coverage
                table.MathVariants.VertGlyphConstruction = constructions
            else:
                table.MathVariants.HorizGlyphCoverage = coverage
                table.MathVariants.HorizGlyphConstruction = constructions
