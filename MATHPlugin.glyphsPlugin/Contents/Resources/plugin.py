# Copyright 2021 Nagwa Limited

import traceback

import objc
import vanilla
from AppKit import NSBezierPath, NSColor, NSMenuItem, NSOffState, NSOnState
from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from GlyphsApp import (
    DOCUMENTEXPORTED,
    DRAWBACKGROUND,
    EDIT_MENU,
    VIEW_MENU,
    Glyphs,
    Message,
)
from GlyphsApp.plugins import GeneralPlugin

PLUGIN_ID = "com.nagwa.MATHPlugin"

MATH_CONSTANTS_GENERAL = [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
    "MathLeading",
    "AxisHeight",
    "AccentBaseHeight",
    "FlattenedAccentBaseHeight",
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

CONSTANT_INTEGERS = [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
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

ITALIC_CORRECTION_ANCHOR = "math.ic"
TOP_ACCENT_ANCHOR = "math.ta"


class MATHPlugin(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.name = "OpenType MATH Plug-in"

    @objc.python_method
    def start(self):
        self.defaults = Glyphs.defaults

        Glyphs.addCallback(self.export_, DOCUMENTEXPORTED)
        Glyphs.addCallback(self.draw_, DRAWBACKGROUND)

        menuItem = self.newMenuItem_("Show MATH italic correction", self.toggleShowIC_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Show MATH top accent position", self.toggleShowTA_)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = self.newMenuItem_("Edit MATH constants...", self.editFont_, False)
        Glyphs.menu[EDIT_MENU].append(menuItem)

    @objc.python_method
    def __del__(self):
        Glyphs.removeCallback(self.export_)
        Glyphs.removeCallback(self.draw_)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

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

    def editFont_(self, menuItem):
        try:
            master = Glyphs.font.selectedFontMaster
            if PLUGIN_ID not in master.userData:
                master.userData[PLUGIN_ID] = {}
            if "constants" not in master.userData[PLUGIN_ID]:
                master.userData[PLUGIN_ID]["constants"] = {}
            data = master.userData[PLUGIN_ID]["constants"]

            width, height = 650, 400
            border = 10
            gap = 30
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

            def makeCallback(c):
                def callback(sender):
                    # Make a copy, otherwise Glyphs wont mark the font modified.
                    # https://forum.glyphsapp.com/t/changing-userdata-does-not-always-mark-the-document-modified/19456
                    data = dict(master.userData[PLUGIN_ID])
                    constants = dict(data["constants"])
                    constants[c] = sender.get()
                    data["constants"] = constants
                    master.userData[PLUGIN_ID] = data

                return callback

            window.tabs = vanilla.Tabs((border, border, -border, -border), tabs.keys())
            for i, name in enumerate(tabs.keys()):
                subwidth = width / 2 - border
                tab = window.tabs[i]
                tab.l = vanilla.Box((0, 0, subwidth, 0))
                tab.r = vanilla.Box((subwidth, 0, subwidth, 0))
                tab.l.setBorderWidth(0)
                tab.r.setBorderWidth(0)
                constants = tabs[name]
                for j, c in enumerate(constants):
                    callback = makeCallback(c)
                    v = data.get(c, 0)
                    box = vanilla.TextBox(
                        (0, gap * j + 1, -border, -border), c, alignment="right"
                    )
                    edit = vanilla.EditText(
                        (0, gap * j + 1, 40, 25), v, callback=callback
                    )
                    setattr(tab.l, f"{c}Box", box)
                    setattr(tab.r, f"{c}Edit", edit)
            window.open()
        except:
            Message(f"Setting constancies failed:\n{traceback.format_exc()}", self.name)

    def editGlyph_(self, menuItem):
        layer = Glyphs.font.selectedLayers[0]
        data = layer.userData[PLUGIN_ID]
        if data:
            print(data)

    @objc.python_method
    def draw_(self, layer, options):
        try:
            names = []
            if self.defaults[f"{PLUGIN_ID}.toggleShowIC:"]:
                names.append(ITALIC_CORRECTION_ANCHOR)
            if self.defaults[f"{PLUGIN_ID}.toggleShowTA:"]:
                names.append(TOP_ACCENT_ANCHOR)

            master = layer.master
            scale = 1.2 * options["Scale"]
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
        except:
            Message(f"Drawing anchors failed:\n{traceback.format_exc()}", self.name)

    @objc.python_method
    def export_(self, notification):
        try:
            info = notification.object()
            instance = info["instance"]
            path = info["fontFilePath"]

            font = instance.interpolatedFont
            with TTFont(path) as ttFont:
                self.build_(font, ttFont)
                ttFont.save(path)
        except:
            Message(f"Exporting failed:\n{traceback.format_exc()}", self.name)

    @staticmethod
    def build_(font, ttFont):
        instance = font.instances[0]
        master = font.masters[0]
        data = master.userData[PLUGIN_ID]

        constants = {}
        found = False
        if data and "constants" in data:
            for c in MATH_CONSTANTS:
                v = data["constants"].get(c, None)
                if v is None:
                    v = 0
                else:
                    found = True
                v = int(v)
                if c in CONSTANT_INTEGERS:
                    constants[c] = v
                else:
                    record = otTables.MathValueRecord()
                    record.Value = v
                    constants[c] = record

        constants = constants if found else {}

        if (
            font.customParameters["Don't use Production Names"]
            or instance.customParameters["Don't use Production Names"]
        ):
            productionNameMap = {g.name: g.name for g in font.glyphs}
        else:
            productionNameMap = {g.name: g.productionName for g in font.glyphs}

        italic = {}
        accent = {}
        for glyph in font.glyphs:
            name = productionNameMap[glyph.name]
            for anchor in glyph.layers[0].anchors:
                if anchor.name == ITALIC_CORRECTION_ANCHOR:
                    italic[name] = otTables.MathValueRecord()
                    italic[name].Value = int(anchor.position.x)
                elif anchor.name == TOP_ACCENT_ANCHOR:
                    accent[name] = otTables.MathValueRecord()
                    accent[name].Value = int(anchor.position.x)

        if not any([constants, italic, accent]):
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

        if not any([italic, accent]):
            return

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
