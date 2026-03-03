# pingtray

A macOS menu-bar app that shows your internet connectivity status using [AnyBar][anybar].

- **filled** — connected
- **exclamation** — no connection

## Install dependencies

```bash
brew install uv # or other python package runner like pipx
brew install --cask anybar
```

## Usage

```bash
uvx pingtray
```

## Configuration

Create `~/.config/pingtray/config.toml` (all keys optional):

```toml
target        = "1.1.1.1"
interval      = 1.0
anybar_binary = "/Applications/AnyBar.app/Contents/MacOS/AnyBar"
log_level     = "WARNING"   # DEBUG, INFO, WARNING, ERROR
```

[anybar]: https://github.com/tonsky/AnyBar
