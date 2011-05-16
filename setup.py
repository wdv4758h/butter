#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

try:
	MODULE_NAME = find_packages()[0]
	PROGRAM_NAME = MODULE_NAME
except IndexError:
	print "No packages found, set MODULE_NAME manually"
	sys.exit(1)

# Set some sane defaults here
version = "0.1"
email = "code@pocketnix.org"
author = "Da_Blitz"
license = "BSD 3 Clause"
description = ""
url = "http://code.pocketnix.org"
tags = ""
test_suite = PROGRAM_NAME

if MODULE_NAME.endswith(".py"):
	MODULE_NAME = MODULE_NAME[:-3]

args = {}
try:
	module = __import__(MODULE_NAME)
	args["version"] = getattr(module, "__version__", version)
	args["email"] = getattr(module, "__email__", email)
	args["author"] = getattr(module, "__author__", author)
	args["license"] = getattr(module, "__license__", license)
	new_description = getattr(module, "__doc__", description)
	if ":" in new_description:
		description = new_description.split("/n")[0].split(":", 2)[1].strip()
	args["description"] = description
	args["url"] = getattr(module, "__url__", url)
	args["tags"] = getattr(module, "__tags__", tags)
	args["test_suite"] = getattr(module, "__tests__", test_suite)
except ImportError:
	pass

readme = ""
for name in ("README", "README.rst"):
	try:
		readme = open(name).read()
	except (OSError, IOError):
		continue
	else:
		break

args["long_description"] = readme

entry_points = {}
#entry_points = {"entrypoint.plugins":["plugin_name=module.submodule:function",
#									"plugin_name=module.submodule:class"]}
# Must be a callable
#entry_points["console_scripts"] = ["cmdline-app=module.utils:main"]

if __name__ == "__main__":
	setup(name = PROGRAM_NAME, packages = [MODULE_NAME],
			entry_points = entry_points, **args)
