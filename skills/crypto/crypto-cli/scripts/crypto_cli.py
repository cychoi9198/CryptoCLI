#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crypto_cli.py - RSA / AES / Base64 CLI 도구

필요 패키지:  pip install cryptography   (>= 41 권장)

하위 명령:
  rsa-keygen    RSA 키쌍 생성
  rsa-encrypt   공개키로 데이터 암호화
  rsa-decrypt   RSA 복호화 (공개키: 개인키로 암호화된 데이터 복원 / 개인키: 표준 복호화)
  aes-keygen    AES 키 생성 (Seed 지정 시 결정적 파생, 생략 시 CSPRNG)
  aes-encrypt   AES 암호화 (기본 GCM, 선택 CBC)
  aes-decrypt   AES 복호화
  b64-encode    Base64 인코딩
  b64-decode    Base64 디코딩

공통 입력 규칙 (데이터를 받는 명령):
  -d/--data TEXT       문자열 직접 입력
  -f/--data-file PATH  파일 입력
  (둘 다 없으면 표준입력(stdin)에서 읽음)
"""

from __future__ import annotations

import argparse
import base64
import binascii
import os
import secrets
import sys
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, padding as sym_padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
HASHES = {"sha1": hashes.SHA1, "sha256": hashes.SHA256, "sha384": hashes.SHA384, "sha512": hashes.SHA512}
AES_BITS = (128, 192, 256)
GCM_NONCE_LEN = 12
GCM_TAG_LEN = 16
CBC_IV_LEN = 16
DEFAULT_KDF_SALT = b"crypto_cli.aes-keygen.v1"  # Seed 파생 시 salt 미지정 기본값
DEFAULT_KDF_ITER = 600_000                      # OWASP Password Storage Cheat Sheet 권고치(PBKDF2-HMAC-SHA256)


class CliError(Exception):
    """사용자에게 보여줄 오류"""


# ---------------------------------------------------------------------------
# 입출력 유틸
# ---------------------------------------------------------------------------
def read_input(args: argparse.Namespace) -> bytes:
    if getattr(args, "data", None) is not None:
        return args.data.encode(args.encoding)
    if getattr(args, "data_file", None):
        return Path(args.data_file).read_bytes()
    if sys.stdin.isatty():
        raise CliError("입력 데이터가 없습니다. -d, -f 또는 stdin 으로 입력하세요.")
    return sys.stdin.buffer.read()


def decode_text_input(raw: bytes, fmt: str) -> bytes:
    """암호문 등 '인코딩된 입력'을 바이트로 변환"""
    if fmt == "raw":
        return raw
    try:
        s = raw.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as e:
        raise CliError(f"입력이 {fmt} 텍스트가 아닙니다. 바이너리라면 --input-format raw 를 쓰세요.") from e
    try:
        if fmt == "base64":
            return base64.b64decode(s, validate=True)
        if fmt == "hex":
            return bytes.fromhex(s)
    except (binascii.Error, ValueError) as e:
        raise CliError(f"입력 {fmt} 형식이 올바르지 않습니다: {e}") from e
    return raw  # raw


def encode_output(data: bytes, fmt: str) -> bytes:
    if fmt == "base64":
        return base64.b64encode(data)
    if fmt == "hex":
        return data.hex().encode("ascii")
    return data  # raw


def write_output(data: bytes, out: str | None, newline: bool = True) -> None:
    if out:
        Path(out).write_bytes(data)
        print(f"[OK] 저장: {out} ({len(data)} bytes)", file=sys.stderr)
    else:
        sys.stdout.buffer.write(data)
        if newline:
            sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()


def parse_key(value: str, fmt: str) -> bytes:
    """AES 키 문자열(hex/base64), @파일경로, 또는 존재하는 키 파일 경로를 바이트로"""
    if value.startswith("@"):
        value = Path(value[1:]).read_text(encoding="ascii").strip()
    elif len(value) < 260 and Path(value).is_file():  # '@' 없이 파일 경로를 준 경우도 허용
        value = Path(value).read_text(encoding="ascii").strip()
    try:
        key = bytes.fromhex(value) if fmt == "hex" else base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as e:
        raise CliError(f"키 형식({fmt})이 올바르지 않습니다: {e} "
                       f"(키 파일이면 경로가 맞는지 확인하세요. 예: -k \"@C:\\temp\\aes.key\")") from e
    if len(key) * 8 not in AES_BITS:
        raise CliError(f"AES 키 길이는 128/192/256 bit 이어야 합니다. (입력: {len(key) * 8} bit)")
    return key


def add_data_args(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("-d", "--data", help="입력 데이터(문자열)")
    g.add_argument("-f", "--data-file", help="입력 데이터 파일 경로")
    p.add_argument("--encoding", default="utf-8", help="--data 문자열 인코딩 (기본 utf-8)")
    p.add_argument("-o", "--out", help="결과 저장 파일 (생략 시 stdout)")


# ---------------------------------------------------------------------------
# 1. RSA 키쌍 생성
# ---------------------------------------------------------------------------
def cmd_rsa_keygen(args: argparse.Namespace) -> None:
    if args.bits < 2048:
        if not args.allow_weak:
            raise CliError("2048 bit 미만은 보안상 거부됩니다. (테스트 목적이면 --allow-weak)")
        if args.bits < 1024:
            raise CliError("1024 bit 미만은 지원하지 않습니다.")
    if args.public_exponent < 3 or args.public_exponent % 2 == 0:
        raise CliError("public exponent 는 3 이상의 홀수여야 합니다. (권장 65537)")

    key = rsa.generate_private_key(public_exponent=args.public_exponent, key_size=args.bits)

    encoding = serialization.Encoding.PEM if args.format == "pem" else serialization.Encoding.DER
    priv_fmt = (serialization.PrivateFormat.PKCS8 if args.private_format == "pkcs8"
                else serialization.PrivateFormat.TraditionalOpenSSL)
    pub_fmt = (serialization.PublicFormat.SubjectPublicKeyInfo if args.public_format == "spki"
               else serialization.PublicFormat.PKCS1)

    if args.password:
        enc_alg = serialization.BestAvailableEncryption(args.password.encode("utf-8"))
    else:
        enc_alg = serialization.NoEncryption()

    priv_bytes = key.private_bytes(encoding, priv_fmt, enc_alg)
    pub_bytes = key.public_key().public_bytes(encoding, pub_fmt)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "pem" if args.format == "pem" else "der"
    priv_path = out_dir / f"{args.name}_private.{ext}"
    pub_path = out_dir / f"{args.name}_public.{ext}"

    for p in (priv_path, pub_path):
        if p.exists() and not args.force:
            raise CliError(f"이미 존재합니다: {p} (덮어쓰려면 --force)")

    priv_path.write_bytes(priv_bytes)
    try:
        os.chmod(priv_path, 0o600)  # Windows 에서는 효과 제한적
    except OSError:
        pass
    pub_path.write_bytes(pub_bytes)

    print(f"[OK] RSA {args.bits} bit, e={args.public_exponent}", file=sys.stderr)
    print(f"  private : {priv_path} ({args.private_format.upper()}, "
          f"{'암호화됨' if args.password else '평문'})", file=sys.stderr)
    print(f"  public  : {pub_path} ({args.public_format.upper()})", file=sys.stderr)


# ---------------------------------------------------------------------------
# 2. RSA 암호화
# ---------------------------------------------------------------------------
def load_public_key(value: str):
    p = Path(value)
    raw = p.read_bytes() if p.exists() else value.replace("\\n", "\n").encode("ascii")
    loaders = (serialization.load_pem_public_key, serialization.load_der_public_key)
    for loader in loaders:
        try:
            k = loader(raw)
            if isinstance(k, rsa.RSAPublicKey):
                return k
            raise CliError("RSA 공개키가 아닙니다.")
        except (ValueError, TypeError):
            continue
    # PKCS#1 'BEGIN RSA PUBLIC KEY' 도 load_pem_public_key 가 처리함. 그 외 base64 DER 시도
    try:
        return serialization.load_der_public_key(base64.b64decode(raw, validate=True))
    except Exception as e:
        raise CliError("공개키를 읽을 수 없습니다. (PEM/DER 파일 경로 또는 PEM 문자열)") from e


def cmd_rsa_encrypt(args: argparse.Namespace) -> None:
    pub = load_public_key(args.pubkey)
    data = read_input(args)
    k = pub.key_size // 8

    if args.padding == "oaep":
        h = HASHES[args.hash]()
        max_len = k - 2 * h.digest_size - 2
        pad = asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=HASHES[args.mgf_hash]()),
                                algorithm=h, label=args.label.encode() if args.label else None)
    else:
        max_len = k - 11
        pad = asym_padding.PKCS1v15()

    if len(data) > max_len:
        raise CliError(f"데이터가 너무 깁니다: {len(data)} bytes > 최대 {max_len} bytes "
                       f"(RSA {pub.key_size}, {args.padding.upper()}). "
                       f"큰 데이터는 AES 로 암호화하고 AES 키만 RSA 로 암호화하세요.")

    ct = pub.encrypt(data, pad)
    write_output(encode_output(ct, args.output_format), args.out, newline=args.output_format != "raw")


# ---------------------------------------------------------------------------
# 2-1. RSA 복호화
#   - 공개키 입력 : '개인키로 암호화된' 데이터 복원 (PKCS#1 v1.5 type 1 블록)
#                   = OpenSSL RSA_private_encrypt / Java Cipher(PRIVATE_KEY, RSA/ECB/PKCS1Padding) 결과
#   - 개인키 입력 : 표준 RSA 복호화 (OAEP / PKCS#1 v1.5 type 2)
# ---------------------------------------------------------------------------
def load_rsa_key(value: str, password: str | None):
    """경로 또는 PEM 문자열 → (key, is_private)"""
    p = Path(value)
    raw = p.read_bytes() if p.exists() else value.replace("\\n", "\n").encode("ascii")
    pw = password.encode("utf-8") if password else None

    for loader in (serialization.load_pem_private_key, serialization.load_der_private_key):
        try:
            k = loader(raw, pw)
            if not isinstance(k, rsa.RSAPrivateKey):
                raise CliError("RSA 키가 아닙니다.")
            return k, True
        except TypeError as e:  # 암호화된 개인키인데 비밀번호 없음 / 반대
            raise CliError(f"개인키 비밀번호 문제: {e}") from e
        except ValueError as e:
            if "password" in str(e).lower() or "decrypt" in str(e).lower():
                raise CliError("개인키 비밀번호가 올바르지 않습니다.") from e
            continue
    return load_public_key(value), False


def cmd_rsa_decrypt(args: argparse.Namespace) -> None:
    key, is_private = load_rsa_key(args.key, args.password)
    ct = decode_text_input(read_input(args), args.input_format)
    k = key.key_size // 8
    if len(ct) != k:
        raise CliError(f"암호문 길이({len(ct)} bytes)가 키 길이({k} bytes)와 다릅니다. "
                       f"--input-format 또는 키를 확인하세요.")

    if is_private:
        args.padding = args.padding or "oaep"
        if args.padding == "oaep":
            pad = asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=HASHES[args.mgf_hash]()),
                                    algorithm=HASHES[args.hash](),
                                    label=args.label.encode() if args.label else None)
        else:
            pad = asym_padding.PKCS1v15()
        try:
            pt = key.decrypt(ct, pad)
        except ValueError as e:
            raise CliError("복호화 실패: 키 불일치 또는 패딩/해시 옵션 불일치") from e
        mode = f"개인키, {args.padding.upper()}"
    else:
        if args.padding == "oaep":
            raise CliError("공개키 복호화는 PKCS#1 v1.5(type 1)만 가능합니다. OAEP 는 개인키가 필요합니다.")
        try:
            # algorithm=None → DigestInfo 해석 없이 type 1 패딩만 제거하고 원문 반환
            pt = key.recover_data_from_signature(ct, asym_padding.PKCS1v15(), None)
        except Exception as e:
            raise CliError("공개키 복호화 실패: 해당 공개키의 개인키로 PKCS#1 v1.5 암호화된 데이터가 아니거나, "
                           "일반 RSA 암호문(공개키로 암호화된 것)입니다. 후자는 개인키로만 복호화됩니다.") from e
        mode = "공개키, PKCS#1 v1.5 type 1"

    print(f"[OK] RSA {key.key_size} 복호화 ({mode}), {len(pt)} bytes", file=sys.stderr)
    write_output(encode_output(pt, args.output_format), args.out,
                 newline=args.output_format != "raw" or (not args.out and sys.stdout.isatty()))


# ---------------------------------------------------------------------------
# 3. AES 키 생성
# ---------------------------------------------------------------------------
def cmd_aes_keygen(args: argparse.Namespace) -> None:
    if args.bits not in AES_BITS:
        raise CliError("bits 는 128, 192, 256 중 하나여야 합니다.")
    n = args.bits // 8

    if args.seed is None:
        key = secrets.token_bytes(n)  # OS CSPRNG
        src = "CSPRNG(secrets)"
    else:
        salt = args.salt.encode("utf-8") if args.salt else DEFAULT_KDF_SALT
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=n, salt=salt, iterations=args.iterations)
        key = kdf.derive(args.seed.encode("utf-8"))
        src = f"PBKDF2-HMAC-SHA256(seed, iter={args.iterations})"

    print(f"[OK] AES-{args.bits} key / source={src}", file=sys.stderr)
    out = key.hex() if args.output_format == "hex" else base64.b64encode(key).decode("ascii")
    write_output(out.encode("ascii"), args.out)


# ---------------------------------------------------------------------------
# 4/5. AES 암호화 / 복호화
#   GCM : 출력 = nonce(12) || ciphertext || tag(16)
#   CBC : 출력 = iv(16)    || ciphertext   (PKCS#7 패딩, 무결성 없음)
# ---------------------------------------------------------------------------
def cmd_aes_encrypt(args: argparse.Namespace) -> None:
    key = parse_key(args.key, args.key_format)
    data = read_input(args)
    aad = args.aad.encode("utf-8") if args.aad else None

    if args.mode == "gcm":
        if args.iv:
            raise CliError("GCM 에서 nonce 직접 지정은 재사용 위험 때문에 지원하지 않습니다.")
        nonce = secrets.token_bytes(GCM_NONCE_LEN)
        blob = nonce + AESGCM(key).encrypt(nonce, data, aad)
    else:
        if aad:
            raise CliError("--aad 는 GCM 모드에서만 사용 가능합니다.")
        iv = bytes.fromhex(args.iv) if args.iv else secrets.token_bytes(CBC_IV_LEN)
        if len(iv) != CBC_IV_LEN:
            raise CliError("CBC IV 는 16 bytes(hex 32자)여야 합니다.")
        padder = sym_padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        blob = iv + enc.update(padded) + enc.finalize()

    write_output(encode_output(blob, args.output_format), args.out, newline=args.output_format != "raw")


def cmd_aes_decrypt(args: argparse.Namespace) -> None:
    key = parse_key(args.key, args.key_format)
    blob = decode_text_input(read_input(args), args.input_format)
    aad = args.aad.encode("utf-8") if args.aad else None

    if args.mode == "gcm":
        if len(blob) < GCM_NONCE_LEN + GCM_TAG_LEN:
            raise CliError("암호문 길이가 너무 짧습니다.")
        nonce, ct = blob[:GCM_NONCE_LEN], blob[GCM_NONCE_LEN:]
        try:
            pt = AESGCM(key).decrypt(nonce, ct, aad)
        except InvalidTag as e:
            raise CliError("복호화 실패: 키/AAD 불일치 또는 데이터 변조 (GCM 인증 실패)") from e
    else:
        if len(blob) < CBC_IV_LEN * 2 or (len(blob) - CBC_IV_LEN) % 16:
            raise CliError("CBC 암호문 길이가 올바르지 않습니다.")
        iv, ct = blob[:CBC_IV_LEN], blob[CBC_IV_LEN:]
        dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        padded = dec.update(ct) + dec.finalize()
        try:
            unpadder = sym_padding.PKCS7(128).unpadder()
            pt = unpadder.update(padded) + unpadder.finalize()
        except ValueError as e:
            raise CliError("복호화 실패: 키 불일치 또는 패딩 오류") from e

    write_output(pt, args.out, newline=False if args.out else sys.stdout.isatty())


# ---------------------------------------------------------------------------
# 6/7. Base64
# ---------------------------------------------------------------------------
def cmd_b64_encode(args: argparse.Namespace) -> None:
    data = read_input(args)
    enc = base64.urlsafe_b64encode(data) if args.url_safe else base64.b64encode(data)
    if args.no_padding:
        enc = enc.rstrip(b"=")
    write_output(enc, args.out)


def cmd_b64_decode(args: argparse.Namespace) -> None:
    s = b"".join(read_input(args).split())  # 줄바꿈/공백 제거 (MIME 형식 대응)
    s += b"=" * (-len(s) % 4)               # 패딩 생략 입력 보정
    try:
        if args.url_safe:
            dec = base64.b64decode(s, altchars=b"-_", validate=True)
        else:
            dec = base64.b64decode(s, validate=True)
    except binascii.Error as e:
        raise CliError(f"올바른 Base64 가 아닙니다: {e}") from e
    write_output(dec, args.out, newline=False if args.out else sys.stdout.isatty())


# ---------------------------------------------------------------------------
# argparse 구성
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="crypto_cli", description="RSA / AES / Base64 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="<command>")

    # 1. rsa-keygen
    p = sub.add_parser("rsa-keygen", help="RSA 키쌍 생성")
    p.add_argument("-b", "--bits", type=int, default=2048, help="키 길이 (기본 2048, 권장 2048/3072/4096)")
    p.add_argument("-e", "--public-exponent", type=int, default=65537, help="공개 지수 (기본 65537)")
    p.add_argument("--format", choices=["pem", "der"], default="pem", help="파일 인코딩 (기본 pem)")
    p.add_argument("--private-format", choices=["pkcs8", "pkcs1"], default="pkcs8",
                   help="개인키 구조 (기본 pkcs8)")
    p.add_argument("--public-format", choices=["spki", "pkcs1"], default="spki",
                   help="공개키 구조 (기본 spki = X.509 SubjectPublicKeyInfo)")
    p.add_argument("-p", "--password", help="개인키 암호화 비밀번호 (생략 시 평문 저장)")
    p.add_argument("--out-dir", default=".", help="저장 디렉터리 (기본 현재 폴더)")
    p.add_argument("-n", "--name", default="rsa", help="파일명 접두어 (기본 rsa)")
    p.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    p.add_argument("--allow-weak", action="store_true", help="1024~2047 bit 허용(테스트용)")
    p.set_defaults(func=cmd_rsa_keygen)

    # 2. rsa-encrypt
    p = sub.add_parser("rsa-encrypt", help="RSA 공개키 암호화")
    p.add_argument("-k", "--pubkey", required=True, help="공개키 파일 경로 또는 PEM 문자열")
    add_data_args(p)
    p.add_argument("--padding", choices=["oaep", "pkcs1"], default="oaep", help="패딩 (기본 oaep)")
    p.add_argument("--hash", choices=HASHES, default="sha256", help="OAEP 해시 (기본 sha256)")
    p.add_argument("--mgf-hash", choices=HASHES, default="sha256", help="OAEP MGF1 해시 (기본 sha256)")
    p.add_argument("--label", help="OAEP label (선택)")
    p.add_argument("--output-format", choices=["base64", "hex", "raw"], default="base64")
    p.set_defaults(func=cmd_rsa_encrypt)

    # 2-1. rsa-decrypt
    p = sub.add_parser("rsa-decrypt", help="RSA 복호화 (공개키: 개인키 암호화 데이터 복원 / 개인키: 표준 복호화)")
    p.add_argument("-k", "--key", required=True, help="공개키 또는 개인키 (파일 경로 또는 PEM 문자열, 자동 판별)")
    p.add_argument("-p", "--password", help="암호화된 개인키의 비밀번호")
    add_data_args(p)
    p.add_argument("--input-format", choices=["base64", "hex", "raw"], default="base64",
                   help="암호문 입력 형식 (기본 base64)")
    p.add_argument("--padding", choices=["oaep", "pkcs1"], default=None,
                   help="개인키: 기본 oaep / 공개키: pkcs1 고정")
    p.add_argument("--hash", choices=HASHES, default="sha256", help="OAEP 해시 (기본 sha256)")
    p.add_argument("--mgf-hash", choices=HASHES, default="sha256", help="OAEP MGF1 해시 (기본 sha256)")
    p.add_argument("--label", help="OAEP label (선택)")
    p.add_argument("--output-format", choices=["raw", "base64", "hex"], default="raw",
                   help="복호화 결과 출력 형식 (기본 raw)")
    p.set_defaults(func=cmd_rsa_decrypt)

    # 3. aes-keygen
    p = sub.add_parser("aes-keygen", help="AES 키 생성")
    p.add_argument("-b", "--bits", type=int, default=128, help="128/192/256 (기본 128)")
    p.add_argument("-s", "--seed", help="Seed 문자열. 지정 시 같은 seed+salt => 같은 키 (결정적)")
    p.add_argument("--salt", help="Seed 파생용 salt (생략 시 고정 기본값)")
    p.add_argument("--iterations", type=int, default=DEFAULT_KDF_ITER, help="PBKDF2 반복 횟수")
    p.add_argument("--output-format", choices=["hex", "base64"], default="hex")
    p.add_argument("-o", "--out", help="키 저장 파일")
    p.set_defaults(func=cmd_aes_keygen)

    # 4/5. aes-encrypt / aes-decrypt
    for name, func, hlp in (("aes-encrypt", cmd_aes_encrypt, "AES 암호화"),
                            ("aes-decrypt", cmd_aes_decrypt, "AES 복호화")):
        p = sub.add_parser(name, help=hlp)
        p.add_argument("-k", "--key", required=True, help="AES 키 (hex/base64 문자열, 또는 @키파일)")
        p.add_argument("--key-format", choices=["hex", "base64"], default="hex")
        add_data_args(p)
        p.add_argument("-m", "--mode", choices=["gcm", "cbc"], default="gcm", help="모드 (기본 gcm)")
        p.add_argument("--aad", help="GCM 추가 인증 데이터(선택, 복호화 시 동일해야 함)")
        if name == "aes-encrypt":
            p.add_argument("--iv", help="CBC IV hex(32자). 생략 시 랜덤(권장)")
            p.add_argument("--output-format", choices=["base64", "hex", "raw"], default="base64")
        else:
            p.add_argument("--input-format", choices=["base64", "hex", "raw"], default="base64")
        p.set_defaults(func=func)

    # 6/7. base64
    for name, func, hlp in (("b64-encode", cmd_b64_encode, "Base64 인코딩"),
                            ("b64-decode", cmd_b64_decode, "Base64 디코딩")):
        p = sub.add_parser(name, help=hlp)
        add_data_args(p)
        p.add_argument("--url-safe", action="store_true", help="URL-safe 알파벳(-_) 사용")
        if name == "b64-encode":
            p.add_argument("--no-padding", action="store_true", help="끝의 '=' 패딩 제거")
        p.set_defaults(func=func)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except CliError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"[ERROR] 파일을 찾을 수 없습니다: {e.filename}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
