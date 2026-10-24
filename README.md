# Price3D

Price3D is a small interactive command-line calculator for estimating the cost
of an FDM/resin 3D print and setting a selling price. It uses only the Python
standard library.

## Features

- Estimate filament weight from slicer grams or model volume and infill.
- Include material, electricity, printer depreciation, maintenance, labor,
  finishing supplies, packaging, shipping, design, and failed-print reserves.
- Compare personal printing cost with a similar store-bought item.
- Calculate break-even and Budget, Recommended, and Premium prices after sales
  fees, royalties, and VAT.
- Set a minimum profit per print hour; the Recommended tier targets whichever
  is greater: the requested profit per unit or the hourly profit target.
- Fetch exchange rates and optional material prices at startup, with cached and
  built-in defaults for offline use.
- Save a plain-text report.

## Requirements

- Python 3.10 or newer
- Internet access is optional. Without it, the calculator uses built-in or
  previously cached data.

## Run

Open a terminal in the project folder and run:

```text
python Price3D.py
```

On Windows, `py Price3D.py` is also commonly available. Follow the prompts and
press Enter to accept a value shown in brackets. Choose the personal-use mode
for a cost estimate, or selling mode to account for fees and target profit.

Run the automated tests with:

```text
python -m unittest discover -v
```

## Build a Windows executable

Price3D is a Python program, so it does not need to be compiled to run. To
create a standalone Windows `.exe`, open PowerShell in the project folder and
run:

```powershell
pip install pyinstaller
PyInstaller --clean --onefile --name Price3D --icon=icon.ico Price3D.py
```

The executable will be created at `dist\Price3D.exe`. Run it from a folder
where it can create its local `config.json` and `cache.json` files. Internet
access is still optional; exchange rates can use cached or built-in defaults.

## Notes

- Built-in material prices, electricity costs, printer lifetime, marketplace
  fees, and other defaults are examples. Check and adjust them for your own
  equipment, location, and sales channel.
- Estimates depend on the values entered and are not tax, accounting, or
  marketplace-fee advice.
- This project currently has no license file. Add a license only after choosing
  the terms you want to apply to the project.
