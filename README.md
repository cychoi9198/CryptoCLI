# CryptoCLI — Hermes Agent 스킬 패키지

RSA / AES / Base64 기능을 제공하는 Python CLI(`crypto_cli.py`)와, 이를 Hermes Agent 가 사용하도록 하는 스킬 `crypto-cli`(`SKILL.md`)를 묶은 패키지입니다.

## 빠른 설치 (GitHub)

```bash
git clone https://github.com/cychoi9198/CryptoCLI.git
cd CryptoCLI
./install.sh                 # Windows: powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## 구성

```
CryptoCLI/
├── README.md                      ← 이 문서 (설치·운영 안내)
├── LICENSE                        ← MIT
├── requirements.txt               ← cryptography>=41
├── install.sh                     ← Linux/macOS 설치 스크립트
├── install.ps1                    ← Windows 설치 스크립트
└── skills/crypto/crypto-cli/      ← Hermes 스킬 본체 (이 폴더를 통째로 설치)
    ├── SKILL.md                   ← 에이전트용 사용 절차 (When to Use / Procedure / Pitfalls / Verification)
    ├── scripts/
    │   ├── crypto_cli.py          ← CLI 본체 (단일 파일)
    │   └── selftest.py            ← 35개 항목 자체 검증
    └── references/
        └── formats.md             ← 바이트 배치·알고리즘 파라미터, C#/Java/OpenSSL 연동 표
```

## 기능

| # | 명령 | 설명 |
|---|---|---|
| 1 | `rsa-keygen` | RSA 키쌍 생성 (bits, public exponent, PEM/DER, PKCS8/PKCS1, SPKI/PKCS1, 개인키 비밀번호) |
| 2 | `rsa-encrypt` | 공개키 암호화 (기본 OAEP-SHA256, 선택 PKCS#1 v1.5) |
| 2-1 | `rsa-decrypt` | 공개키 입력 시 "개인키로 암호화된" 데이터 복원, 개인키 입력 시 표준 복호화 (키 종류 자동 판별) |
| 3 | `aes-keygen` | AES 키 생성 (128/192/256, 기본 128). seed 생략 시 CSPRNG, seed 지정 시 PBKDF2-HMAC-SHA256 결정적 파생 |
| 4 | `aes-encrypt` | AES 암호화 (기본 GCM, 선택 CBC) |
| 5 | `aes-decrypt` | AES 복호화 |
| 6 | `b64-encode` | Base64 인코딩 (표준 / URL-safe / 패딩 제거) |
| 7 | `b64-decode` | Base64 디코딩 |

## 요구사항

- Python 3.9 이상 (검증: Python 3.13)
- `cryptography` 41 이상 (검증: 50.0.1)
- 표준 라이브러리만으로는 동작하지 않습니다(Python 표준 라이브러리에 RSA·AES 구현이 없음).

## 설치

### 방법 A. 설치 스크립트

```bash
# Linux / macOS
./install.sh            # 기본: ~/.hermes/skills/crypto/crypto-cli
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

스크립트가 하는 일은 세 가지입니다: `cryptography` 설치(없을 때만) → 스킬 폴더 복사 → `selftest.py` 실행.
대상 경로에 이미 스킬이 있으면 덮어쓰지 않고 중단합니다(`--force` / `-Force` 로 덮어쓰기).

### 방법 B. 수동

```bash
python3 -m pip install -r requirements.txt
mkdir -p ~/.hermes/skills/crypto
cp -r skills/crypto/crypto-cli ~/.hermes/skills/crypto/
python3 ~/.hermes/skills/crypto/crypto-cli/scripts/selftest.py   # → ALL PASSED
```

설치 후 **새 Hermes 세션**을 시작하면 스킬이 인식됩니다. 확인: `hermes skills list` 또는 대화에서 `/skills`.

### 오프라인(폐쇄망) 설치

인터넷이 되는 PC에서 대상 OS/Python 에 맞는 wheel 을 받아 옮깁니다.

```bash
# 예: 대상이 Windows x64, Python 3.12
pip download "cryptography>=41" --only-binary=:all: --platform win_amd64 --python-version 3.12 -d wheels
# 대상 PC
pip install --no-index --find-links wheels cryptography
```

`cffi`, `pycparser` 등 의존 wheel 도 함께 받아집니다. 플랫폼 태그는 대상 환경에 맞게 바꾸세요.

## Hermes 없이 단독 사용

```bash
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py --help
python3 skills/crypto/crypto-cli/scripts/crypto_cli.py <명령> --help
```

명령별 상세 옵션·예시는 `skills/crypto/crypto-cli/SKILL.md`, 바이트 포맷과 타 언어 연동은 `references/formats.md` 를 참고하세요.

## 보안 주의사항

- 개인키·AES 키를 `-d`/`-k` 문자열로 넘기면 쉘 히스토리·에이전트 로그에 남을 수 있습니다. 가능하면 파일(`-f`, `-k @파일`, `-o`)을 쓰세요.
- 개인키는 `-p` 로 비밀번호 보호를 권장합니다. 생성 시 POSIX 에서는 권한 600 으로 저장합니다(Windows 는 ACL 별도 관리 필요).
- seed 기반 AES 키는 seed 엔트로피만큼만 안전합니다. 운영 키는 seed 없이 생성하세요.
- 공개키로 복원되는 데이터(개인키 암호화)는 기밀성이 없습니다. 신규 설계에서는 RSA-PSS 서명을 쓰는 것이 표준입니다.
- CBC 는 무결성 검증이 없습니다. 호환 요구가 없으면 GCM(기본)을 쓰세요.

## 검증 내역 (2026-10-29)

- `selftest.py` 35개 항목 통과: 키 생성 옵션 조합, RSA OAEP/PKCS1 왕복, 암호화 개인키, 공개키 복호화(바이너리/base64), AES 128/192/256·GCM/CBC 왕복, GCM 변조·AAD 불일치 탐지, seed 결정성 및 PBKDF2 명세 일치, Base64 표준/URL-safe/stdin, 오류 입력 거부
- OpenSSL 3.0.13 교차 검증: OAEP-SHA256 양방향, `pkeyutl -sign`(PKCS1) 결과의 공개키 복원

## 참고 문서

- Hermes Agent — Creating Skills: https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- Hermes Agent — Work with Skills: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills
- RFC 8017 PKCS #1 v2.2 (IETF, 2016): https://www.rfc-editor.org/rfc/rfc8017
- NIST SP 800-38D (GCM, 2007): https://csrc.nist.gov/pubs/sp/800/38/d/final
- NIST SP 800-57 Part 1 Rev.5 (2020): https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- RFC 4648 Base64 (IETF, 2006): https://www.rfc-editor.org/rfc/rfc4648
- OWASP Password Storage Cheat Sheet (PBKDF2 반복 횟수): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- pyca/cryptography RSA: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
