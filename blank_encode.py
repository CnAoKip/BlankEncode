import os, chardet
from sys import argv
from pyperclip import copy as copy_to_clip
from pyperclip import paste as paste_from_clip


# 默认编码字符集
default_charset = [chr(ch) for ch in range(0x2000, 0x2010)] + ['utf-8'] # 这些字符全为不可见的，有的是特殊空格，有的是 Unicode 操纵字符
encode_suffix = ""
decode_suffix = ""


is_valid_charset = lambda charset: len(set(charset)) == len(charset)

def encode(input: bytes, charset: list) -> tuple:
    '''使用charset对input进行编码，返回二元字符串元组。
    返回值：元组（编码结果，字符集编码类型）
    '''
    encoded_str = ""
    for b in input:
        encoded_str += charset[b>>4]  # 先转码二进制的高四位，对应2位16进制数的第一位
        encoded_str += charset[b&0xf] # 再转码二进制的低四位，对应2位16进制数的第二位
    charset_encoding = charset[-1]
    return encoded_str, charset_encoding


def decode(input: bytes, charset: list) -> tuple:
    '''使用charset对input进行解码，返回二元字符串元组。
    返回值：元组（解码结果，结果编码类型）
    '''
    encoded_encoding = chardet.detect(input)["encoding"]
    input = str(input, encoding=encoded_encoding)
    decoded_bytes = bytes() # b''
    try:
        for i in range(0, len(input), 2):
            h = charset.index(input[i])
            l = charset.index(input[i+1])  # 从编码字符集查找并且拼凑出原先的字节
            decoded_bytes += bytes([(h<<4)|l])
    except ValueError:
        print("编码字符集与加密内容不匹配！")
        return '', 'utf-8'
    decoded_encoding = chardet.detect(decoded_bytes)["encoding"]
    return str(decoded_bytes, encoding=decoded_encoding), decoded_encoding


def transcode_file(charset_path='', encode_path='', decode_path='') -> None:
    '''通用的解码/编码函数，给定encode_path则解码至.dec文件，给定decode_path则编码至.enc文件
    给定charset_path，则使用自定义的字符集进行编码
    '''
    charset = list() # []
    mode = -1  # 0=Encode 1=Decode
    charset_encoding = "utf-8" # 默认为 UTF-8
    try:
        if(charset_path == ''): 
            charset = default_charset # 未指定编码字符集时采用默认的“空白字符”编码字符集
        else:
            with open(charset_path, "rb") as charset_file:
                charset_bytes = charset_file.read(16)
                charset_encoding = chardet.detect(charset_bytes)["encoding"] # 判断编码字符集编码
                charset = list(str(charset_bytes, encoding=charset_encoding)) + [charset_encoding]

        if(encode_path == ''):
            mode = 0
            encode_path = "result.enc" + encode_suffix
        if(decode_path == ''):
            if(mode == 0): exit(4)
            mode = 1
            decode_path = "result.dec" + decode_suffix

        if(os.path.exists(decode_path)):
            mode = 0
        if(os.path.exists(encode_path)):
            if(mode == 0): exit(4) # 不覆写
            mode = 1

        # 没想好这个函数怎么命名
        def perform_io(input_path: str, output_path: str, encode_func):
            with open(input_path, 'rb') as input_file:
                input_bytes = input_file.read()
            encoded, encoding = encode_func(input_bytes, charset)
            with open(output_path, 'w', encoding=encoding) as output_file:
                output_file.write(encoded)

        if(mode == 0):
            perform_io(decode_path, encode_path, encode)

        if(mode == 1):
            perform_io(encode_path, decode_path, decode)
    except IOError:
        print("文件读写错误！")


# 为了方便操作，待操作文件名（或扩展名）中需要一个修饰符。
# 规则是文件名中含有.enc为待编码文件，.dec为待解码文件，.dict为编码字符集文件。
if __name__ == "__main__":
    charset_path = ""
    encode_path = ""
    decode_path = ""
    # print(argv)
    if len(argv) == 1 or '-h' in argv or '-help' in argv: # 打印帮助
        print("""- 基本用法：blank_encode.py input [dict][output]
其中，输入与两个可选参数文件名（或扩展名）中需要一个修饰符。规则是文件名中含有.enc为待解码文件，.dec为待编码文件，.dict为编码字符集文件。
.enc 或 .dec 前（相邻）可以指定转码后默认文件扩展名，如 1.mp4.dec.html 编码后默认输出 result.enc.mp4。
编码字符集内容应为无重复字符且长度为 16 的字符串。如果编码字符集未指定，采用默认空白编码字符集。
- 快速用法：blank_encode.py [-encode text] [-decode text] [--encode-clip] [--decode-clip]""")
        exit(0)
    
    if '-encode' in argv:
        decoded = encode(bytes(argv[argv.index('-encode')+1], encoding='utf-8'), default_charset)[0]
        copy_to_clip(decoded)
        print(f"已复制编码结果到剪切板: [{decoded}]")
        exit(0)
    elif '-decode' in argv:
        # print(list(argv[argv.index('-decode')+1]))
        decoded = decode(bytes(argv[argv.index('-decode')+1], encoding='utf-8'), default_charset)[0]
        copy_to_clip(decoded)
        print(f"已复制解码结果到剪切板: [{decoded}]")
        exit(0)
    elif '--encode-clip' in argv:
        decoded = encode(bytes(paste_from_clip(), encoding='utf-8'), default_charset)[0]
        copy_to_clip(decoded)
        print(f"已复制编码结果到剪切板: [{decoded}]")
        exit(0)
    elif '--decode-clip' in argv:
        decoded = decode(bytes(paste_from_clip(), encoding='utf-8'), default_charset)[0]
        copy_to_clip(decoded)
        print(f"已复制解码结果到剪切板: [{decoded}]")
        exit(0)
    
    for path in argv[1:]:
        if(".enc" in path):
            encode_path = path
            decode_suffix = path[path.index("."): path.index(".enc")]
        if(".dec" in path):
            decode_path = path
            encode_suffix = path[path.index("."): path.index(".dec")]
        if(".dict" in path): 
            charset_path = path

    transcode_file(charset_path, encode_path, decode_path)