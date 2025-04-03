---
title: Examples
---

This page contains scripts examples using costumy.

## Same shirt on different bodies

This example simulates the same shirt onto bodies of increasing size.

```python
from costumy.classes import Pattern
from costumy.designs import Aaron
from costumy.bodies import SMPL
from pathlib import Path


# Single sleevless shirt from freesewing
design = Aaron.from_template_measures()
pattern = design.new_pattern()

outdir = Path() # path to a directory 
for i in range(0,4):
    # outdir/shirt_00
    fp = Path(outdir/f"shirt_{i:02}") 

    # Create a SMPL body
    body = SMPL(shapes=[0,-i])
    body.setup()

    # Align the pattern with the current body
    pattern.align_panels(body.references)
    
    # Export the shirt as a garment
    pattern.as_garment(body.object, output_path = fp.with_suffix(".obj"))
    
    # Export the shirt pattern as an svg
    with open(fp.with_suffix(".svg"), "w", encoding="utf8") as f:
        f.write(pattern.as_svg()) # or pattern.as_debug_svg()
    
```

## Same design adjusted for different bodies

This example creates fitted pattern of the same design for bodies of increasing size.

```python
from costumy.classes import Pattern
from costumy.designs import Aaron
from costumy.bodies import SMPL
from pathlib import Path

outdir = Path() # path to a directory 
for i in range(0,4):
    # outdir/shirt_00
    fp = Path(outdir/f"shirt_{i:02}") 

    # Create a SMPL body
    body = SMPL(shapes=[0,-i])
    body.setup()

    # Make a pattern for each bodies
    pattern = Aaron(body.measures).new_pattern()
    pattern.align_panels(body.references)
    
    # Export the shirt as a garment
    pattern.as_garment(body.object, output_path = fp.with_suffix(".obj"))
    
    # Export the shirt pattern as an svg
    with open(fp.with_suffix(".svg"), "w", encoding="utf8") as f:
        f.write(pattern.as_svg()) # or pattern.as_debug_svg()

```

## All styles on a single body

This example simulates the same design with different style on one body.

```python
from costumy.designs import Aaron
from costumy.bodies import Cmorph
from pathlib import Path

# Create a mb-lab body
body = Cmorph()
body.setup()

# Make design from measurements
design = Aaron(body.measures)

outdir = Path() #location of ur choice

# Make a pattern for each style
for style, options in design.styles.items():
    fp = Path(outdir/f"shirt_{style}")
    
    # Make a pattern using the style
    pattern = design.new_pattern(style)
    pattern.align_panels(body.references)

    # Export the shirt as a garment
    pattern.as_garment(body.object, output_path = fp.with_suffix(".obj"))
    
    # Export the shirt pattern as an svg
    with open(fp.with_suffix(".svg"), "w", encoding="utf8") as f:
        f.write(pattern.as_svg()) # or pattern.as_debug_svg()

```

