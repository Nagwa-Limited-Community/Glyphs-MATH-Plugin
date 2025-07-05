# Copyright 2021 Nagwa Limited

import traceback

import objc
import AppKit

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
    GSCallbackHandler,
)
from GlyphsApp.plugins import GeneralPlugin
from OpenTypeMathPlugin import NSLocalizedString
from OpenTypeMathPlugin.build import MathTableBuilder
from OpenTypeMathPlugin.constants import (
    CONSTANTS_ID,
    EXTENDED_SHAPE_ID,
    ITALIC_CORRECTION_ANCHOR,
    KERN_BOTTOM_LEFT_ANCHOR,
    KERN_BOTTOM_RIGHT_ANCHOR,
    KERN_TOP_LEFT_ANCHOR,
    KERN_TOP_RIGHT_ANCHOR,
    MATH_CONSTANTS,
    NAME,
    PLUGIN_ID,
    SKIP_EXPORT_ID,
    STATUS_ID,
    TOP_ACCENT_ANCHOR,
    H_ASSEMBLY_ID,
    H_VARIANTS_ID,
    VARIANTS_ID,
    V_ASSEMBLY_ID,
    V_VARIANTS_ID,
)
from OpenTypeMathPlugin.drawing import MathDrawing
from OpenTypeMathPlugin.windows import ConstantsWindow, VariantsWindow, _message


class MATHPlugin(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.name = NAME

    @objc.python_method
    def start(self):
        self.defaults = Glyphs.defaults

        if self.defaults.get(SKIP_EXPORT_ID):
            self.notification_(
                "MATHPlugin export is disabled. "
                'Set Glyphs.defaults["com.nagwa.MATHPlugin.skipExport"] to False to enable it.'
            )
        else:
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
        if not self.defaults.get(SKIP_EXPORT_ID):
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
        except Exception:
            _message(f"Editing failed:\n{traceback.format_exc()}")

    def editGlyph_(self, menuItem):
        try:
            layer = Glyphs.font.selectedLayers[0]
            window = VariantsWindow(layer)
            window.open()
        except Exception:
            _message(f"Editing failed:\n{traceback.format_exc()}")

    @objc.python_method
    def draw_(self, layer, options):
        try:
            scale = 1 / options["Scale"]

            if self.defaults[f"{PLUGIN_ID}.toggleShowIC:"]:
                MathDrawing.drawAnchors(layer, ITALIC_CORRECTION_ANCHOR, scale)
            if self.defaults[f"{PLUGIN_ID}.toggleShowTA:"]:
                MathDrawing.drawAnchors(layer, TOP_ACCENT_ANCHOR, scale)

            if self.defaults[f"{PLUGIN_ID}.toggleShowMK:"]:
                MathDrawing.drawMathKern(layer, scale)

            showGV = self.defaults[f"{PLUGIN_ID}.toggleShowGV:"]
            showGA = self.defaults[f"{PLUGIN_ID}.toggleShowGA:"]
            if showGV or showGA:
                layerData = layer.userData.get(VARIANTS_ID, {})
                glyphData = layer.parent.userData.get(VARIANTS_ID, {})
                if layerData or glyphData:
                    assembly = layerData.get(V_ASSEMBLY_ID, []) if showGA else []
                    variants = glyphData.get(V_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        MathDrawing.drawVariants(variants, assembly, layer, scale, True)

                    assembly = layerData.get(H_ASSEMBLY_ID, []) if showGA else []
                    variants = glyphData.get(H_VARIANTS_ID, []) if showGV else []
                    if assembly or variants:
                        MathDrawing.drawVariants(
                            variants, assembly, layer, scale, False
                        )
        except Exception:
            _message(f"Drawing MATH data failed:\n{traceback.format_exc()}")

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
            except Exception:
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
        except Exception:
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
                _message("Export failed:\nloading math data failed")
                return

            font = instance.interpolatedFont

            with TTFont(path) as ttFont:
                MathTableBuilder.buildMathTable(font, ttFont)
                if "MATH" in ttFont:
                    ttFont.save(path)
                    self.notification_("MATH table exported successfully")
        except Exception:
            _message(f"Export failed:\n{traceback.format_exc()}")

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
            value = None
            for masterId, factor in interpolation.items():
                userData = font.masters[masterId].userData.get(CONSTANTS_ID, {})
                if v := userData.get(c):
                    if value is None:
                        value = 0
                    value += v * factor
            if value is not None:
                constants[c] = round(value)
        if constants:
            master.userData[CONSTANTS_ID] = constants

        return (True, None)
