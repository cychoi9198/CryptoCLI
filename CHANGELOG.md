# Changelog

**[한국어](#한국어) · [English](#english) · [日本語](#日本語)**

이 문서는 [Keep a Changelog](https://keepachangelog.com/) 형식을, 버전은 [Semantic Versioning](https://semver.org/) 을 따릅니다.
This project follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).
本プロジェクトは [Keep a Changelog](https://keepachangelog.com/) の形式と [Semantic Versioning](https://semver.org/) に従います。

---

## 한국어

### [1.1.1] - 2026-10-29

#### 변경
- `aes-encrypt` / `aes-decrypt` 의 `-k` 에 `@` 없이 키 파일 경로만 지정해도 동작하도록 변경 (예: `-k C:\temp\aes.key`). 해당 경로에 파일이 있으면 파일에서 키를 읽음. 기존 `@파일경로`, 키 문자열 입력은 그대로 지원. (`f3edc80`)
- 키 형식 오류 메시지에 올바른 사용 예를 추가. (`f3edc80`)

#### 수정
- Windows 콘솔(cp949 등)에서 복호화·Base64 디코딩 결과의 한글이 깨지던 문제 수정. 콘솔 출력 시 UTF-8 텍스트는 문자열로 출력하도록 변경. 파일 출력(`-o`)·파이프·바이너리 출력은 기존과 동일. (`736ef8b`)

#### 문서
- README.md, references/formats.md 를 한국어·영어·일본어 3개 언어로 작성. (`c7034d7`, `f2d5880`)
- CHANGELOG.md 추가.

#### 호환성
- 암호문 포맷, 키 생성 방식, 알고리즘 변경 없음. 1.1.0 으로 만든 키·암호문을 그대로 사용 가능.

### [1.1.0] - 2026-10-29

최초 공개 버전. (`ff46dc1`)

#### 추가
- `rsa-keygen`: RSA 키쌍 생성 (키 길이, 공개 지수, PEM/DER, PKCS#8/PKCS#1, SPKI/PKCS#1, 개인키 비밀번호)
- `rsa-encrypt`: 공개키 암호화 (OAEP-SHA256 기본, PKCS#1 v1.5 선택)
- `rsa-decrypt`: 개인키 표준 복호화 및 공개키로 "개인키 암호화" 데이터 복원 (키 종류 자동 판별)
- `aes-keygen`: AES 128/192/256 키 생성 (CSPRNG 또는 seed 기반 PBKDF2-HMAC-SHA256)
- `aes-encrypt` / `aes-decrypt`: GCM(기본)·CBC
- `b64-encode` / `b64-decode`: 표준·URL-safe·패딩 생략
- Hermes Agent 스킬(`SKILL.md`), 자체 검증(`selftest.py`, 35개 항목), 연동 포맷 문서(`formats.md`), 설치 스크립트(`install.sh`, `install.ps1`), MIT 라이선스

---

## English

### [1.1.1] - 2026-10-29

#### Changed
- `-k` for `aes-encrypt` / `aes-decrypt` now also accepts a plain key file path without `@` (e.g. `-k C:\temp\aes.key`). If a file exists at that path, the key is read from it. The existing `@path` form and inline key strings are still supported. (`f3edc80`)
- The key-format error message now includes a correct usage example. (`f3edc80`)

#### Fixed
- Non-ASCII (e.g. Korean) text in decryption and Base64 decoding results was garbled on Windows consoles (cp949, etc.). When writing to a console, UTF-8 text is now written as a string. File output (`-o`), pipes and binary output are unchanged. (`736ef8b`)

#### Documentation
- README.md and references/formats.md are now written in Korean, English and Japanese. (`c7034d7`, `f2d5880`)
- Added CHANGELOG.md.

#### Compatibility
- No changes to the ciphertext format, key generation or algorithms. Keys and ciphertexts created with 1.1.0 work as-is.

### [1.1.0] - 2026-10-29

First public release. (`ff46dc1`)

#### Added
- `rsa-keygen`: RSA key-pair generation (key size, public exponent, PEM/DER, PKCS#8/PKCS#1, SPKI/PKCS#1, private-key password)
- `rsa-encrypt`: public-key encryption (OAEP-SHA256 by default, optional PKCS#1 v1.5)
- `rsa-decrypt`: standard private-key decryption, and public-key recovery of data "encrypted with the private key" (key type detected automatically)
- `aes-keygen`: AES 128/192/256 key generation (CSPRNG, or PBKDF2-HMAC-SHA256 from a seed)
- `aes-encrypt` / `aes-decrypt`: GCM (default) and CBC
- `b64-encode` / `b64-decode`: standard, URL-safe, unpadded
- Hermes Agent skill (`SKILL.md`), self-test (`selftest.py`, 35 checks), interop format reference (`formats.md`), installers (`install.sh`, `install.ps1`), MIT license

---

## 日本語

### [1.1.1] - 2026-10-29

#### 変更
- `aes-encrypt` / `aes-decrypt` の `-k` で、`@` を付けずに鍵ファイルのパスだけを指定しても動作するよう変更（例: `-k C:\temp\aes.key`）。そのパスにファイルが存在する場合はファイルから鍵を読み込みます。従来の `@パス` 形式と鍵文字列の直接指定も引き続き使用できます。（`f3edc80`）
- 鍵形式エラーのメッセージに正しい使用例を追加。（`f3edc80`）

#### 修正
- Windows コンソール（cp949 など）で、復号および Base64 デコード結果の非 ASCII 文字（韓国語など）が文字化けする問題を修正。コンソールへ出力する際、UTF-8 テキストは文字列として出力するよう変更。ファイル出力（`-o`）・パイプ・バイナリ出力は従来どおり。（`736ef8b`）

#### ドキュメント
- README.md と references/formats.md を韓国語・英語・日本語の 3 言語で作成。（`c7034d7`、`f2d5880`）
- CHANGELOG.md を追加。

#### 互換性
- 暗号文の形式、鍵の生成方式、アルゴリズムに変更はありません。1.1.0 で作成した鍵・暗号文をそのまま使用できます。

### [1.1.0] - 2026-10-29

最初の公開バージョン。（`ff46dc1`）

#### 追加
- `rsa-keygen`: RSA 鍵ペア生成（鍵長、公開指数、PEM/DER、PKCS#8/PKCS#1、SPKI/PKCS#1、秘密鍵パスワード）
- `rsa-encrypt`: 公開鍵による暗号化（既定 OAEP-SHA256、選択 PKCS#1 v1.5）
- `rsa-decrypt`: 秘密鍵による標準的な復号、および公開鍵による「秘密鍵で暗号化された」データの復元（鍵の種類は自動判別）
- `aes-keygen`: AES 128/192/256 鍵生成（CSPRNG、または seed からの PBKDF2-HMAC-SHA256）
- `aes-encrypt` / `aes-decrypt`: GCM（既定）・CBC
- `b64-encode` / `b64-decode`: 標準・URL-safe・パディング省略
- Hermes Agent スキル（`SKILL.md`）、セルフテスト（`selftest.py`、35 項目）、連携フォーマット資料（`formats.md`）、インストールスクリプト（`install.sh`、`install.ps1`）、MIT ライセンス

[1.1.1]: https://github.com/cychoi9198/CryptoCLI/compare/ff46dc1...25a6bee
[1.1.0]: https://github.com/cychoi9198/CryptoCLI/tree/ff46dc1
