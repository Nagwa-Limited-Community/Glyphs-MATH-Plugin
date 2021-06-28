Glyphs OpenType MATH Plug-in
============================

This is a plug-in for [Glyphs app](https://glyphsapp.com) to edit OpenType MATH
table data as well as generate MATH table when exporting font.

Installation
------------

To install from Git, clone this repository, open `MATHPlugin.glyphsPlugin` in
Glyphs (e.g. by double clicking or drag and drop), and Glyphs will prompt you
to install it. Select Install, and when asked whether to Copy or Alias the
plug-in, Alias is preferred so that the plug-in gets updated when the local
clone is updated without having to install again.

The plug-in requires FontTools and Vanilla modules, make sure to install them
from _Window → Plugin Manger → Modules_.

Restart Glyphs and the plug-in should be ready (when the plug-in is updated
Glyphs should be restarted as well, to use the new version).

Usage
-----

The plug-in adds some new menu entries:
* _Edit → Edit MATH Constants..._ for editing font-level MATH table constants.
  The constants are saved per-master and should be edited for each master.
  ![MATH constants dialog](math-constants.png)
* _View → Show MATH Italic Correction_ draws a vertical _blue_ line if there is
  an anchor named `math.ic`. This anchor will use to generate italic
  correction.
* _View → Show MATH Top Accent Position_ draws a vertical _magenta_ line if
  there is an anchor named `math.ta`. This anchor will use to generate top
  accent position.
  ![MATH anchors](math-anchors.png)

If the font contains any MATH data, the plug-in will generate MATH table when
the font is exported, no extra steps are needed.
