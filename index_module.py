# -*- coding: utf-8 -*-
import sublime
import os
import re

var_pattern = re.compile(r"^(\w+)\s*=")
fun_pattern = re.compile(r"^function\s*(\w+)\s*\(([\w,]*)\)")


indices = {} # path -> variables

def index_module(view, location, content):
	if len(indices) == 0:
		generate_indices()

	# find whole word
	pos = view.find_by_class(location, False, sublime.CLASS_WORD_START, " ")
	if pos <= 0: return None

	word = view.substr(sublime.Region(pos, location))
	names = word.split('.')
	if len(names) != 2: return None

	first_name = names[0]
	path = find_require_path(first_name, content)
	print("prefix", first_name, path)

	if path is None: return None

	return indices.get(path.replace("/", ".")), sublime.INHIBIT_WORD_COMPLETIONS

def generate_indices():
	window = sublime.active_window()
	for proj_data in window.project_data()["folders"]:
		proj_dir = proj_data["path"]
		lua_paths = proj_data.get("lua_paths", ("", ))
		for lpath in lua_paths:
			cur_path = os.path.join(proj_dir, lpath)
			if not os.path.exists(cur_path) or not os.path.isdir(cur_path):
				continue

			gen_indices_in_path(cur_path)

	return


def gen_indices_in_path(path):
	for root, dirs, files in os.walk(path):
		for fname in files:
			name, ext = os.path.splitext(fname)
			if ext != ".lua": continue

			key = os.path.relpath(root, path)
			key = key.replace('\\', '.').replace('/', '.')
			key += "." + name
			gen_indices_in_file(key, os.path.join(root, fname))

	return

def gen_indices_in_file(key, path):
	global indices

	ret = {}
	with open(path, "r", encoding="utf-8") as f:
		for line in f.readlines():
			match = var_pattern.match(line)
			if match:
				var = match.group(1)
				ret[var + "\tvariable"] = var
				continue

			match = fun_pattern.match(line)
			if match:
				var = match.group(1)
				args = match.group(2)
				ret[var + "\tfunction"] = var + "($0%s)" % args

	if len(ret) > 0:
		values = [[k, v] for k, v in ret.items()]
		values.sort(key = lambda x: x[1])
		indices[key] = values

	return

def find_require_path(name, content):
	pattern = r"""%s\s*=\s*require\s*\(?\s*["']([\w\.]+)""" % name
	match = re.search(pattern, content)
	return match.group(1) if match else None
