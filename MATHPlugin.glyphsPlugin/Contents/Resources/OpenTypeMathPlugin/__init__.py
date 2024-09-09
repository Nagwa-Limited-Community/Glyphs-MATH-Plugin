import AppKit
import objc
from GlyphsApp import GSGlyphReference


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
    when you add more `NSLocalizedString()`, run this from the command line (with the
    Resources folder as current folder)
    genstrings -u -q -o en.lproj plugin.py

    (requires macOS and Xcode installed.)
    For now, it needs the `def NSLocalizedString()` be changed to something like
    `defNSLocalizedStringXX()` to not confuse genstrings

    then sync all the new keys with the localized files.
"""


def NSLocalizedString(string, comment):
    return pluginBundle.localizedStringForKey_value_table_(string, string, None)
