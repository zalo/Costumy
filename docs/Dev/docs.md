# Bulding Docs

This page explains how to read costumy's docs as a beautifull website.  
Otherwise you can still read the docs with plain markdown but it will not be fun.

## Installation

> [!NOTE]
> Costumy must be installed before following the instruction on this page.

## Serve

To have a local version in your web browser you can do:

1. Activate the virtual environment made during costumy's installation :

    ```powershell
    ./venv/Scripts/activate
    ```

    **If you have not installed the docs requirements already**, you may do:

    ```powershell
    python -m pip install -r requirements_docs.txt
    ```

2. Serve the documentation site locally using :

    ```powershell
    mkdocs serve
    ```

3. Open the url printed in the terminal in your web browser

    ```text
    INFO - [14:00:00] Serving on <url>
    ```

You can now enjoy this very nice documentation locally, as long as your terminal is serving it.  

You can interput the process or close the terminal to stop.
