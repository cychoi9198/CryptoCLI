# CryptoCLI

**[한국어](#한국어) · [English](#english) · [日本語](#日本語)**

---

## 한국어

**CryptoCLI** 는 RSA·AES·Base64 작업을 명령 한 줄로 처리하는 Python CLI 이자, [Hermes Agent](https://hermes-agent.nousresearch.com/) 가 바로 쓸 수 있는 스킬 패키지입니다.

- **RSA** — 키쌍 생성(키 길이·공개 지수·PEM/DER·PKCS#8/PKCS#1·개인키 비밀번호), 공개키 암호화(OAEP-SHA256 / PKCS#1 v1.5), 복호화(개인키 표준 복호화 + 개인키로 암호화된 데이터의 공개키 복원)
- **AES** — 128/192/256bit 키 생성(CSPRNG 또는 seed 기반 PBKDF2 결정적 파생), GCM(기본)·CBC 암호화/복호화
- **Base64** — 표준·URL-safe·패딩 생략 인코딩/디코딩
- **에이전트 친화적** — 단일 파일, 명확한 종료 코드, stdout(결과)/stderr(상태) 분리, `-d`·`-f`·stdin 입력, 민감 데이터 취급 규칙을 담은 `SKILL.md`
- **검증 완료** — 35개 항목 자체 테스트(`selftest.py`)와 OpenSSL 교차 검증, C#·Java·OpenSSL 연동 포맷 문서 제공

널리 쓰이는 암호 라이브러리 [pyca/cryptography](https://cryptography.io/) 위에서 동작하며, 약한 설정(2048bit 미만 RSA, GCM nonce 재사용 등)은 기본적으로 차단합니다.

### 빠른 설치

```bash
git clone https://github.com/cychoi9198/CryptoCLI.git
cd CryptoCLI
./install.sh                 # Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### 구성

```
CryptoCLI/
├── README.md                      ← 이 문서 (설치·운영 안내)
├── LICENSE                        ← MIT
├── CHANGELOG.md                   ← 업데이트 기록 (3개 언어)
├── requirements.txt               ← cryptography>=41
├── install.sh                     ← Linux/macOS 설치 스크립트
├── install.ps1                    ← Windows 설치 스크립트
└── skills/crypto/crypto-cli/      ← Hermes 스킬 본체 (이 폴더를 통째로 설치)
    ├── SKILL.md                   ← 에이전트용 사용 절차
    ├── scripts/
    │   ├── crypto_cli.py          ← CLI 본체 (단일 파일)
    │   └── selftest.py            ← 35개 항목 자체 검증
    └── references/
        └── formats.md             ← 바이트 배치·알고리즘 파라미터, C#/Java/OpenSSL 연동 (3개 언어)
```

### 기능

| # | 명령 | 설명 |
|---|---|---|
| 1 | `rsa-keygen` | RSA 키쌍 생성 (키 길이, 공개 지수, PEM/DER, PKCS8/PKCS1, SPKI/PKCS1, 개인키 비밀번호) |
| 2 | `rsa-encrypt` | 공개키 암호화 (기본 OAEP-SHA256, 선택 PKCS#1 v1.5) |
| 2-1 | `rsa-decrypt` | 공개키 입력 시 "개인키로 암호화된" 데이터 복원, 개인키 입력 시 표준 복호화 (키 종류 자동 판별) |
| 3 | `aes-keygen` | AES 키 생성 (128/192/256, 기본 128). seed 생략 시 CSPRNG, seed 지정 시 PBKDF2-HMAC-SHA256 결정적 파생 |
| 4 | `aes-encrypt` | AES 암호화 (기본 GCM, 선택 CBC) |
| 5 | `aes-decrypt` | AES 복호화 |
| 6 | `b64-encode` | Base64 인코딩 (표준 / URL-safe / 패딩 제거) |
| 7 | `b64-decode` | Base64 디코딩 |

### 요구사항

- Python 3.9 이상 (검증: Python 3.13)
- `cryptography` 41 이상 (검증: 50.0.1)
- 표준 라이브러리만으로는 동작하지 않습니다(Python 표준 라이브러리에 RSA·AES 구현이 없음).

### 설치

**방법 A. 설치 스크립트**

```bash
# Linux / macOS
./install.sh            # 기본: ~/.hermes/skills/crypto/crypto-cli
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

스크립트는 `cryptography` 설치(없을 때만) → 스킬 폴더 복사 → `selftest.py` 실행 순으로 동작합니다.
대상 경로에 이미 스킬이 있으면 덮어쓰지 않고 중단합니다(`--force` / `-Force` 로 덮어쓰기).

**방법 B. 수동**

```bash
python3 -m pip install -r requirements.txt
mkdir -p ~/.hermes/skills/crypto
cp -r skills/crypto/crypto-cli ~/.hermes/skills/crypto/
python3 ~/.hermes/skills/crypto/crypto-cli/scripts/selftest.py   # → ALL PASSED
```

설치 후 **새 Hermes 세션**을 시작하면 스킬이 인식됩니다. 확인: `hermes skills list` 또는 대화에서 `/skills`.

**오프라인(폐쇄망) 설치**

인터넷이 되는 PC에서 대상 OS/Python 에 맞는 wheel 을 받아 옮깁니다.

```bash
# 예: 대상이 Windows x64, Python 3.12
pip download "cryptography>=41" --only-binary=:all: --platform win_amd64 --python-version 3.12 -d wheels
# 대상 PC
pip install --no-index --find-links wheels cryptography
```

`cffi`, `pycparser` 등 의존 wheel 도 함께 받아집니다. 플랫폼 태그는 대상 환경에 맞게 바꾸세요.

### Hermes 없이 단독 사용

```bash
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py --help
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py <명령> --help
```

명령별 상세 옵션·예시는 `skills/crypto/crypto-cli/SKILL.md`, 바이트 포맷과 타 언어 연동은 `references/formats.md` 를 참고하세요.

### 보안 주의사항

- 개인키·AES 키를 `-d`/`-k` 문자열로 넘기면 쉘 히스토리·에이전트 로그에 남을 수 있습니다. 가능하면 파일(`-f`, `-k @파일`, `-o`)을 쓰세요.
- 개인키는 `-p` 로 비밀번호 보호를 권장합니다. POSIX 에서는 권한 600 으로 저장합니다(Windows 는 ACL 별도 관리 필요).
- seed 기반 AES 키는 seed 의 엔트로피만큼만 안전합니다. 운영 키는 seed 없이 생성하세요.
- 공개키로 복원되는 데이터(개인키 암호화)는 기밀성이 없습니다. 신규 설계에서는 RSA-PSS 서명을 쓰는 것이 표준입니다.
- CBC 는 무결성 검증이 없습니다. 호환 요구가 없으면 GCM(기본)을 쓰세요.

### 검증 내역 (2026-10-29)

- `selftest.py` 35개 항목 통과: 키 생성 옵션 조합, RSA OAEP/PKCS1 왕복, 암호화된 개인키, 공개키 복호화(바이너리/base64), AES 128/192/256·GCM/CBC 왕복, GCM 변조·AAD 불일치 탐지, seed 결정성 및 PBKDF2 명세 일치, Base64 표준/URL-safe/stdin, 오류 입력 거부
- OpenSSL 3.0.13 교차 검증: OAEP-SHA256 양방향, `pkeyutl -sign`(PKCS1) 결과의 공개키 복원

### 업데이트 기록

[CHANGELOG.md](CHANGELOG.md) 참조. 현재 버전: **1.1.1**

### 라이선스

MIT — [LICENSE](LICENSE) 참조.

---

## English

**CryptoCLI** is a Python command-line tool for everyday RSA, AES and Base64 tasks, packaged as a ready-to-use skill for [Hermes Agent](https://hermes-agent.nousresearch.com/).

- **RSA** — key-pair generation (key size, public exponent, PEM/DER, PKCS#8/PKCS#1, password-protected private keys), public-key encryption (OAEP-SHA256 / PKCS#1 v1.5), and decryption (standard private-key decryption, plus public-key recovery of data encrypted with a private key)
- **AES** — 128/192/256-bit key generation (CSPRNG, or deterministic PBKDF2 derivation from a seed), GCM (default) and CBC encryption/decryption
- **Base64** — standard, URL-safe and unpadded encoding/decoding
- **Agent-friendly** — single file, clear exit codes, results on stdout and status on stderr, input via `-d`, `-f` or stdin, and a `SKILL.md` with rules for handling secrets
- **Tested** — 35-check self-test (`selftest.py`), cross-checked against OpenSSL, with a format reference for C#, Java and OpenSSL interoperability

Built on the widely used [pyca/cryptography](https://cryptography.io/) library, with weak settings (RSA below 2048 bits, GCM nonce reuse, etc.) blocked by default.

### Quick install

```bash
git clone https://github.com/cychoi9198/CryptoCLI.git
cd CryptoCLI
./install.sh                 # Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Layout

```
CryptoCLI/
├── README.md                      ← this document (installation & operation)
├── LICENSE                        ← MIT
├── CHANGELOG.md                   ← change history (3 languages)
├── requirements.txt               ← cryptography>=41
├── install.sh                     ← installer for Linux/macOS
├── install.ps1                    ← installer for Windows
└── skills/crypto/crypto-cli/      ← the Hermes skill itself (install this whole folder)
    ├── SKILL.md                   ← usage procedure for the agent
    ├── scripts/
    │   ├── crypto_cli.py          ← the CLI (single file)
    │   └── selftest.py            ← 35-check self-test
    └── references/
        └── formats.md             ← byte layouts, algorithm parameters, C#/Java/OpenSSL interop (3 languages)
```

### Features

| # | Command | Description |
|---|---|---|
| 1 | `rsa-keygen` | Generate an RSA key pair (key size, public exponent, PEM/DER, PKCS8/PKCS1, SPKI/PKCS1, private-key password) |
| 2 | `rsa-encrypt` | Public-key encryption (default OAEP-SHA256, optional PKCS#1 v1.5) |
| 2-1 | `rsa-decrypt` | With a public key: recover data "encrypted with the private key". With a private key: standard decryption (key type detected automatically) |
| 3 | `aes-keygen` | Generate an AES key (128/192/256, default 128). CSPRNG without a seed; deterministic PBKDF2-HMAC-SHA256 derivation with a seed |
| 4 | `aes-encrypt` | AES encryption (default GCM, optional CBC) |
| 5 | `aes-decrypt` | AES decryption |
| 6 | `b64-encode` | Base64 encoding (standard / URL-safe / no padding) |
| 7 | `b64-decode` | Base64 decoding |

### Requirements

- Python 3.9 or later (tested: Python 3.13)
- `cryptography` 41 or later (tested: 50.0.1)
- It does not work with the standard library alone (Python's standard library has no RSA or AES implementation).

### Installation

**Option A. Installer script**

```bash
# Linux / macOS
./install.sh            # default: ~/.hermes/skills/crypto/crypto-cli
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The script installs `cryptography` (only if missing), copies the skill folder, then runs `selftest.py`.
If the skill already exists at the destination it stops without overwriting (use `--force` / `-Force` to overwrite).

**Option B. Manual**

```bash
python3 -m pip install -r requirements.txt
mkdir -p ~/.hermes/skills/crypto
cp -r skills/crypto/crypto-cli ~/.hermes/skills/crypto/
python3 ~/.hermes/skills/crypto/crypto-cli/scripts/selftest.py   # → ALL PASSED
```

Start a **new Hermes session** after installing and the skill will be picked up. Check with `hermes skills list` or `/skills` in a conversation.

**Offline (air-gapped) installation**

On a machine with internet access, download wheels matching the target OS/Python and carry them over.

```bash
# Example: target is Windows x64, Python 3.12
pip download "cryptography>=41" --only-binary=:all: --platform win_amd64 --python-version 3.12 -d wheels
# On the target machine
pip install --no-index --find-links wheels cryptography
```

Dependency wheels such as `cffi` and `pycparser` are downloaded too. Adjust the platform tag to the target environment.

### Standalone use (without Hermes)

```bash
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py --help
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py <command> --help
```

See `skills/crypto/crypto-cli/SKILL.md` for per-command options and examples, and `references/formats.md` for byte formats and interoperability with other languages.

### Security notes

- Passing private keys or AES keys as `-d`/`-k` strings can leave them in shell history or agent logs. Prefer files (`-f`, `-k @file`, `-o`).
- Protecting private keys with `-p` is recommended. On POSIX systems they are saved with mode 600 (on Windows, manage ACLs separately).
- A seed-derived AES key is only as strong as the seed's entropy. Generate production keys without a seed.
- Data recoverable with a public key (private-key encryption) has no confidentiality. For new designs, RSA-PSS signatures are the standard choice.
- CBC provides no integrity check. Use GCM (the default) unless compatibility requires otherwise.

### Verification (2026-10-29)

- `selftest.py`, 35 checks passed: key-generation option combinations, RSA OAEP/PKCS1 round trips, encrypted private keys, public-key decryption (binary/base64), AES 128/192/256 GCM/CBC round trips, detection of GCM tampering and AAD mismatch, seed determinism and conformance to the PBKDF2 spec, Base64 standard/URL-safe/stdin, rejection of invalid input
- Cross-checked with OpenSSL 3.0.13: OAEP-SHA256 in both directions, public-key recovery of `pkeyutl -sign` (PKCS1) output

### Changelog

See [CHANGELOG.md](CHANGELOG.md). Current version: **1.1.1**

### License

MIT — see [LICENSE](LICENSE).

---

## 日本語

**CryptoCLI** は、RSA・AES・Base64 の処理をコマンド 1 行で行える Python CLI であり、[Hermes Agent](https://hermes-agent.nousresearch.com/) からそのまま利用できるスキルパッケージです。

- **RSA** — 鍵ペア生成（鍵長・公開指数・PEM/DER・PKCS#8/PKCS#1・秘密鍵のパスワード保護）、公開鍵による暗号化（OAEP-SHA256 / PKCS#1 v1.5）、復号（秘密鍵による標準的な復号に加え、秘密鍵で暗号化されたデータの公開鍵による復元）
- **AES** — 128/192/256bit 鍵生成（CSPRNG、または seed から PBKDF2 による決定的導出）、GCM（既定）・CBC による暗号化/復号
- **Base64** — 標準・URL-safe・パディング省略のエンコード/デコード
- **エージェント向け設計** — 単一ファイル、明確な終了コード、結果は stdout・状態は stderr、`-d`・`-f`・stdin による入力、機密データの取り扱いルールを記した `SKILL.md`
- **検証済み** — 35 項目のセルフテスト（`selftest.py`）と OpenSSL とのクロス検証、C#・Java・OpenSSL 連携用フォーマット資料を同梱

広く使われている暗号ライブラリ [pyca/cryptography](https://cryptography.io/) 上で動作し、脆弱な設定（2048bit 未満の RSA、GCM nonce の再利用など）は既定で拒否します。

### クイックインストール

```bash
git clone https://github.com/cychoi9198/CryptoCLI.git
cd CryptoCLI
./install.sh                 # Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### 構成

```
CryptoCLI/
├── README.md                      ← 本ドキュメント（インストール・運用案内）
├── LICENSE                        ← MIT
├── CHANGELOG.md                   ← 更新履歴（3 言語）
├── requirements.txt               ← cryptography>=41
├── install.sh                     ← Linux/macOS 用インストールスクリプト
├── install.ps1                    ← Windows 用インストールスクリプト
└── skills/crypto/crypto-cli/      ← Hermes スキル本体（このフォルダごとインストール）
    ├── SKILL.md                   ← エージェント向けの利用手順
    ├── scripts/
    │   ├── crypto_cli.py          ← CLI 本体（単一ファイル）
    │   └── selftest.py            ← 35 項目のセルフテスト
    └── references/
        └── formats.md             ← バイト配置・アルゴリズムパラメータ、C#/Java/OpenSSL 連携（3 言語）
```

### 機能

| # | コマンド | 説明 |
|---|---|---|
| 1 | `rsa-keygen` | RSA 鍵ペア生成（鍵長、公開指数、PEM/DER、PKCS8/PKCS1、SPKI/PKCS1、秘密鍵パスワード） |
| 2 | `rsa-encrypt` | 公開鍵による暗号化（既定 OAEP-SHA256、選択 PKCS#1 v1.5） |
| 2-1 | `rsa-decrypt` | 公開鍵を指定すると「秘密鍵で暗号化された」データを復元、秘密鍵を指定すると標準的な復号（鍵の種類は自動判別） |
| 3 | `aes-keygen` | AES 鍵生成（128/192/256、既定 128）。seed 省略時は CSPRNG、seed 指定時は PBKDF2-HMAC-SHA256 による決定的導出 |
| 4 | `aes-encrypt` | AES 暗号化（既定 GCM、選択 CBC） |
| 5 | `aes-decrypt` | AES 復号 |
| 6 | `b64-encode` | Base64 エンコード（標準 / URL-safe / パディング除去） |
| 7 | `b64-decode` | Base64 デコード |

### 動作要件

- Python 3.9 以上（検証環境: Python 3.13）
- `cryptography` 41 以上（検証環境: 50.0.1）
- 標準ライブラリだけでは動作しません（Python の標準ライブラリには RSA・AES の実装がありません）。

### インストール

**方法 A. インストールスクリプト**

```bash
# Linux / macOS
./install.sh            # 既定: ~/.hermes/skills/crypto/crypto-cli
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

スクリプトは `cryptography` のインストール（未導入の場合のみ）→ スキルフォルダのコピー → `selftest.py` の実行、の順に動作します。
インストール先にすでにスキルがある場合は上書きせずに中止します（上書きするには `--force` / `-Force`）。

**方法 B. 手動**

```bash
python3 -m pip install -r requirements.txt
mkdir -p ~/.hermes/skills/crypto
cp -r skills/crypto/crypto-cli ~/.hermes/skills/crypto/
python3 ~/.hermes/skills/crypto/crypto-cli/scripts/selftest.py   # → ALL PASSED
```

インストール後に **新しい Hermes セッション** を開始するとスキルが認識されます。確認方法: `hermes skills list`、または会話中で `/skills`。

**オフライン（閉域網）インストール**

インターネットに接続できる PC で、対象の OS/Python に合った wheel を取得して持ち込みます。

```bash
# 例: 対象が Windows x64、Python 3.12 の場合
pip download "cryptography>=41" --only-binary=:all: --platform win_amd64 --python-version 3.12 -d wheels
# 対象 PC で
pip install --no-index --find-links wheels cryptography
```

`cffi`、`pycparser` などの依存 wheel も一緒に取得されます。プラットフォームタグは対象環境に合わせて変更してください。

### Hermes を使わない単体利用

```bash
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py --help
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py <コマンド> --help
```

コマンドごとの詳細オプションと例は `skills/crypto/crypto-cli/SKILL.md`、バイト形式と他言語との連携は `references/formats.md` を参照してください。

### セキュリティ上の注意

- 秘密鍵や AES 鍵を `-d`/`-k` の文字列で渡すと、シェル履歴やエージェントのログに残る場合があります。可能な限りファイル（`-f`、`-k @ファイル`、`-o`）を使用してください。
- 秘密鍵は `-p` によるパスワード保護を推奨します。POSIX 環境では権限 600 で保存されます（Windows では ACL を別途管理してください）。
- seed から導出した AES 鍵の強度は seed のエントロピーを超えません。本番用の鍵は seed なしで生成してください。
- 公開鍵で復元できるデータ（秘密鍵による暗号化）には機密性がありません。新規設計では RSA-PSS 署名を使うのが標準です。
- CBC には完全性の検証がありません。互換性の要件がなければ GCM（既定）を使用してください。

### 検証履歴（2026-10-29）

- `selftest.py` 35 項目合格: 鍵生成オプションの組み合わせ、RSA OAEP/PKCS1 の往復、暗号化された秘密鍵、公開鍵による復号（バイナリ/base64）、AES 128/192/256・GCM/CBC の往復、GCM の改ざん・AAD 不一致の検出、seed の決定性と PBKDF2 仕様との一致、Base64 標準/URL-safe/stdin、不正入力の拒否
- OpenSSL 3.0.13 とのクロス検証: OAEP-SHA256 の双方向、`pkeyutl -sign`（PKCS1）出力の公開鍵による復元

### 更新履歴

[CHANGELOG.md](CHANGELOG.md) を参照してください。現在のバージョン: **1.1.1**

### ライセンス

MIT — [LICENSE](LICENSE) を参照してください。

---

## 참고 문서 · References · 参考資料

- Hermes Agent — Creating Skills: https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- Hermes Agent — Work with Skills: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills
- RFC 8017 PKCS #1 v2.2 (IETF, 2016): https://www.rfc-editor.org/rfc/rfc8017
- NIST SP 800-38D (GCM, 2007): https://csrc.nist.gov/pubs/sp/800/38/d/final
- NIST SP 800-57 Part 1 Rev.5 (2020): https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- RFC 4648 Base64 (IETF, 2006): https://www.rfc-editor.org/rfc/rfc4648
- OWASP Password Storage Cheat Sheet (PBKDF2 iterations): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- pyca/cryptography RSA: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
