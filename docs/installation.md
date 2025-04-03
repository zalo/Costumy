---
title: Installation
---

This page explains how to install the costumy prototype project.

## Requirements

To use costumy you will need :

- Python 3.10.0 (exact version)
- Node.js
- A system that meets [blender's minimum requirements](https://www.blender.org/download/requirements/)

>[!NOTE]
> You must use python 3.10.0 exactly.  
> Blender is released as a python package ([bpy](https://pypi.org/project/bpy/)) that requires a specific python version to work.

## Installation steps

### Installing the basics

To install costumy you may do the following :

1. Install [Python 3.10.0](https://www.python.org/downloads/release/python-3100/)
2. Install [Node.js](https://nodejs.org/en/download)
3. Clone Costumy's repository in the location of your choice

Next, you will need to create a virtual environment.

### Creating the virtual environment

1. Navigate to costumy's repository root in a terminal.  
You want to be in the repository root, not within the `costumy` package.

    ```powershell
    cd path/to/my/dir
    ```

2. Create the virtual environment

    ```powershell
    py -3.10 -m venv venv
    ```

    >[!NOTE]
    > Windows has a python manager installed (`py`). On other OS, you might need to do something like `path/to/python3.10 -m venv path/to/project`. See [venv docs](https://docs.python.org/3/library/venv.html#creating-virtual-environments)

3. Activate the virtual environment

    ```powershell
    ./venv/Scripts/activate
    ```

4. Upgrade the virtual environment's pip

    ```powershell
    python -m pip install --upgrade pip
    ```

Now that the virtual environment is activated, time to install the dependencies

### Installing the dependencies

#### Python dependencies

Within the activated virtual environment's terminal do the following:

1. Install costumy's dependencies

    ```powershell
    python -m pip install -r requirements.txt
    ```

2. Install costumy itself in editable mode

    ```powershell
    python -m pip install -e .
    ```

3. **Optional but recommended**  
  Install the documentation dependencies

    ```powershell
    python -m pip install -r requirements_docs.txt
    ```

#### Node.js modules

To install the Node.js dependencies, you may do the following :

1. Open a new terminal (or `deactivate` the venv)
2. Navigate to `costumy/node/`

    ```powershell
    cd costumy/node/
    ```

3. Install the node.js modules :

    ```powershell
    npm install
    ```

## Next Steps

> [!NOTE] Virtual Envrionment
> Once you are done installing Costumy, you must use the created virtual environment for costumy to work.

To use costumy at its best you should do the following :

- [build the docs](Dev/docs.md) as they are intended to be seen as a static site  
- If you want to use `costumy.bodies.SMPL` or `costumy.bodies.Cmorph`, [install them](#installing-bodies-blender-addons)

## Installing Bodies (Blender Addons)

This sections explains how to install bodies for costumy.

> [!WARNING]  
> Bodies are not included with costumy.  
> They are optionnal and fall under different licences.
> See [Limitations](About/limitations.md) and [Licences](About/licenses.md).

### Mb-Lab (Cmorph)

Quote from [MB-Lab models licence](https://mb-lab-docs.readthedocs.io/en/latest/license.html):  
> The AGPL can be an obstacle in case someone wants to create a closed source game or closed source 3D models using 3D characters made with the lab because the AGPL will propagate from the base models and from the database to the output models.

To use [MB-Lab](https://github.com/animate1978/MB-Lab) models, you can follow the steps below:

1. Download the [CharMorph v0.3.5](https://github.com/Upliner/CharMorph/releases/tag/v0.3.5) Add-on.
2. Unzip the Add-on and open it
3. Copy the `CharMorph` folder and paste it in `costumy/data/addons`

There should now be a file located at `costumy/data/addons/CharMorph/__init__.py`

### SMPL

Quote from [SMPL model licence](https://smpl.is.tue.mpg.de/modellicense.html):  
> Licensor grants you (Licensee) personally a single-user, non-exclusive, non-transferable, free of charge right:
>
> - To install the Software on computers owned, leased or otherwise controlled by you and/or your organization;
> - To use the Software for the sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects;
> - To modify, adapt, translate or create derivative works based upon the Software.
>  
> Any other use, in particular any use for commercial purposes, is prohibited.

To use the [SMPL](https://smpl.is.tue.mpg.de/) bodies:

1. Create an account on the [SMPL website](https://smpl.is.tue.mpg.de/) (free)
2. Download the [blender Add-on](https://smpl.is.tue.mpg.de/download.php)
3. Unzip the Add-on and open it
4. Copy the `smpl_blender_addon` folder and paste it in `costumy/data/addons`
5. Open the file `costumy/data/addons/smpl_blender_addon\__init__.py` with a text editor
6. Change the line 371 from

    ```python
    vertices_np = np.zeros((len(mesh_from_eval.vertices)*3), dtype=np.float)
    ```

    to

    ```python
    vertices_np = np.zeros((len(mesh_from_eval.vertices)*3), dtype=float)
    ```

7. Save your changes

If you did it right, there should be a file located at `costumy/data/addons/smpl_blender_addon/__init__.py`

---
