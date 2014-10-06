#!/usr/bin/python
# -*- coding: utf-8 -*-

# later:
# [ ] color highlighter plugin issue (global bg is not always first plist_file["settings"][0]["settings"])
# [ ] issue regarding finding themes inside zipped packages

# Settings
# - label_color (ligh, dark)
# - sidebar_bg_brightness_change
# - side_bar_sep_line_brightness_change
# - enabled
# - ignored_syntaxes, ignored_themes

# Caveats:
# - not working well with multiple windows, sidebar change globally
# - when the syntax is changed by user it should react

import sublime, sublime_plugin
import codecs, json
from os import path
from plistlib import readPlist


class SidebarMatchColorScheme(sublime_plugin.EventListener):

    def on_activated_async(self, view):
        global cache
        scheme_file = view.settings().get('color_scheme')
        if scheme_file == cache.get('color_scheme'):
            return

        syntax = view.settings().get('syntax')
        # do not change side bar for special syntaxes like vintagous-commandline-mode
        if syntax and (syntax.endswith("VintageousEx Cmdline.tmLanguage") or syntax.endswith("TestConsole.tmLanguage")):
            return
        color_scheme = path.normpath(scheme_file)
        path_packages = sublime.packages_path()
        plist_path = path_packages + color_scheme.replace('Packages', '')
        # print('THEME ==> ' + plist_path)
        # print('SYNTX ==> ' + syntax)
        if plist_path and plist_path.endswith("Widgets.stTheme"):
            # print('ignored ' + plist_path)
            return

        plist_file = readPlist(plist_path)
        global_settings = [i["settings"] for i in plist_file["settings"] if i["settings"].get("lineHighlight")]
        color_settings = global_settings[0]

        bg = color_settings.get("background", '#FFFFFF')
        fg = color_settings.get("foreground", '#000000')

        cache = {
            "bg": bg,
            "fg": fg,
            "color_scheme": scheme_file
        }
        # print("Updating sidebar BG to", cache)

        _NUMERALS = '0123456789abcdefABCDEF'
        _HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}

        def rgb(triplet):
            return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]

        def is_light(triplet):
            r, g, b = _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]
            yiq = ((r*299)+(g*587)+(b*114))/1000;
            return yiq >= 128

        def color_variant(hex_color, brightness_offset=1):
            """ takes a color like #87c95f and produces a lighter or darker variant """
            if len(hex_color) == 9:
                print("=> Passed %s into color_variant()" % hex_color)
                hex_color = hex_color[0:-2]
                print("=> Reformatted as %s " % hex_color)
            if len(hex_color) != 7:
                raise Exception("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
            rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
            new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
            new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int] # make sure new values are between 0 and 255
            return "#%02x%02x%02x" % tuple(new_rgb_int)

        def label_color(triplet):
            if is_light(triplet):
                return [30, 30, 30]
            else:
                return [220, 220, 220]

        def side_bar_sep_line(bg):
            if is_light(bg.lstrip('#')):
                return rgb(color_variant(bg,-50).lstrip('#'))
            else:
                return rgb(color_variant(bg,50).lstrip('#'))

        # darken/lighten sidebar by a percentage
        def bg_variat(bg):
            if sidebar_bg_variant == 0:
                return rgb(bgc)
            else:
                return rgb(color_variant(bg,sidebar_bg_variant).lstrip('#'))

        bgc = bg.lstrip('#')

        template = [
            {
                "class": "tree_row",
                "layer0.texture": "Theme - Default/row_highlight_dark.png",
                "layer0.tint": side_bar_sep_line(bg),
            },
            {
                "class": "sidebar_container",
                "layer0.tint": side_bar_sep_line(bg),
                "layer0.opacity": 1.0,
            },
            {
                "class": "sidebar_tree",
                "layer0.tint": bg_variat(bg),
                "layer0.opacity": 1,
                "dark_content": not is_light(bgc)
            },
            {
                "class": "sidebar_label",
                "color": label_color(bgc),
            },
            {
                "class": "sidebar_heading",
                "shadow_offset": [0, 0]
            }
        ]

        json_str = json.dumps(template, sort_keys=True, indent=4, separators=(',', ': ')).encode('raw_unicode_escape')
        new_theme_file_path = path_packages + "/User/" + view.settings().get('theme')
        with codecs.open(new_theme_file_path, 'w', 'utf-8') as f:
            f.write(json_str.decode())


def plugin_loaded():
    global cache
    global sidebar_bg_variant
    cache = {}
    sidebar_bg_variant = 0