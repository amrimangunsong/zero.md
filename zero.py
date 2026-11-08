#!/usr/bin/env python3
"""
zero.md: Zero-bloat, ultra-lightweight native Markdown viewer for Linux.
Built with Python 3, GTK3, WebKit2, Markdown-it, and Pygments.
Zero heavy runtimes (no Electron, no Qt6, no Pandoc).
"""

import sys
import os
import argparse
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, Gdk, GLib

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

VERSION = "0.1.0"

def highlight_code(code, lang, attrs):
    try:
        lexer = get_lexer_by_name(lang) if lang else TextLexer()
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)

md_parser = MarkdownIt("commonmark", {"highlight": highlight_code, "html": True})
md_parser.enable(["table", "strikethrough"])

PYGMENTS_LIGHT = HtmlFormatter(style="friendly").get_style_defs("pre code")
PYGMENTS_DARK = HtmlFormatter(style="monokai").get_style_defs("pre code")

CSS_TEMPLATE = f"""
:root {{
  color-scheme: light dark;
  --bg-color: #ffffff;
  --text-color: #1f2328;
  --border-color: #d1d9e0;
  --code-bg: #f6f8fa;
  --quote-color: #0969da;
  --table-alt: #f6f8fa;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg-color: #0d1117;
    --text-color: #e6edf3;
    --border-color: #30363d;
    --code-bg: #161b22;
    --quote-color: #2f81f7;
    --table-alt: #161b22;
  }}
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  line-height: 1.6;
  padding: 36px 48px;
  max-width: 920px;
  margin: 0 auto;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-size: 15px;
}}

h1, h2, h3, h4, h5, h6 {{
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}}

h1 {{ font-size: 2em; padding-bottom: 0.3em; border-bottom: 1px solid var(--border-color); }}
h2 {{ font-size: 1.5em; padding-bottom: 0.3em; border-bottom: 1px solid var(--border-color); }}
h3 {{ font-size: 1.25em; }}

p {{ margin-top: 0; margin-bottom: 16px; }}

a {{ color: #0969da; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
@media (prefers-color-scheme: dark) {{
  a {{ color: #4493f8; }}
}}

code {{
  font-family: "JetBrains Mono", "Fira Code", monospace, Consolas, "Liberation Mono";
  font-size: 85%;
  background-color: var(--code-bg);
  padding: 0.2em 0.4em;
  border-radius: 4px;
}}

pre {{
  font-family: "JetBrains Mono", "Fira Code", monospace, Consolas, "Liberation Mono";
  font-size: 85%;
  background-color: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
  line-height: 1.45;
}}

pre code {{
  background: none;
  padding: 0;
  font-size: 100%;
}}

blockquote {{
  margin: 0 0 16px 0;
  padding: 0 1em;
  color: var(--text-color);
  opacity: 0.85;
  border-left: 0.25em solid var(--quote-color);
}}

table {{
  border-spacing: 0;
  border-collapse: collapse;
  margin-top: 0;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
}}

th, td {{
  padding: 8px 14px;
  border: 1px solid var(--border-color);
}}

th {{
  font-weight: 600;
  background-color: var(--code-bg);
}}

tr:nth-child(2n) {{
  background-color: var(--table-alt);
}}

hr {{
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: var(--border-color);
  border: 0;
}}

img {{
  max-width: 100%;
  box-sizing: border-box;
  border-radius: 6px;
}}

ul, ol {{
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}}

li + li {{
  margin-top: 0.25em;
}}

/* Pygments Syntax Highlighting */
{PYGMENTS_LIGHT}

@media (prefers-color-scheme: dark) {{
  {PYGMENTS_DARK}
}}
"""

class ZeroMDViewer(Gtk.Window):
    def __init__(self, filepath=None):
        super().__init__(title="zero.md")
        self.set_default_size(880, 720)
        self.filepath = os.path.abspath(filepath) if filepath else None
        self.current_zoom = 1.0

        # HeaderBar / Window Controls
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        self.set_titlebar(header)
        self.header = header

        open_btn = Gtk.Button.new_from_icon_name("document-open", Gtk.IconSize.BUTTON)
        open_btn.set_tooltip_text("Open File (Ctrl+O)")
        open_btn.connect("clicked", self.on_open_clicked)
        header.pack_start(open_btn)

        reload_btn = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
        reload_btn.set_tooltip_text("Reload (Ctrl+R / F5)")
        reload_btn.connect("clicked", lambda b: self.load_content())
        header.pack_start(reload_btn)

        print_btn = Gtk.Button.new_from_icon_name("document-print", Gtk.IconSize.BUTTON)
        print_btn.set_tooltip_text("Print / Export to PDF (Ctrl+P)")
        print_btn.connect("clicked", lambda b: self.print_document())
        header.pack_start(print_btn)

        zoom_out_btn = Gtk.Button.new_from_icon_name("zoom-out", Gtk.IconSize.BUTTON)
        zoom_out_btn.set_tooltip_text("Zoom Out (Ctrl -)")
        zoom_out_btn.connect("clicked", lambda b: self.change_zoom(-0.1))
        header.pack_end(zoom_out_btn)

        zoom_in_btn = Gtk.Button.new_from_icon_name("zoom-in", Gtk.IconSize.BUTTON)
        zoom_in_btn.set_tooltip_text("Zoom In (Ctrl +)")
        zoom_in_btn.connect("clicked", lambda b: self.change_zoom(0.1))
        header.pack_end(zoom_in_btn)

        # WebKit View
        self.view = WebKit2.WebView()
        self.view.connect("decide-policy", self.on_navigation)

        scroller = Gtk.ScrolledWindow()
        scroller.add(self.view)
        self.add(scroller)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.load_content()

    def on_navigation(self, web_view, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if uri.startswith("http://") or uri.startswith("https://"):
                decision.ignore()
                Gtk.show_uri_on_window(self, uri, Gdk.CURRENT_TIME)
                return True
        return False

    def load_content(self):
        if self.filepath and os.path.exists(self.filepath):
            filename = os.path.basename(self.filepath)
            self.header.set_title(filename)
            self.header.set_subtitle(self.filepath)
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_md = f.read()
            base_dir = os.path.dirname(self.filepath)
            base_uri = f"file://{base_dir}/"
        else:
            self.header.set_title("zero.md")
            self.header.set_subtitle("No file loaded")
            raw_md = "# zero.md\n\nNo file loaded.\n\nOpen a Markdown file with **Ctrl+O** or run:\n\n```bash\nzero.md filename.md\n```"
            base_uri = "file:///"

        rendered_html = md_parser.render(raw_md)
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{CSS_TEMPLATE}
</style>
</head>
<body>
{rendered_html}
</body>
</html>"""
        self.view.load_html(full_html, base_uri)

    def print_document(self):
        print_op = WebKit2.PrintOperation.new(self.view)
        print_op.run_dialog(self)

    def change_zoom(self, delta):
        self.current_zoom = max(0.4, min(3.0, self.current_zoom + delta))
        self.view.set_zoom_level(self.current_zoom)

    def reset_zoom(self):
        self.current_zoom = 1.0
        self.view.set_zoom_level(self.current_zoom)

    def on_key_press(self, widget, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)

        if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval in (Gdk.KEY_w, Gdk.KEY_q)):
            Gtk.main_quit()
            return True
        elif event.keyval == Gdk.KEY_F5 or (ctrl and event.keyval == Gdk.KEY_r):
            self.load_content()
            return True
        elif ctrl and event.keyval == Gdk.KEY_p:
            self.print_document()
            return True
        elif ctrl and event.keyval in (Gdk.KEY_plus, Gdk.KEY_equal):
            self.change_zoom(0.1)
            return True
        elif ctrl and event.keyval == Gdk.KEY_minus:
            self.change_zoom(-0.1)
            return True
        elif ctrl and event.keyval == Gdk.KEY_0:
            self.reset_zoom()
            return True
        elif ctrl and event.keyval == Gdk.KEY_o:
            self.on_open_clicked(None)
            return True
        return False

    def on_open_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Open Markdown File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown files (*.md, *.markdown)")
        filter_md.add_mime_type("text/markdown")
        filter_md.add_mime_type("text/x-markdown")
        filter_md.add_pattern("*.md")
        filter_md.add_pattern("*.markdown")
        dialog.add_filter(filter_md)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.filepath = dialog.get_filename()
            self.load_content()
        dialog.destroy()

def main():
    parser = argparse.ArgumentParser(description="zero.md — Zero-bloat native Markdown viewer for Linux")
    parser.add_argument("file", nargs="?", help="Path to markdown file")
    parser.add_argument("-v", "--version", action="version", version=f"zero.md {VERSION}")
    args = parser.parse_args()

    app = ZeroMDViewer(args.file)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
