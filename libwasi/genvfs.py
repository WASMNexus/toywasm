from enum import Enum
import re
import sys

re_name_str = '[a-z][_a-z0-9]*$'
re_name = re.compile(re_name_str)

re_path_info_str = f'struct path_info \*({re_name_str})'
re_path_info = re.compile(re_path_info_str)

filename = "wasi_vfs.def"

class Mode(Enum):
    VfsPrototype = 1,
    VfsStructDecl = 2,
    VfsStructDefine = 3,
    VfsDefine = 4,

f = open(filename, "r")
content = f.read()
content = content.replace("\n", "")
lines = content.split(";")

def process(mode, out, prefix="wasi_vfs_", qual="static const"):
    print("/* this file is generated by genvfs.sh */", file=out)
    print('#include "wasi_vfs_types.h"', file=out)
    if mode == Mode.VfsStructDecl:
        print("struct wasi_vfs_ops {", file=out)
    if mode == Mode.VfsStructDefine:
        print(f"{qual} struct wasi_vfs_ops {prefix}ops = {{", file=out)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line, _ = line.split(")")
        fn, args = line.split("(")
        args = args.split(",")
        args_sig = []
        for a in args:
            args_sig.append(a.strip())
        args_name = []
        for a in args:
            a = a.strip()
            m = re_name.search(a)
            args_name.append(m.group())
        path_info_arg = []
        for a in args:
            m = re_path_info.search(a)
            if m:
                path_info_arg.append(m.group(1))

        if mode == Mode.VfsStructDecl:
            print(f"\tint (*{fn})({', '.join(args_sig)});", file=out)
        elif mode == Mode.VfsStructDefine:
            print(f"\t.{fn} = {prefix}{fn},", file=out)
        elif mode == Mode.VfsPrototype:
            print(f"int {prefix}{fn}({', '.join(args_sig)});", file=out)
        elif mode == Mode.VfsDefine:
            print(f"int\nwasi_vfs_{fn}({', '.join(args_sig)})", file=out)
            print("{", file=out)
            if fn.startswith("path_"):
                for a in path_info_arg[1:]:
                    print(f"\tif (check_xdev({path_info_arg[0]}, {a})) {{", file=out)
                    print("\t\treturn EXDEV;", file=out)
                    print("\t}", file=out)
                print(f"\tconst struct wasi_vfs_ops *ops = path_vfs_ops({path_info_arg[0]});", file=out)
            else:
                print(f"\tconst struct wasi_vfs_ops *ops = fdinfo_vfs_ops(fdinfo);", file=out)
            print(f"\treturn ops->{fn}({', '.join(args_name)});", file=out)
            print("}", file=out)
    if mode == Mode.VfsStructDecl:
        print("};", file=out)
    if mode == Mode.VfsStructDefine:
        print("};", file=out)

with open("wasi_vfs_ops.h", "w") as fp:
    process(Mode.VfsStructDecl, fp)

with open("wasi_vfs.h", "w") as fp:
    process(Mode.VfsPrototype, fp);

with open("wasi_vfs_dispatch.h", "w") as fp:
    process(Mode.VfsDefine, fp)

#with open("wasi_vfs_impl_host.h", "w") as fp:
#    process(Mode.VfsPrototype, fp, prefix="wasi_host_")

#process(Mode.VfsStructDefine, sys.stdout, prefix="wasi_host_");