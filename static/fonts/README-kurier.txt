Kurier web fonts
================

The files kurier-*-latin.woff2 in this folder are a modified version (a
"Derived Work" in the sense of the LaTeX Project Public License) of the
font Kurier.

  Typeface design: Malgorzata Budyta, Warszawa, Poland (1975)
  Font:            Janusz Marian Nowacki, Grudziadz, Poland
  Copyright 2005-2010 Janusz M. Nowacki.
  Released under the GUST Font License, see GUST-FONT-LICENSE.txt in this
  folder.


Original
--------

The complete, unmodified original (version 0.995b, August 2010) is available
from CTAN:

  https://ctan.org/pkg/kurier


Changes
-------

Only these four of the original OpenType files were used:

  Kurier-Regular.otf     ->  kurier-regular-latin.woff2
  Kurier-Italic.otf      ->  kurier-italic-latin.woff2
  Kurier-Bold.otf        ->  kurier-bold-latin.woff2
  Kurier-BoldItalic.otf  ->  kurier-bold-italic-latin.woff2

Each file was changed as follows, using fontTools 4.60.1 (pyftsubset):

1. Reduced to the glyphs for these Unicode ranges (Basic Latin, Latin-1
   including the German umlauts and sharp s, general punctuation, the euro
   sign and a few common symbols); all other glyphs (Latin Extended,
   Cyrillic, Greek, Vietnamese, mathematical symbols) were removed:

     U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
     U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2190-2199, U+2212,
     U+2215, U+2300, U+2318

   All OpenType layout features of the kept glyphs were retained.

2. Converted from OpenType (OTF) to WOFF2.

The glyph shapes and metrics were not changed. The copyright notice and the
font family and style names inside the files were kept unchanged.


Support
-------

These files are provided as they are, for use on this website. The authors
of the original font do not provide any support for this modified version.
Please do not send reports about these files to them.
