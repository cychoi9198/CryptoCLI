#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crypto_cli.py 자체 검증 스크립트 (임시 폴더에서 실행, 사용자 파일을 건드리지 않음)

사용: python3 selftest.py      → 마지막 줄 ALL PASSED / N FAILED
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLI = [sys.executable, str(HERE / "crypto_cli.py")]
results: list[tuple[str, bool, str]] = []


def run(*args, stdin: bytes | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(CLI + list(args), input=stdin, capture_output=True, cwd=cwd)


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not cond else ""))


def out(p: subprocess.CompletedProcess) -> str:
    return p.stdout.decode().strip()


def private_encrypt_pkcs1(priv_pem: Path, data: bytes, password: bytes | None = None) -> bytes:
    """OpenSSL RSA_private_encrypt(PKCS1) 와 동일한 결과를 만든다 (공개키 복호화 테스트용)"""
    from cryptography.hazmat.primitives import serialization
    key = serialization.load_pem_private_key(priv_pem.read_bytes(), password)
    nums = key.private_numbers()
    k = key.key_size // 8
    em = b"\x00\x01" + b"\xff" * (k - len(data) - 3) + b"\x00" + data
    c = pow(int.from_bytes(em, "big"), nums.d, nums.public_numbers.n)
    return c.to_bytes(k, "big")


def main() -> int:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        print("[FAIL] cryptography 패키지가 없습니다: python3 -m pip install \"cryptography>=41\"")
        return 1

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)

        # 1. rsa-keygen
        p = run("rsa-keygen", "-b", "2048", "--out-dir", "k", "-n", "a", cwd=t)
        check("rsa-keygen 2048", p.returncode == 0 and (t / "k/a_private.pem").exists(), p.stderr.decode())
        p = run("rsa-keygen", "-b", "3072", "-p", "pw", "--out-dir", "k", "-n", "b", cwd=t)
        check("rsa-keygen 3072 + password", p.returncode == 0 and
              b"ENCRYPTED" in (t / "k/b_private.pem").read_bytes(), p.stderr.decode())
        p = run("rsa-keygen", "-b", "2048", "--out-dir", "k", "-n", "c", "--format", "der",
                "--private-format", "pkcs1", "--public-format", "pkcs1", cwd=t)
        check("rsa-keygen DER/PKCS1", p.returncode == 0 and (t / "k/c_public.der").exists(), p.stderr.decode())
        check("rsa-keygen 1024 거부", run("rsa-keygen", "-b", "1024", "--out-dir", "k", "-n", "w", cwd=t).returncode == 1)
        check("rsa-keygen 덮어쓰기 거부", run("rsa-keygen", "--out-dir", "k", "-n", "a", cwd=t).returncode == 1)

        msg = "RSA 테스트 메시지"
        # 2 / 2-1. rsa-encrypt ↔ rsa-decrypt(개인키)
        for pad in ("oaep", "pkcs1"):
            ct = out(run("rsa-encrypt", "-k", "k/a_public.pem", "--padding", pad, "-d", msg, cwd=t))
            p = run("rsa-decrypt", "-k", "k/a_private.pem", "--padding", pad, "-d", ct, cwd=t)
            check(f"RSA {pad} 왕복", p.stdout.decode() == msg, p.stderr.decode())
        ct = out(run("rsa-encrypt", "-k", "k/b_public.pem", "-d", msg, cwd=t))
        check("RSA 암호화 개인키 왕복", run("rsa-decrypt", "-k", "k/b_private.pem", "-p", "pw", "-d", ct,
                                         cwd=t).stdout.decode() == msg)
        check("RSA 비밀번호 오류 거부", run("rsa-decrypt", "-k", "k/b_private.pem", "-p", "x", "-d", ct,
                                          cwd=t).returncode == 1)
        ct = out(run("rsa-encrypt", "-k", "k/c_public.der", "-d", msg, cwd=t))
        check("RSA DER 공개키 암호화", len(base64.b64decode(ct)) == 256)
        check("RSA 길이 초과 거부", run("rsa-encrypt", "-k", "k/a_public.pem", "-d", "x" * 191, cwd=t).returncode == 1)

        # 2-1. rsa-decrypt(공개키)
        raw = os.urandom(64)
        (t / "pe.bin").write_bytes(private_encrypt_pkcs1(t / "k/a_private.pem", raw))
        p = run("rsa-decrypt", "-k", "k/a_public.pem", "-f", "pe.bin", "--input-format", "raw", "-o", "pe.dec", cwd=t)
        check("RSA 공개키 복호화(바이너리)", p.returncode == 0 and (t / "pe.dec").read_bytes() == raw, p.stderr.decode())
        pe_b64 = base64.b64encode(private_encrypt_pkcs1(t / "k/b_private.pem", msg.encode(), b"pw")).decode()
        check("RSA 공개키 복호화(base64)", run("rsa-decrypt", "-k", "k/b_public.pem", "-d", pe_b64,
                                             cwd=t).stdout.decode() == msg)
        ct = out(run("rsa-encrypt", "-k", "k/a_public.pem", "-d", msg, cwd=t))
        check("공개키로 일반 암호문 복호화 거부", run("rsa-decrypt", "-k", "k/a_public.pem", "-d", ct, cwd=t).returncode == 1)
        check("공개키 + OAEP 거부", run("rsa-decrypt", "-k", "k/a_public.pem", "--padding", "oaep", "-d", pe_b64,
                                     cwd=t).returncode == 1)

        # 3. aes-keygen
        for bits, hexlen in (("128", 32), ("192", 48), ("256", 64)):
            check(f"aes-keygen {bits}", len(out(run("aes-keygen", "-b", bits))) == hexlen)
        check("aes-keygen 기본 128", len(out(run("aes-keygen"))) == 32)
        a = out(run("aes-keygen", "-s", "seed", "--iterations", "1000"))
        b = out(run("aes-keygen", "-s", "seed", "--iterations", "1000"))
        c = out(run("aes-keygen", "-s", "seed", "--iterations", "1000", "--salt", "other"))
        check("aes-keygen seed 결정성", a == b and a != c)
        import hashlib
        exp = hashlib.pbkdf2_hmac("sha256", b"seed", b"crypto_cli.aes-keygen.v1", 1000, 16).hex()
        check("aes-keygen seed = PBKDF2 명세값", a == exp)
        check("aes-keygen 잘못된 bits 거부", run("aes-keygen", "-b", "100").returncode == 1)
        check("aes-keygen 랜덤 비중복", out(run("aes-keygen")) != out(run("aes-keygen")))

        # 4/5. aes
        key = out(run("aes-keygen", "-b", "256"))
        for mode in ("gcm", "cbc"):
            e = out(run("aes-encrypt", "-k", key, "-m", mode, "-d", "AES 한글 평문"))
            check(f"AES {mode} 왕복", run("aes-decrypt", "-k", key, "-m", mode, "-d", e).stdout.decode() == "AES 한글 평문")
        e = out(run("aes-encrypt", "-k", key, "--aad", "h", "-d", "x"))
        check("AES GCM AAD 불일치 거부", run("aes-decrypt", "-k", key, "--aad", "z", "-d", e).returncode == 1)
        tampered = bytearray(base64.b64decode(e)); tampered[-1] ^= 1
        check("AES GCM 변조 탐지", run("aes-decrypt", "-k", key, "-d", base64.b64encode(tampered).decode()).returncode == 1)
        check("AES 다른 키 거부", run("aes-decrypt", "-k", out(run("aes-keygen", "-b", "256")), "-d", e).returncode == 1)
        (t / "aes.key").write_text(key)
        blob = os.urandom(200_000); (t / "big.bin").write_bytes(blob)
        run("aes-encrypt", "-k", "@aes.key", "-f", "big.bin", "--output-format", "raw", "-o", "big.enc", cwd=t)
        run("aes-decrypt", "-k", "@aes.key", "-f", "big.enc", "--input-format", "raw", "-o", "big.dec", cwd=t)
        check("AES 바이너리 파일 왕복(@키파일, raw)", (t / "big.dec").read_bytes() == blob)
        kb64 = out(run("aes-keygen", "--output-format", "base64"))
        e = out(run("aes-encrypt", "-k", kb64, "--key-format", "base64", "-d", "b64key"))
        check("AES base64 키", run("aes-decrypt", "-k", kb64, "--key-format", "base64", "-d", e).stdout == b"b64key")

        # 6/7. base64
        check("b64-encode", out(run("b64-encode", "-d", "Hello 세계")) == "SGVsbG8g7IS46rOE")
        check("b64-decode", run("b64-decode", "-d", "SGVsbG8g7IS46rOE").stdout.decode() == "Hello 세계")
        check("b64 url-safe/no-padding", out(run("b64-encode", "-d", "??>>", "--url-safe", "--no-padding")) == "Pz8-Pg"
              and run("b64-decode", "-d", "Pz8-Pg", "--url-safe").stdout == b"??>>")
        check("b64 stdin 파이프", run("b64-decode", stdin=run("b64-encode", stdin=b"pipe\x00\xff").stdout).stdout
              == b"pipe\x00\xff")
        check("b64 잘못된 입력 거부", run("b64-decode", "-d", "!!!").returncode == 1)

    failed = [r for r in results if not r[1]]
    print("-" * 40)
    print("ALL PASSED" if not failed else f"{len(failed)} FAILED / {len(results)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
