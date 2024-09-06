# flake8: noqa

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

# fmt: off
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
# fmt: on

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
