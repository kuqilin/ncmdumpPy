# -*- coding: utf-8 -*-

import struct
import base64
import json
import os
import argparse
import sys
from typing import Dict, Any
from Crypto.Cipher import AES
from mutagen._file import File as MutagenFile   # 报错就换成 from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC            # 报错就换成 from mutagen.id3 import APIC
from mutagen.flac import FLAC, Picture

# ---------- 固定密钥常量 ----------
CORE_KEY = bytes.fromhex("687A4852416D736F356B496E62617857")
META_KEY = bytes.fromhex("2331346C6A6B5F215C5D2630553C2728")
NCM_MAGIC = b'CTENFDAM'

# ---------- 一些选项参数 ----------
DEL_ORIGIN = False  # 是否删除原始 .ncm 文件

def Mprint(message: str) -> None:
    """信息输出"""
    print(f"\033[34m[信息]\033[0m {message}")

def Wprint(message: str) -> None:
    """警告输出"""
    print(f"\033[33m[警告]\033[0m {message}")

def Eprint(message: str) -> None:
    """错误输出"""
    print(f"\033[31m[错误]\033[0m {message}")


# ---------- 工具函数 ----------
def unpad_pkcs7(data: bytes) -> bytes:
    """去除 PKCS#7 填充"""
    return data[:-data[-1]]

def generate_key_box(key_material: bytes) -> bytearray:
    """根据密钥材料生成 256 字节 S 盒（类 RC4）"""
    key_len = len(key_material)
    s_box = bytearray(range(256))
    c = 0
    last_byte = 0
    key_offset = 0
    for i in range(256):
        swap = s_box[i]
        c = (swap + last_byte + key_material[key_offset]) & 0xFF
        key_offset += 1
        if key_offset >= key_len:
            key_offset = 0
        s_box[i] = s_box[c]
        s_box[c] = swap
        last_byte = c
    return s_box

def decrypt_rc4_like(data: bytearray, s_box: bytearray) -> None:
    """流式解密"""
    length = len(data)
    for i in range(1, length + 1):
        j = i & 0xFF
        idx1 = (s_box[j] + j) & 0xFF
        idx2 = (s_box[j] + s_box[idx1]) & 0xFF
        data[i - 1] ^= s_box[idx2]

def _safe_get(meta: Dict, *keys: str, default: str = '') -> str:
    """从元数据中安全提取字符串"""
    for key in keys:
        value = meta.get(key)
        if value is not None:
            if isinstance(value, list):
                if value and isinstance(value[0], list):
                    return str(value[0][0])
                elif value:
                    return str(value[0])
            return str(value)
    return default

# ---------- 元数据写入（使用原始图片字节流） ----------
def write_metadata(audio_path: str,
                   meta: Dict[str, Any],
                   cover_bytes: bytes = None) -> None:
    """
    将元数据及封面图片写入音频文件
    :param audio_path:  解密后的音频路径
    :param meta:        解密得到的元数据字典
    :param cover_bytes: 从NCM文件直接读取的图片原始字节（JPEG/PNG等）
    """
    ext = os.path.splitext(audio_path)[1].lower()

    title = _safe_get(meta, 'musicName', 'name')
    artist = _safe_get(meta, 'artist')
    album = _safe_get(meta, 'album')
    year = _safe_get(meta, 'year')
    track = _safe_get(meta, 'track', 'no')
    genre = _safe_get(meta, 'genre', 'style')

    # 自动判断图片 MIME 类型（默认 jpeg）
    mime = 'image/jpeg'
    if cover_bytes and cover_bytes[:4] == b'\x89PNG':
        mime = 'image/png'

    try:
        if ext == '.mp3':
            try:
                audio = EasyID3(audio_path)
            except Exception:
                audio = MutagenFile(audio_path, easy=True)
                audio.add_tags()

            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            audio['date'] = year
            audio['tracknumber'] = track
            audio['genre'] = genre
            audio.save()

            if cover_bytes:
                id3 = ID3(audio_path)
                id3.delall('APIC')
                id3.add(
                    APIC(encoding=3, mime=mime, type=3, desc='Cover', data=cover_bytes)
                )
                id3.save()

        elif ext == '.flac':
            audio = FLAC(audio_path)
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            audio['date'] = year
            audio['tracknumber'] = track
            audio['genre'] = genre
            audio.save()

            if cover_bytes:
                image = Picture()
                image.type = 3
                image.mime = mime
                image.desc = 'Cover'
                image.data = cover_bytes
                audio.add_picture(image)
                audio.save()
        else:
            Mprint(f"不支持 {ext} 格式的元数据写入，已跳过。")
    except Exception as e:
        Wprint(f"元数据写入失败：{e}")

# ---------- 核心解密 ----------
def dump(ncm_path: str) -> str:
    """
    解密 .ncm 文件，输出音频并写入元数据及封面。
    :return: 输出文件名
    """
    with open(ncm_path, 'rb') as f:
        # 1. 魔数校验
        if f.read(8) != NCM_MAGIC:
            Eprint(f"{ncm_path}: 无效的 .ncm 文件")
            return ""
        Mprint(f"{ncm_path}: 校验完成，开始解密")
        f.seek(2, 1)  # 保留

        # 2. 解密音频密钥 -> S 盒
        key_len = struct.unpack('<I', f.read(4))[0]
        enc_key = bytearray(f.read(key_len))
        for i in range(key_len):
            enc_key[i] ^= 0x64
        dec_key = unpad_pkcs7(AES.new(CORE_KEY, AES.MODE_ECB).decrypt(bytes(enc_key)))
        s_box = generate_key_box(dec_key[17:])

        Mprint(f"{ncm_path}: 密钥解密完成")

        # 3. 解密元数据
        meta_len = struct.unpack('<I', f.read(4))[0]
        enc_meta = bytearray(f.read(meta_len))
        for i in range(meta_len):
            enc_meta[i] ^= 0x63
        meta_cipher = base64.b64decode(bytes(enc_meta[22:]))
        meta_json = unpad_pkcs7(AES.new(META_KEY, AES.MODE_ECB).decrypt(meta_cipher)).decode('utf-8')
        meta_dict = json.loads(meta_json[6:])

        Mprint(f"{ncm_path}: 元数据解密完成")

        # 4. 跳过 CRC / 保留
        f.read(4)
        f.seek(5, 1)

        # 5. **** 关键修改：读取封面图片二进制数据 ****
        img_size = struct.unpack('<I', f.read(4))[0]
        cover_data = f.read(img_size) if img_size > 0 else None

        # 6. 解密音频数据
        output_dir = os.path.dirname(ncm_path)
        # 格式优先从 meta 取，若没有则默认 mp3
        fmt = meta_dict.get('format', 'mp3')
        out_name = os.path.splitext(os.path.basename(ncm_path))[0] + '.' + fmt
        out_path = os.path.join(output_dir, out_name)

        Mprint(f"{ncm_path}: 音频解密完成")

        with open(out_path, 'wb') as out:
            while True:
                chunk = bytearray(f.read(0x8000))
                if not chunk:
                    break
                decrypt_rc4_like(chunk, s_box)
                out.write(chunk)
        Mprint(f"{ncm_path}: 音频写入完成")

    # 7. 写入元数据（使用直接读取的封面二进制）
    write_metadata(out_path, meta_dict, cover_data)
    Mprint(f"{ncm_path}: 元数据写入完成")
    if DEL_ORIGIN:
        try:
            os.remove(ncm_path)
            Mprint(f"{ncm_path}: 原始文件已删除")
        except Exception as e:
            Wprint(f"{ncm_path}: 无法删除原始文件 - {e}")
    
    print(f"\033[32m-------- {ncm_path} 解密完成 --------\033[0m")

    return out_name


if __name__ == '__main__':

    cnt = 0

    parser = argparse.ArgumentParser(description='解密 .ncm 文件')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--input', nargs='+', help='.nmc 文件路径 (可指定多个)')
    group.add_argument('-d', '--directory', help='包含 NCM 文件的目录，用于批量处理')
    parser.add_argument('-r', '--remove', action='store_true', help='是否删除原始 .ncm 文件')
    args = parser.parse_args()

    # 判断是否删除原始 .ncm 文件
    if args.remove:
        Wprint("将会删除原始 .ncm 文件")
        DEL_ORIGIN = True

    # 处理单个文件 -i
    if args.input:
        for input_file in args.input:
            if os.path.isfile(input_file):
                dump(input_file)
                cnt += 1
            else:
                Eprint(f"{input_file} 不是一个有效的文件")
        
    # 处理文件夹 -d
    if args.directory:
        if os.path.isdir(args.directory):
            for ncm_file in os.listdir(args.directory):
                if ncm_file.endswith('.ncm'):
                    dump(os.path.join(args.directory, ncm_file))
                    cnt += 1
        else:
            Eprint(f"{args.directory} 不是一个有效的目录")
    
    Mprint(f"共 {cnt} 个文件处理完毕")
