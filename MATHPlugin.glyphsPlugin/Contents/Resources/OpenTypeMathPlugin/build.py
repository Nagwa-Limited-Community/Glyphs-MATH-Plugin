from OpenTypeMathPlugin.constants import (
    CONSTANTS_ID,
    EXTENDED_SHAPE_ID,
    ITALIC_CORRECTION_ANCHOR,
    KERN_BOTTOM_LEFT_ANCHOR,
    KERN_BOTTOM_RIGHT_ANCHOR,
    KERN_TOP_LEFT_ANCHOR,
    KERN_TOP_RIGHT_ANCHOR,
    TOP_ACCENT_ANCHOR,
    H_ASSEMBLY_ID,
    H_VARIANTS_ID,
    VARIANTS_ID,
    V_ASSEMBLY_ID,
    V_VARIANTS_ID,
)
from OpenTypeMathPlugin.helpers import _bboxHeight, _bboxWidth


class MathTableBuilder:
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
                vVars = [productionMap[str(n)] for n in vVars]
                vVariants[name] = [
                    (n, _bboxHeight(font.glyphs[n].layers[0])) for n in vVars
                ]
                if glyph.userData[EXTENDED_SHAPE_ID]:
                    extended.update(str(v) for v in vVars)
            if hVars := varData.get(H_VARIANTS_ID):
                hVars = [productionMap[str(n)] for n in hVars]
                hVariants[name] = [
                    (n, _bboxWidth(font.glyphs[n].layers[0])) for n in hVars
                ]

            layer = glyph.layers[master.id]
            varData = layer.userData.get(VARIANTS_ID, {})
            if vAssembly := varData.get(V_ASSEMBLY_ID):
                vAssemblies[name] = [
                    [
                        (
                            productionMap[str(part[0])],
                            *part[1:],
                            _bboxHeight(part[0].glyph.layers[0]),
                        )
                        for part in vAssembly
                    ],
                    italic.pop(str(vAssembly[-1][0]), 0),
                ]
            if hAssembly := varData.get(H_ASSEMBLY_ID):
                hAssemblies[name] = [
                    [
                        (
                            productionMap[str(part[0])],
                            *part[1:],
                            _bboxWidth(part[0].glyph.layers[0]),
                        )
                        for part in hAssembly
                    ],
                    italic.pop(str(hAssembly[-1][0]), 0),
                ]

        if not any(
            [
                *constants.values(),
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
