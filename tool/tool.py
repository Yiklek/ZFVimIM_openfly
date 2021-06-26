import yaml
import os
import argparse
import re
import sys


def openfly(in_path, out_path):
    path = in_path
    out_path = os.path.abspath(out_path)
    config_base_dir = os.path.abspath(os.path.dirname(path))
    line_pattern = re.compile(r"^(.*?)\s+(.*?)\s*(\d*)\s*$")
    config = None
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    tables = config["import_tables"]
    all_word_dict = dict()
    for t in tables:
        try:
            f = open(os.path.join(config_base_dir, t+'.dict.yaml'), 'r')
            file_content = f.read()
            file_split = file_content.split("...")
            file_config = file_split[0]
            file_dict = file_split[1]
            file_line = file_dict.splitlines()
            for l in file_line:
                m = line_pattern.match(l)
                if m:
                    word = m.group(1)
                    code = m.group(2)
                    if word and code:
                        all_word_dict[code] = all_word_dict.get(code, [])
                        all_word_dict[code].append(word)
        except Exception as e:
            print("convert table {} ocurred error skip.{}", t, e)
        finally:
            if f is not None and not f.closed:
                f.close()
    sorted_keys = sorted(all_word_dict.keys())
    output = open(out_path, 'w')
    for k in sorted_keys:
        output.write("{} {}\n".format(k, " ".join(all_word_dict[k])))
    output.close()
    print("{} records converted. write to {}".format(
        len(all_word_dict), out_path))


def build(parser, args):
    if getattr(args, 'from') == 'openfly':
        openfly(args.input, args.output)


def create_arg_parser():
    parser = argparse.ArgumentParser(description='build tool.')
    subparsers = parser.add_subparsers(metavar="COMMAND", dest='command')
    # install
    parser_install = subparsers.add_parser(
        'build', aliases=['b'], help='build db file')
    parser_install.set_defaults(func=build)
    parser_install.add_argument('from', metavar='FROM', type=str, choices=['openfly'],
                                default='openfly', help='from format. options: openfly. ')
    parser_install.add_argument('-i', '--input', dest='input', type=str, default='openfly.dict.yaml',
                                action='store', help='input file')

    parser_install.add_argument('-o', '--output', dest='output', type=str, default='openfly.txt',
                                action='store', help='output file')

    return parser


def main(args):
    parser = create_arg_parser()
    arg = parser.parse_args(args)
    if arg.command is None:
        parser.print_help()
    else:
        arg.func(parser, arg)


if __name__ == "__main__":
    main(sys.argv[1:])
