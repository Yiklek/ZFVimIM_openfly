import yaml
import os
import argparse
import re
import sys
from urllib.parse import urlparse
from copy import deepcopy
from functools import reduce

line_pattern = re.compile(r"^(.*?)\s+(.*?)$")
dup_pattern = re.compile(r"(.)\1{2,}")


def load_rime_dict(path, code2word=None, word2code=None):
    f = None
    if code2word is None:
        code2word = dict()

    if word2code is None:
        word2code = dict()

    try:
        f = open(path, 'r', encoding="utf-8")
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
                    word2code[word] = word2code.get(word, [])
                    word2code[word].append(code)
                    word2code[word] = sorted(word2code[word], key=lambda l: len(l))

    except Exception as e:
        print("load table {} ocurred error skip.{}".format(path, e),
                file=sys.stderr)
    finally:
        if f is not None and not f.closed:
            f.close()
    return code2word, word2code


def load_zf(path, code2word=None, word2code=None):
    f = None
    if code2word is None:
        code2word = dict()

    if word2code is None:
        word2code = dict()
    try:
        f = open(path, 'r')
        file_content = f.readlines()
        for l in file_content:
            m = line_pattern.match(l)
            if m:
                code = m.group(1)
                words = m.group(2) or ''
                for word in words.split(' '):
                    wrd_m = dup_pattern.match(word)
                    if code:
                        code2word[code] = code2word.get(code, [])
                        code2word[code].append(word)
                        word2code[word] = word2code.get(word, [])
                        word2code[word].append(code)
                        word2code[word] = sorted(word2code[word], key=lambda l: len(l))

    except Exception as e:
        print("load table {} ocurred error skip.{}".format(path, e),
                file=sys.stderr)
    finally:
        if f is not None and not f.closed:
            f.close()
    return code2word, word2code


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
        out_file = open(out_path, 'w', encoding="utf-8")
    # 1 is stdout, use utf-8
    with open(1, "w", encoding="utf-8") as stdout:
        for k in out:
            if out_file is not None:
                out_file.write(k + '\n')
            if outstd:
                print(k, file=stdout, flush=True)
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

# 一简字补充双拼
def fix_openfly_code(word2code):
    # 少量需要调整，暂时写在代码里
    w2c = {
            '去':'quts',
            '我':'wopd',
            '二':'eraa',
            '人':'rfpn',
            '他':'tary',
            '一':'yiaa',
            '是':'uior',
            '出':'iuvk',
            '哦':'ookw',
            '平':'pkau',
            '啊':'aakk',
            '三':'sjae',
            '的':'debu',
            '的':'debu',
            '非':'fwla',
            '个':'gerl',
            '和':'hehk',
            '就':'jqwy',
            '可':'kedk',
            '了':'levl',
            '在':'zdut',
            '小':'xnld',
            '才':'cdap',
            '这':'vezw',
            '不':'buad',
            '你':'nirx',
            '没':'mwdy',
            '万':'wjap',
            '识':'uiyb',
            '叶':'yeku',
            }
    for k,v in w2c.items():
        word2code[k].insert(0, v)

def openfly(base, source, extra=False):
    base = urlparse(base)
    source = urlparse(source)
    if base.scheme not in ['rime', 'zf']:
        print("base scheme not support.", file=sys.stderr)
        return
    if source.scheme not in ['rime', 'zf']:
        print("source scheme not support.", file=sys.stderr)
        return

    base_loader = None
    if base.scheme == 'rime':
        base_loader = load_rime
    elif base.scheme == 'zf':
        base_loader = load_zf
    print("load base dict...", file=sys.stderr)
    base_c2w, base_w2c = base_loader(os.path.expanduser(base.netloc + base.path))
    fix_openfly_code(base_w2c)

    print("load source dict...", file=sys.stderr)
    source_path = os.path.expanduser(source.netloc + source.path)
    src_loader = None
    if source.scheme == 'rime':
        src_loader = load_rime_dict
    elif source.scheme == 'zf':
        src_loader = load_zf
    src_c2w, src_w2c = src_loader(source_path)

    result = []
    result_c2w = dict()
    result_w2c = dict()

    def append(code, word):
        # 该编码原来只有一个候选略过，保证原始四码上屏
        # 且基础词库未收录
        if (base_c2w.get(code) is None or len(base_c2w[code]) != 1) \
                                        and base_w2c.get(word) is None:
            result.append("{}\t{}".format(word, code))
            result_c2w[code] = result_c2w.get(code) or deepcopy(base_c2w.get(code, []))
            result_c2w[code].append(word)
            result_w2c[word] = result_w2c.get(word) or deepcopy(base_w2c.get(word, []))
            result_w2c[word].append(code)

    def w2c(word):
        code = base_w2c[word]
        for c in code:
            if len(c) > 1 and not c.startswith('ob'):
                return c
        raise KeyError(word)

    for word in src_w2c.keys():
        try:
            wrd_m = dup_pattern.match(word)
            if wrd_m:
                continue

            if len(word) == 1:
                continue
            elif len(word) == 2:
                code = w2c(word[0])[0:2] + w2c(word[1])[0:2]
            elif len(word) == 3:
                code = w2c(word[0])[0:1] + w2c(word[1])[0:1] + w2c(word[2])[0:2]
            else:
                code = w2c(word[0])[0:1] + w2c(word[1])[0:1] + w2c(word[2])[0:1] + w2c(word[-1])[0:1]
                # extra code
                if extra:
                    code_extra = "".join([w2c(i)[0] for i in word])
                    if code_extra != code:
                        append(code_extra, word)
        except KeyError as e:
            print("no code for {}.".format(str(e)), file=sys.stderr)
            continue

        append(code, word)

    sorted_c2w_val = sorted(result_c2w.values(), key=lambda l: len(l), reverse=True)
    sorted_w2c_val = sorted(result_w2c.values(), key=lambda l: len(l), reverse=True)
    sum_code_dup = reduce(lambda x, y: x + len(y), sorted_c2w_val, 0)
    print("code max duplication: {} {} \nave: {}".format(len(sorted_c2w_val[0]), sorted_c2w_val[0], sum_code_dup/len(sorted_c2w_val)), file=sys.stderr)
    print("word max duplication: {} {}".format(len(sorted_w2c_val[0]), sorted_w2c_val[0]), file=sys.stderr)

    return result

def build(parser, args):
    result = None
    if getattr(args, 'target') == 'openfly_extra':
        result = openfly(args.base, args.input, True)
    elif getattr(args, 'target') == 'openfly':
        result = openfly(args.base, args.input, False)

    if result is not None:
        output(result, args.output, args.outstd)

def create_arg_parser():
    parser = argparse.ArgumentParser(description='build tool.')

    subparsers = parser.add_subparsers(metavar="COMMAND", dest='command')
    # convert
    parser_convert = subparsers.add_parser(
        'convert', aliases=['conv'], help='convert format of dict file')
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
    # build
    parser_build = subparsers.add_parser(
        'build', aliases=['b'], help='build target dict based on the specified dict code')
    parser_build.set_defaults(func=build)
    build_target = ['openfly', 'openfly_extra']
    parser_build.add_argument('target', metavar='TARGET', type=str, choices=build_target,
                                default='openfly_extra', help='target. options: {} '.format(", ".join(build_target)))
    parser_build.add_argument('base', metavar='BASE', type=str, action='store',
            help='base dict. support scheme: rime. example: rime://openfly.dict.yaml')
    parser_build.add_argument('input', metavar='INPUT', type=str,
                                help='source dict. support scheme: rime.\n example: rime://meogirl.dict.yaml')


    parser_build.add_argument('-o', '--output', dest='output', type=str, default=None,
                                action='store', help='output file')
    parser_build.add_argument('-outstd', '--output-std', dest='outstd', default=False,
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
