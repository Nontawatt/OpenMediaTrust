# OpenMediaTrust – C2PA Toolkit

This project aims to build an accessible **C2PA** toolkit within the `OpenMediaTrust` folder. The goal is to make it easy for journalists, creators and everyday users to work with [Content Credentials](https://c2pa.org/), based on the **Coalition for Content Provenance and Authenticity (C2PA)** standard.

## Overview

The C2PA standard defines a way to attach cryptographically signed metadata (a *manifest*) to an image, video or audio file. This metadata can record who created the asset, what modifications were made, and other claims about its provenance. Tools like the official [c2patool](https://opensource.contentauthenticity.org/docs/c2patool/) and the [c2pa‑python library](https://opensource.contentauthenticity.org/docs/c2pa-python/) allow developers to work with these manifests – read them, validate their signatures and create new ones.

While these tools are powerful, they are often designed for developers or command‑line users. **OpenMediaTrust** builds on these foundations to offer a simpler interface for common tasks:

* **Verify content** – quickly check if a media file contains a valid C2PA manifest and view a human‑readable summary of its claims.
* **Read detailed metadata** – access a low‑level report of the manifest data for auditing or debugging.
* **Sign your own media** – create and attach C2PA manifests to photos, videos and audio, using a simple configuration file or interactive prompts. Supported signing algorithms and assertions are provided by the c2pa‑python library.
* **Add assertions** – include custom claims such as “Do Not Train” or licensing information when signing your assets.

## Getting Started

### Prerequisites

* **Python 3.10+** – the toolkit is built on the `c2pa` Python package, which requires Python 3.10 or later.
* **c2pa‑python** – install via pip:

```
bash
pip install c2pa-python
```

### Installation

1. Clone or download the `OpenMediaTrust` repository.
2. Navigate into the `C2PA` subfolder (to be created) and install dependencies:

```
bash
cd OpenMediaTrust/C2PA
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

   The `requirements.txt` file should list `c2pa-python` and any other dependencies required by this project.

### Usage

Below are some common operations provided by this toolkit. The actual command‑line interface may evolve as development continues.

#### Verify a media file

```
bash
python c2pa_toolkit.py verify path/to/file.jpg
```

This command reads the C2PA manifest (if present) and prints a summary of its claims and signature status.

#### Read full manifest data

```
bash
python c2pa_toolkit.py report path/to/file.mp4
```

Generates a detailed JSON report of all metadata contained in the manifest.

#### Sign a file with a manifest

```
bash
python c2pa_toolkit.py sign \
  --input path/to/source.png \
  --output path/to/signed.png \
  --assertions manifest.yml
```

Creates a new C2PA manifest for `source.png`, attaching it to a copy (`signed.png`). The `manifest.yml` file contains the assertions you want to include (creator identity, description, “Do Not Train” flag, etc.). The tool uses the c2pa‑python library to sign the manifest and embed it into the media file.

### Example assertion file (`manifest.yml`)

```yaml
title: "Sunset Photograph"
creator: "Jane Doe"
assertions:
  - label: c2pa.did
    value: "did:example:123456789abcdef"
  - label: c2pa.usage.do_not_train
    value: true
```

## Roadmap

The initial version of the toolkit will focus on verifying and signing image files. Planned improvements include:

1. **Support for additional media types** – video and audio formats supported by the underlying c2pa‑python library.
2. **Simple GUI** – a cross‑platform desktop interface for users who prefer not to use the command line.
3. **Integration with OpenMediaTrust services** – automatic upload of signed assets to the OpenMediaTrust platform, enabling provenance and authenticity tracking.

## Contributing

Contributions are welcome! If you have ideas or find issues, please open an issue or pull request. You can also refer to the [official c2patool documentation](https://opensource.contentauthenticity.org/docs/c2patool/) for advanced usage and compare with this project’s simplified approach.

## License

This project adopts the same dual licensing model (Apache 2.0 and MIT) as the underlying c2pa‑python library. See the `LICENSE` file for more details.
