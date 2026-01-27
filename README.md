# Spectral Line Finder

A simple tool to browse, filter and visualize atomic spectral line data in the terminal, built using the awesome [Textual](https://textual.textualize.io/) library. The data is retrieved from the [NIST atomic spectra database](https://physics.nist.gov/PhysRefData/ASD/lines_form.html) and cached on disk. Since the [Trump administration defunded](https://www.npr.org/2025/03/26/nx-s1-5340687/trump-cuts-nist-atomic-spectra-lab-advanced-chips-medical-devices) [the entire atomic spectroscopy group at NIST](https://howonearthradio.org/archives/10056) in 2025 we can only hope this data remains available to scientists. There is [some hope](https://www.callabmag.com/nist-group-finds-new-home/), after all.


## Usage

To run this application, use uv

```sh
uvx spectral-line-finder
```

or install this package from PyPI.

The filter dialog allows for selecting one or multiple elements and filtering the data based on ionization stage, observed wavelength, relative intensity, or the initial and final energy levels. Once filtered, the data is displayed in a table but the (filtered) spectrum can also be visualized in a spectrum plot.


## Screenshots

