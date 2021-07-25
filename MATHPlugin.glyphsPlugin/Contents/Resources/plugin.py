# Copyright 2021 Nagwa Limited

import traceback

import objc
import vanilla
from AppKit import (
    NSAlternateKeyMask,
    NSBezierPath,
    NSColor,
    NSCommandKeyMask,
    NSMenuItem,
    NSNumberFormatter,
    NSObject,
    NSOffState,
    NSOnState,
    NSShiftKeyMask,
)
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
    GSGlyphReference,
    Message,
)
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


class MPGlyphReference(GSGlyphReference):
    @objc.python_method
    def __str__(self):
        return self.glyph.name

    @objc.python_method
    def __repr__(self):
        return str(self)

    @objc.python_method
    def __eq__(self, other):
        return str(self) == str(other)


class VariantsWindow:
    def __init__(self, glyph):
        self._glyph = glyph
        self._window = window = vanilla.Window((650, 400), "MATH Variants")
        window.tabs = vanilla.Tabs((10, 10, -10, -10), ["Vertical", "Horizontal"])

        self._emptyRow = {"g": "", "s": 0, "e": 0, "f": False}

        for i, tab in enumerate(window.tabs):
            tab.vbox = vanilla.TextBox("auto", "Variants:")
            tab.vedit = vanilla.EditText(
                "auto", continuous=False, callback=self._editTextCallback
            )
            tab.vedit.getNSTextField().setTag_(i)

            tab.abox = vanilla.TextBox("auto", "Assembly:")
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
            rules = [
                "V:|-[vbox]-[vedit(40)]-[abox]-[alist]-|",
                "H:|-[vbox]-|",
                "H:|-[vedit]-|",
                "H:|-[abox]-|",
                "H:|-[alist]-|",
            ]
            if i == 0:
                tab.check = vanilla.CheckBox(
                    "auto", "Extended shape", callback=self._checkBoxCallback
                )
                rules[0] = rules[0][:-1] + "[check]-|"
                rules.append("|-[check]-|")
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
            return MPGlyphReference(self._glyph.parent.glyphs[name])
        except:
            _message(traceback.format_exc())

    def _editTextCallback(self, sender):
        try:
            glyph = self._glyph
            old = ""
            new = sender.get().strip()
            tag = sender.getNSTextField().tag()
            varData = glyph.userData[VARIANTS_ID]
            if not varData:
                varData = {}
            if var := varData.get(H_VARIANTS_ID if tag else V_VARIANTS_ID):
                old = " ".join(str(v) for v in var)
            if old == new:
                return

            varData = {k: list(v) for k, v in varData.items()}
            var = [self._glyphRef(n) for n in new.split()]
            varData[H_VARIANTS_ID if tag else V_VARIANTS_ID] = var
            glyph.userData[VARIANTS_ID] = dict(varData)
        except:
            _message(traceback.format_exc())

    def _listEditCallback(self, sender):
        try:
            glyph = self._glyph
            old = []
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
            tag = sender.getNSTableView().tag()
            varData = glyph.userData[VARIANTS_ID]
            if not varData:
                varData = {}
            if var := varData.get(H_ASSEMBLY_ID if tag else V_ASSEMBLY_ID):
                old = var
            if old == new:
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

        menuItem = self.newMenuItem_("Edit MATH Variants...", self.editGlyph_, False)
        menuItem.setKeyEquivalentModifierMask_(NSCommandKeyMask | NSShiftKeyMask)
        menuItem.setKeyEquivalent_("x")
        Glyphs.menu[GLYPH_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Edit MATH Constants...", self.editFont_, False)
        menuItem.setKeyEquivalentModifierMask_(NSCommandKeyMask | NSAlternateKeyMask)
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
        menuItem = NSMenuItem.new()
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
            state = self.defaults.get(key, NSOnState)
        self.defaults[key] = state
        menuItem.setState_(state)

    def toggleShowIC_(self, menuItem):
        newState = NSOnState
        state = menuItem.state()
        if state == NSOnState:
            newState = NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowTA_(self, menuItem):
        newState = NSOnState
        state = menuItem.state()
        if state == NSOnState:
            newState = NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def toggleShowMK_(self, menuItem):
        newState = NSOnState
        state = menuItem.state()
        if state == NSOnState:
            newState = NSOffState
        self.setMenuItemState_(menuItem, newState)
        Glyphs.redraw()

    def editFont_(self, menuItem):
        try:
            master = Glyphs.font.selectedFontMaster
            if CONSTANTS_ID not in master.userData:
                constants = {}
            else:
                constants = dict(master.userData[CONSTANTS_ID])

            width, height = 650, 400
            window = vanilla.Window((width, height), "MATH Constants")
            tabs = {
                "General": MATH_CONSTANTS_GENERAL,
                "Sub/Superscript": MATH_CONSTANTS_SCRIPTS,
                "Limits": MATH_CONSTANTS_LIMITS,
                "Stacks": MATH_CONSTANTS_STACKS,
                "Fractions": MATH_CONSTANTS_FRACTIONS,
                "Over/Underbar": MATH_CONSTANTS_BARS,
                "Radicals": MATH_CONSTANTS_RADICALS,
            }

            def callback(sender):
                value = sender.get()
                value = value if value is None else int(value)
                tag = sender.getNSTextField().tag()
                c = MATH_CONSTANTS[tag]
                if c in constants and constants[c] == value:
                    return

                constants[c] = value
                if value is None:
                    del constants[c]

                if constants:
                    master.userData[CONSTANTS_ID] = constants

            uformatter = NSNumberFormatter.new()
            uformatter.setAllowsFloats_(False)
            uformatter.setMinimum_(0)
            uformatter.setMaximum_(0xFFFF)

            sformatter = NSNumberFormatter.new()
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
                    formatter = uformatter if c in CONSTANT_UNSIGNED else sformatter
                    box.edit = vanilla.EditText(
                        "auto",
                        constants.get(c, None),
                        callback=callback,
                        formatter=formatter,
                        placeholder="0",
                    )
                    box.edit.getNSTextField().setTag_(MATH_CONSTANTS.index(c))
                    box.box.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])
                    box.edit.getNSTextField().setToolTip_(MATH_CONSTANTS_TOOLTIPS[c])

                    box.addAutoPosSizeRules(
                        [
                            f"H:|[box({width/2})]-[edit(40)]-{width/2-40}-|",
                            "V:|[box]|",
                            "V:|[edit(24)]|",
                        ]
                    )
                    rules.append(f"H:|[{c}]|")
                    setattr(tab, f"{c}", box)
                tab.addAutoPosSizeRules(rules)
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
            names = []
            if self.defaults[f"{PLUGIN_ID}.toggleShowIC:"]:
                names.append(ITALIC_CORRECTION_ANCHOR)
            if self.defaults[f"{PLUGIN_ID}.toggleShowTA:"]:
                names.append(TOP_ACCENT_ANCHOR)

            master = layer.master
            scale = 1 / options["Scale"]
            for anchor in layer.anchors:
                if anchor.name in names:
                    line = NSBezierPath.bezierPath()
                    line.moveToPoint_((anchor.position.x, master.descender))
                    line.lineToPoint_((anchor.position.x, master.ascender))
                    line.setLineWidth_(scale)
                    if anchor.name == ITALIC_CORRECTION_ANCHOR:
                        NSColor.blueColor().set()
                    elif anchor.name == TOP_ACCENT_ANCHOR:
                        NSColor.magentaColor().set()
                    line.stroke()

            if not self.defaults[f"{PLUGIN_ID}.toggleShowMK:"]:
                return

            for name in (
                KERN_TOP_RIHGT_ANCHOR,
                KERN_TOP_LEFT_ANCHOR,
                KERN_BOTTOM_RIGHT_ANCHOR,
                KERN_BOTTOM_LEFT_ANCHOR,
            ):
                points = []
                for anchor in layer.anchors:
                    if anchor.name.startswith(name):
                        points.append(anchor.position)
                points = sorted(points, key=lambda pt: pt.y)

                line = NSBezierPath.bezierPath()
                line.setLineWidth_(scale)
                NSColor.greenColor().set()
                for i, pt in enumerate(points):
                    if i == 0:
                        line.moveToPoint_((pt.x, master.descender))
                    line.lineToPoint_((pt.x, pt.y))
                    if i < len(points) - 1:
                        line.lineToPoint_((points[i + 1].x, pt.y))
                    else:
                        line.lineToPoint_((pt.x, master.ascender))
                line.stroke()
        except:
            _message(f"Drawing anchors failed:\n{traceback.format_exc()}")

    @objc.python_method
    def open_(self, notification):
        """Load glyph name in GSGlyph.userData into GlyphName class so they
        track glyph renames."""
        try:
            doc = notification.object()
            font = doc.font

            def gn(n):
                return MPGlyphReference(font.glyphs[n])

            varids = (V_VARIANTS_ID, H_VARIANTS_ID)
            assemblyids = (V_ASSEMBLY_ID, H_ASSEMBLY_ID)
            for glyph in font.glyphs:
                varData = glyph.userData.get(VARIANTS_ID, {})
                for id in varids:
                    if names := varData.get(id):
                        varData[id] = [gn(n) for n in names]
                for id in assemblyids:
                    if assembly := varData.get(id):
                        varData[id] = [(gn(a[0]), *a[1:]) for a in assembly]
            font.tempData[STATUS_ID] = True
        except MPMissingGlyph as e:
            _message(f"Opening failed:\n{e}")
        except:
            _message(f"Opening failed:\n{traceback.format_exc()}")

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
                success = self.build_(font, ttFont)
                if "MATH" in ttFont:
                    ttFont.save(path)
                    self.notification_("MATH table exported successfully")
        except:
            _message(f"Export failed:\n{traceback.format_exc()}")

    @staticmethod
    def build_(font, ttFont):
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
                                pt.x -= bounds.origin.x + bounds.size.width
                            elif ext.endswith("l"):
                                pt.x = bounds.origin.x - pt.x
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

        if italic or accent:
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
            table.MathGlyphInfo.ExtendedShapeCoverage = otl.buildCoverage(
                extended, glyphMap
            )

        if any([vvariants, hvariants, vassemblies, hassemblies]):
            table.MathVariants = otTables.MathVariants()
            overlap = userData.get("MinConnectorOverlap", 0)
            table.MathVariants.MinConnectorOverlap = overlap

        for variants, assemblies in (
            (vvariants, vassemblies),
            (hvariants, hassemblies),
        ):
            if not variants and not assemblies:
                continue
            vertical = variants == vvariants
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
