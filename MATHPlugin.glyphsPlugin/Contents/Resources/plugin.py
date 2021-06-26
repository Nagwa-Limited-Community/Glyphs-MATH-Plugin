# Copyright 2021 Nagwa Limited

import json
import traceback

import objc
from AppKit import NSBezierPath, NSColor, NSMenuItem, NSOffState, NSOnState
from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from GlyphsApp import DOCUMENTEXPORTED, DRAWBACKGROUND, VIEW_MENU, Glyphs, Message
from GlyphsApp.plugins import GeneralPlugin

PLUGIN_ID = "com.nagwa.MATHPlugin"

CONSTANT_INTEGERS = [
    "ScriptPercentScaleDown",
    "ScriptScriptPercentScaleDown",
    "DelimitedSubFormulaMinHeight",
    "DisplayOperatorMinHeight",
    "RadicalDegreeBottomRaisePercent",
]

CONSTANT_VALUERECORDS = [
    "MathLeading",
    "AxisHeight",
    "AccentBaseHeight",
    "FlattenedAccentBaseHeight",
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
    "UpperLimitGapMin",
    "UpperLimitBaselineRiseMin",
    "LowerLimitGapMin",
    "LowerLimitBaselineDropMin",
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
    "OverbarVerticalGap",
    "OverbarRuleThickness",
    "OverbarExtraAscender",
    "UnderbarVerticalGap",
    "UnderbarRuleThickness",
    "UnderbarExtraDescender",
    "RadicalVerticalGap",
    "RadicalDisplayStyleVerticalGap",
    "RadicalRuleThickness",
    "RadicalExtraAscender",
    "RadicalKernBeforeDegree",
    "RadicalKernAfterDegree",
]

MATH_CONSTANTS = CONSTANT_INTEGERS + CONSTANT_VALUERECORDS

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

        menuItem = NSMenuItem.new()
        menuItem.setTitle_("Show MATH italic correction")
        menuItem.setAction_(self.toggleShowIC_)
        menuItem.setTarget_(self)
        state = self.defaults.get(f"{PLUGIN_ID}.{menuItem.identifier()}", NSOnState)
        self.setMenuItemState_(menuItem, state)
        Glyphs.menu[VIEW_MENU].append(menuItem)

        menuItem = NSMenuItem.new()
        menuItem.setTitle_("Show MATH top accent position")
        menuItem.setAction_(self.toggleShowTA_)
        menuItem.setTarget_(self)
        state = self.defaults.get(f"{PLUGIN_ID}.{menuItem.identifier()}", NSOnState)
        self.setMenuItemState_(menuItem, state)
        Glyphs.menu[VIEW_MENU].append(menuItem)

    @objc.python_method
    def __del__(self):
        Glyphs.removeCallback(self.export_)
        Glyphs.removeCallback(self.draw_)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

    def validateMenuItem_(self, menuItem):
        return Glyphs.font is not None and Glyphs.font.selectedLayers

    @objc.python_method
    def setMenuItemState_(self, menuItem, state):
        self.defaults[f"{PLUGIN_ID}.{menuItem.identifier()}"] = state
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

            # XXX
            url = instance.font.parent.fileURL()
            with open(url.path().replace(".glyphs", ".json")) as fp:
                data = json.load(fp)
            # XXX

            font = instance.interpolatedFont
            with TTFont(path) as ttFont:
                self.build_(font, ttFont, data)
                ttFont.save(path)
        except:
            Message(f"Exporting failed:\n{traceback.format_exc()}", self.name)

    @staticmethod
    def build_(font, ttFont, data):
        instance = font.instances[0]
        master = font.masters[0]

        constants = {}
        if data and "Parameters" in data:
            for c in MATH_CONSTANTS:
                v = data["Parameters"].get(c, None)
                if v is None:
                    print(f"MATH constant {c} is missing")
                    v = 0
                if v == "":
                    print(f"MATH constant {c} is empty")
                    v = 0
                v = int(float(v))
                if c in CONSTANT_VALUERECORDS:
                    record = otTables.MathValueRecord()
                    record.Value = v
                    constants[c] = record
                else:
                    constants[c] = v

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
