import AppKit

from GlyphsApp import GSGlyphReference
from GlyphsApp.drawingTools import restore, save, translate
from OpenTypeMathPlugin.constants import (
    CONSTANTS_ID,
    ITALIC_CORRECTION_ANCHOR,
    KERN_BOTTOM_LEFT_ANCHOR,
    KERN_BOTTOM_RIGHT_ANCHOR,
    KERN_TOP_LEFT_ANCHOR,
    KERN_TOP_RIGHT_ANCHOR,
    SAMPLE_MATH_ACCENTS,
    TOP_ACCENT_ANCHOR,
)
from OpenTypeMathPlugin.helpers import _bboxHeight, _bboxWidth, _getMetrics


def dashedLine(pt1, pt2, width):
    path = AppKit.NSBezierPath.bezierPath()
    path.setLineWidth_(width)
    path.setLineDash_count_phase_((width * 2, width * 2), 2, 0)
    path.moveToPoint_(pt1)
    path.lineToPoint_(pt2)
    path.stroke()


class MathDrawing:
    @staticmethod
    def drawAnchors(layer, name, width):
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
                    MathDrawing.drawAccent(layer, anchor)
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
            if variantLayer is None:
                continue

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
            if partLayer is None:
                continue
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
            if partLayer is None:
                continue

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
