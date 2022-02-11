<div align="center">
<img src=".github/readme.png" height="100">

### Chef

A python script that takes care of all the knick-knacks in competitive programming

![License](https://img.shields.io/github/license/radiantly/chef?style=for-the-badge) ![Code style](https://img.shields.io/badge/code%20style-black-%23000000?style=for-the-badge)

</div>

### Features

- **Header precompilation:** In competitive programming, it is a common practice to include `bits/stdc++.h` which in turn includes all other headers. Precompiling this header shortens the compile time.

- **Source file generation from template:** When paired with the [Competitive Companion](https://github.com/jmerle/competitive-companion) extension, chef can generate the source file from a template with comments including the problem title, url, and the testcases and open it up with [VS Code](https://code.visualstudio.com/).

- **Compile & Run on save:** Your file is automatically compiled and run with the given inputs when saved.

- **Easy custom input:** Passing a new testcase to run is as easy as adding or changing a comment at the end of your source file.

- **Sane defaults:** For compilation, `g++` is used with flags to show a variety of warnings including out-of-bound memory access detection.

- **Colorful display:** Chef uses the ubiquitous [`rich`](https://github.com/Textualize/rich) library to spice your terminal output with nice colors.

- (Mostly) **Editor agnostic:** Chef does not tightly integrate with any editor, and the only interaction with an editor is opening the generated source file.

- **Supported on Arch Linux:** Chef works best when used on [Arch Linux](https://archlinux.org/) or [Arch Linux on WSL](https://github.com/yuk7/ArchWSL).

### Upcoming features

- Multiple language support
- Easier configuration

### Usage

Chef is best used with [Competitive Companion](https://github.com/jmerle/competitive-companion) and [VS Code](https://code.visualstudio.com/). Requires a recent version of Python 3.

```sh
# Install dependencies
pip install -r requirements.txt

# Run chef
python chef.py
```

### License

MIT

_Chef hat illustration by [Icons 8](https://icons8.com/illustrations/author/5c07e68d82bcbc0092519bb6) from [Ouch!](https://icons8.com/illustrations)_
