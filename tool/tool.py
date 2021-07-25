import yaml
import os
import argparse
import re
import sys

def load_rime_dict(path, code2word, word2code):
    line_pattern = re.compile(r"^(.*?)\s+(.*?)\s*(\d*)\s*$")
    try:
        f = open(path, 'r')
        file_content = f.read()
        file_split = file_content.split("...")
        _file_config = file_split[0]
        file_dict = file_split[1]
        file_line = file_dict.splitlines()
        for l in file_line:
            m = line_pattern.match(l)
            if m:
                word = m.group(1)
                code = m.group(2)
                if word and code:
                    code2word[code] = code2word.get(code, [])
                    code2word[code].append(word)
                    word2code[word] = code2word.get(word, [])
                    word2code[word].append(code)
                    word2code[word] = sorted(word2code[word]) 
    except Exception as e:
        print("load table {} ocurred error skip.{}".format(path, e), 
                file=sys.stderr)
    finally:
        if f is not None and not f.closed:
            f.close()

def load_rime(path):
    config_base_dir = os.path.abspath(os.path.dirname(path))
    config = None
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    tables = config["import_tables"]
    code2word = dict()
    word2code = dict()
    for t in tables:
        load_rime_dict(os.path.join(config_base_dir, t +
                       '.dict.yaml'), code2word, word2code)
    return code2word, word2code


def rime2zf(path):
    code2word, word2code = load_rime(path)
    sorted_keys = sorted(code2word.keys())
    return ["{} {}".format(k, " ".join(code2word[k])) for k in sorted_keys]


def output(out, out_path, outstd):
    out_file = None
    if out_path is not None:
        out_file = open(out_path, 'w')
    for k in out:
        if out_file is not None:
            out_file.write(k + '\n')
        if outstd:
            print(k, file=sys.stdout)
    if out_file is not None and not out_file.closed:
        out_file.close()

    print("{} records converted. write to {}".format(
        len(out), out_path or 'stdout' if outstd else None), file=sys.stderr)


def convert(parser, args):
    result = None
    if getattr(args, 'from') == 'rime' and getattr(args, 'to') == 'zf':
        result = rime2zf(args.input)
    
    if result is not None:
        output(result, args.output, args.outstd)

def create_arg_parser():
    parser = argparse.ArgumentParser(description='build tool.')

    subparsers = parser.add_subparsers(metavar="COMMAND", dest='command')
    # convert
    parser_convert = subparsers.add_parser(
        'convert', aliases=['conv'], help='convert dict file')
    parser_convert.set_defaults(func=convert)
    parser_convert.add_argument('from', metavar='FROM', type=str, choices=['rime'],
                                default='rime', help='from format. options: rime. ')
    parser_convert.add_argument('to', metavar='TO', type=str, choices=['zf'],
                                default='zf', help='to format. options: zf. ')
    parser_convert.add_argument('-i', '--input', dest='input', type=str, default='openfly.dict.yaml',
                                action='store', help='input file')

    parser_convert.add_argument('-o', '--output', dest='output', type=str, default=None,
                                action='store', help='output file')
    parser_convert.add_argument('-outstd', '--output-std', dest='outstd', default=False,
                               action='store_true', help='output stdout')

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
