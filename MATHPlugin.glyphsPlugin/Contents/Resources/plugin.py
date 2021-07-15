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
    Message,
)
from GlyphsApp.plugins import GeneralPlugin

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


class MPMissingGlyph(Exception):
    def __init__(self, name):
        super().__init__(f"Glyph name referenced but missing from font: {name}")


class MPGlyphName(NSObject):
    @staticmethod
    def __new__(cls, *args, **kwargs):
        return cls.new()

    @objc.python_method
    def __init__(self, font, name):
        self.glyph = font.glyphs[name]
        if not self.glyph:
            font.tempData[STATUS_ID] = False
            raise MPMissingGlyph(name)

    @objc.python_method
    def __str__(self):
        return self.glyph.name

    @objc.python_method
    def __repr__(self):
        return str(self)

    @objc.python_method
    def __eq__(self, other):
        return str(self) == str(other)

    def propertyListValueFormat_(self, formatVersion):
        return str(self)


def _getMetrics(layer):
    width = layer.width
    height = layer.vertWidth
    if height is None:
        height = layer.bounds.size.height
    return (width, height)


class MATHPlugin(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.name = "OpenType MATH Plug-in"

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

    def message_(self, message):
        Message(message, self.name)

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

            def makeCallback(c, constants):
                def callback(sender):
                    value = sender.get()
                    value = value if value is None else int(value)
                    if c in constants and constants[c] == value:
                        return

                    constants[c] = value
                    if value is None:
                        del constants[c]

                    if constants:
                        master.userData[CONSTANTS_ID] = constants

                return callback

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
                        callback=makeCallback(c, constants),
                        formatter=formatter,
                        placeholder="0",
                    )
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
            self.message_(f"Editing failed:\n{traceback.format_exc()}")

    def editGlyph_(self, menuItem):
        try:
            font = Glyphs.font
            glyph = font.selectedLayers[0].parent

            window = vanilla.Window((650, 400), "MATH Variants")
            window.tabs = vanilla.Tabs((10, 10, -10, -10), ["Vertical", "Horizontal"])

            def gn(n):
                return n
                return MPGlyphName(font, n)

            def callback(sender):
                try:
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
                    var = [gn(n) for n in new.split()]
                    varData[H_VARIANTS_ID if tag else V_VARIANTS_ID] = var
                    glyph.userData[VARIANTS_ID] = dict(varData)
                except:
                    self.message_(traceback.format_exc())

            emptyRow = {"g": "", "s": 0, "e": 0, "f": False}

            def editCallback(sender):
                try:
                    old = []
                    new = [
                        (
                            gn(item["g"]),
                            int(item["f"]),
                            int(item["s"]),
                            int(item["e"]),
                        )
                        for item in sender.get()
                        if item != emptyRow
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
                    self.message_(traceback.format_exc())

            def doubleClickCallback(sender):
                try:
                    table = sender.getNSTableView()
                    column = table.clickedColumn()
                    row = table.clickedRow()
                    if row < 0 and column < 0:
                        items = sender.get()
                        items.append(emptyRow)
                        sender.set(items)
                        row = len(items) - 1
                    table._startEditingColumn_row_event_(column, row, None)
                except:
                    self.message_(traceback.format_exc())

            def checkBoxCallback(sender):
                glyph.userData[EXTENDED_SHAPE_ID] = sender.get()
                if not sender.get():
                    del glyph.userData[EXTENDED_SHAPE_ID]

            for i, tab in enumerate(window.tabs):
                tab.vbox = vanilla.TextBox("auto", "Variants:")
                tab.vedit = vanilla.EditText(
                    "auto", continuous=False, callback=callback
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
                    editCallback=editCallback,
                    doubleClickCallback=doubleClickCallback,
                )
                tab.alist.getNSTableView().setTag_(i)
                rules = [
                    "V:|-[vbox]-[vedit]-[abox]-[alist]-|",
                    "H:|-[vbox]-|",
                    "H:|-[vedit]-|",
                    "H:|-[abox]-|",
                    "H:|-[alist]-|",
                ]
                if i == 0:
                    tab.check = vanilla.CheckBox(
                        "auto", "Extended shape", callback=checkBoxCallback
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

            window.open()
        except:
            self.message_(f"Editing failed:\n{traceback.format_exc()}")

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
        except:
            self.message_(f"Drawing anchors failed:\n{traceback.format_exc()}")

    @objc.python_method
    def open_(self, notification):
        """Load glyph name in GSGlyph.userData into GlyphName class so they
        track glyph renames."""
        try:
            doc = notification.object()
            font = doc.font

            def gn(n):
                return n
                return MPGlyphName(font, n)

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
            self.message_(f"Opening failed:\n{e}")
        except:
            self.message_(f"Opening failed:\n{traceback.format_exc()}")

    @objc.python_method
    def export_(self, notification):
        try:
            info = notification.object()
            instance = info["instance"]
            path = info["fontFilePath"]

            if not instance.font.tempData[STATUS_ID]:
                self.message_(f"Export failed:\nloading math data failed")
                return

            font = instance.interpolatedFont
            with TTFont(path) as ttFont:
                success = self.build_(font, ttFont)
                if "MATH" in ttFont:
                    ttFont.save(path)
                    self.notification_("MATH table exported successfully")
        except:
            self.message_(f"Export failed:\n{traceback.format_exc()}")

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
                    record = otTables.MathValueRecord()
                    record.Value = v
                    constants[c] = record

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
        extended = set()
        for glyph in font.glyphs:
            name = productionMap[glyph.name]
            layer = glyph.layers[0]
            for anchor in layer.anchors:
                if anchor.name == ITALIC_CORRECTION_ANCHOR:
                    italic[name] = otTables.MathValueRecord()
                    italic[name].Value = int(anchor.position.x - layer.width)
                elif anchor.name == TOP_ACCENT_ANCHOR:
                    accent[name] = otTables.MathValueRecord()
                    accent[name].Value = int(anchor.position.x)
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
                    assembly.ItalicsCorrection = otTables.MathValueRecord()
                    assembly.ItalicsCorrection.Value = 0
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
