# Licences and Credits

Costumy is made of many open source projects that I like and wants to credit.  
I am also legally required to mention their licence, so in a way even the law wants you to acknowledge their awesomeness.

## Costumy's Licence

**Costumy's code is under [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)**  
Patterns and garments exported with Costumy are yours  
(that might depend on the body used to drape the pattern as a garment and the source of the pattern itself)

> The 3D bodies are under different licences (more restrictive), and are not distributed with Costumy.

## Costumy's Credits

Costumy was developped by [Christophe Marois](https://github.com/Qaqelol) within a [CDRIN](https://www.cdrin.com/) R&D project.  

Special Thanks to :

- Shaghayegh Taheri (Sherry)
- Olivier Leclerc
- Yann Roubeau
- Julien Coll

## Costumy's Dependencies

> [!NOTE]
> This list is just my best effort to give credit to what Costumy uses.  
> There is no endorsement from any of the dependencies.

| Name                | Licence     | Details/Attribution                                                                |
| ------------------- | ----------- | ---------------------------------------------------------------------------------- |
| [Freesewing][]      | MIT         | pattern generation, pattern designs, measurements_sets                             |
| [Blender][]         | GPL-3.0     | garment simulation, 3D bodies manipulations, measurements, renders                 |
| [SMPL][]            | [SMPL Model][] | SMPL 3D bodies usable with `costumy.bodies.SMPL` but not included with costumy     |
| [MB-Lab meshes][]   | [AGPL](https://mb-lab-docs.readthedocs.io/en/latest/license.html)        | MB-Lab 3D bodies usable with `costumy.bodies.Cmorph` but not included with costumy |
| [CharMorph][]       | GNU-3.0     | Add-on that handles MB-Lab bodies, not included with costumy                       |
| [Python][]          | Python      | Costumy is made in python                                                          |
| [Node.js][]         | Node.js     | Costumy calls node.js to use Freesewing and cubic2quad                             |
| [svg.path][]        | MIT         | pattern conversion from svg                                                        |
| [triangle][]        | LGPL-3.0    | create pattern topology for simulation (`costumy.simulation.prepare`)              |
| [mkdocs][]          | BSD         | Documentation generation                                                           |
| [mkdocs-material][] | MIT         | Documentation generation                                                           |
| [matplotlib][]      | BSD         | `costumy.classes.Pattern.as_plot()`                                                |
| [numpy][]           | BSD         | for fancy maths                                                                    |
| [cubic2quad][]      | MIT         | for cubic curves approximation (node.js)                                           |

> This table is a summary of the licences used (checked on the 9 april 2024) and might not be up to date.

### Additionnal mentions

- [GarmentPattern][] (MIT) for the pattern structure and `costumy.utils.functions.control_to_abs_coord()` and `control_to_relative_coord`.
- SVG patterns are exported with a link to open the path within [SvgPathEditor](https://github.com/Yqnn/svg-path-editor) to quickly visualize a panel without opening the svg in a software.

---

[SMPL Model]: https://smpl.is.tue.mpg.de/modellicense.html

[Freesewing]:https://github.com/freesewing/freesewing  

[Blender]:https://www.blender.org/about/license/

[GarmentPattern]:https://github.com/maria-korosteleva/Garment-Pattern-Generator  

[SMPL]:https://smpl.is.tue.mpg.de  

[MB-Lab meshes]:https://mb-lab-community.github.io/MB-Lab.github.io/  

[CharMorph]:https://github.com/Upliner/CharMorph  

[Python]:https://www.python.org/  

[Node.js]:https://github.com/nodejs/node  

[svg.path]:https://pypi.org/project/svg.path/  

[triangle]:https://pypi.org/project/triangle/  

[numpy]:https://numpy.org/  

[mkdocs]:https://www.mkdocs.org/  

[mkdocs-material]:https://squidfunk.github.io/mkdocs-material/  

[matplotlib]:https://matplotlib.org/  

[cubic2quad]: https://www.npmjs.com/package/cubic2quad  

