---
name: crypto-cli
description: RSA keygen/encrypt/decrypt, AES-128/192/256 keygen/encrypt/decrypt (GCM, CBC) and Base64 encode/decode via a local Python CLI. Use when asked to generate RSA or AES keys, encrypt/decrypt data, recover data encrypted with an RSA private key using a public key, or convert data to/from Base64. (RSA·AES 키 생성, 암·복호화, Base64 변환)
version: 1.1.0
author: CCY
license: MIT
metadata:
  hermes:
    category: crypto
    tags: [crypto, rsa, aes, base64, encryption, cli]
    requires_toolsets: [terminal]
---

# crypto-cli

`${HERMES_SKILL_DIR}/scripts/crypto_cli.py` 하나로 동작하는 암호화 CLI 사용 절차입니다.
아래 명령 예시의 `CLI` 는 다음 명령을 뜻합니다.

```bash
python3 ${HERMES_SKILL_DIR}/scripts/crypto_cli.py
```

Windows 에서는 `python3` 대신 `python` 또는 `py` 를 사용합니다.

## When to Use

- RSA 키쌍 생성, RSA 공개키 암호화, RSA 복호화(공개키 또는 개인키)
- AES 키 생성(랜덤 또는 seed 기반 결정적 파생), AES 암호화/복호화
- 문자열/파일의 Base64 인코딩·디코딩
- 사용하지 말아야 할 경우: 전자서명 생성·검증(RSA-PSS 등), 인증서(X.509) 발급, 비밀번호 해싱 → 이 CLI 범위 밖이므로 사용자에게 알린다.

## Prerequisites (최초 1회 확인)

1. `python3 --version` → 3.9 이상
2. `python3 -c "import cryptography; print(cryptography.__version__)"`
   - 실패하면 사용자 승인을 받은 뒤 `python3 -m pip install "cryptography>=41"` 실행
   - 폐쇄망이면 README.md 의 "오프라인 설치" 절차를 안내한다.

## Command Reference

입력 데이터는 모든 명령이 동일한 규칙을 따른다: `-d "문자열"` | `-f 파일경로` | (둘 다 없으면 stdin).
`-o 파일` 을 주면 파일로 저장하고, 없으면 stdout 으로 출력한다. 상태 메시지(`[OK]`, `[ERROR]`)는 stderr 로 나간다.
종료 코드: 성공 0, 실패 1.

| # | 명령 | 필수 인자 | 주요 옵션 (기본값) |
|---|---|---|---|
| 1 | `rsa-keygen` | – | `-b 2048` `-e 65537` `--format pem\|der` `--private-format pkcs8\|pkcs1` `--public-format spki\|pkcs1` `-p 비밀번호` `--out-dir .` `-n rsa` `--force` |
| 2 | `rsa-encrypt` | `-k 공개키` + 데이터 | `--padding oaep\|pkcs1` `--hash sha256` `--mgf-hash sha256` `--label` `--output-format base64\|hex\|raw` |
| 2-1 | `rsa-decrypt` | `-k 공개키 또는 개인키` + 데이터 | `-p 비밀번호` `--input-format base64\|hex\|raw` `--padding oaep\|pkcs1`(개인키만) `--output-format raw\|base64\|hex` |
| 3 | `aes-keygen` | – | `-b 128\|192\|256 (128)` `-s seed` `--salt` `--iterations 600000` `--output-format hex\|base64` `-o` |
| 4 | `aes-encrypt` | `-k 키` + 데이터 | `--key-format hex\|base64` `-m gcm\|cbc (gcm)` `--aad` `--iv`(CBC만) `--output-format base64\|hex\|raw` |
| 5 | `aes-decrypt` | `-k 키` + 데이터 | `--key-format` `-m` `--aad` `--input-format base64\|hex\|raw` |
| 6 | `b64-encode` | 데이터 | `--url-safe` `--no-padding` |
| 7 | `b64-decode` | 데이터 | `--url-safe` (공백·줄바꿈·패딩 누락 자동 보정) |

`-k` 는 키 문자열 또는 `@파일경로`(AES), 파일 경로 또는 PEM 문자열(RSA)을 받는다.
세부 포맷은 `${HERMES_SKILL_DIR}/references/formats.md` 참조.

## Procedure

1. 사용자의 요청을 위 표의 명령 하나 이상에 대응시킨다. 모호하면(예: "RSA 복호화"인데 키 종류 불명) 먼저 묻는다.
2. 키·암호문 등 민감 데이터는 가능하면 `-f`/`-o` 파일 경로로 주고받는다. (쉘 히스토리·로그에 남지 않도록)
3. 명령을 실행하고 종료 코드와 stderr 를 확인한다.
4. 결과를 사용자에게 전달한다. 개인키·AES 키 원문은 사용자가 명시적으로 요청한 경우에만 채팅에 출력하고, 기본은 저장 경로만 알린다.

### 예시

```bash
# RSA 3072 키쌍 (개인키 비밀번호 보호)
CLI rsa-keygen -b 3072 -p "<pw>" --out-dir ./keys -n svc

# RSA 암호화 → 개인키 복호화 왕복
CT=$(CLI rsa-encrypt -k ./keys/svc_public.pem -d "hello")
CLI rsa-decrypt -k ./keys/svc_private.pem -p "<pw>" -d "$CT"

# 상대 시스템이 '개인키로 암호화'한 데이터를 공개키로 복원
CLI rsa-decrypt -k partner_public.pem -f received.bin --input-format raw -o plain.bin

# AES-256 키 생성 → 파일 암·복호화
CLI aes-keygen -b 256 -o aes.key
CLI aes-encrypt -k @aes.key -f input.bin -o input.enc
CLI aes-decrypt -k @aes.key -f input.enc -o input.dec

# seed 기반 결정적 키 (같은 seed+salt+iterations → 같은 키)
CLI aes-keygen -b 128 -s "<seed>" --salt "<salt>"

# 큰 데이터: AES 로 데이터 암호화 + AES 키를 RSA 로 암호화 (하이브리드)
CLI aes-keygen -b 256 -o k.hex
CLI aes-encrypt -k @k.hex -f big.bin -o big.enc
CLI rsa-encrypt -k pub.pem -f k.hex -o k.enc

# Base64
CLI b64-encode -d "Hello 세계"
CLI b64-decode -d "SGVsbG8g7IS46rOE"
```

## Pitfalls

- **RSA 공개키로 복호화되는 것은 "개인키로 암호화된" 데이터(PKCS#1 v1.5 type 1)뿐이다.** `rsa-encrypt` 결과(공개키 암호화)는 개인키로만 복호화된다. 공개키 + OAEP 조합은 원리상 불가하며 CLI 가 거부한다.
- 공개키로 복원 가능한 데이터는 기밀성이 없다(공개키 보유자 누구나 복원). 새 설계라면 서명/검증(RSA-PSS)을 권고한다.
- RSA 평문 최대 길이: OAEP-SHA256 = 키바이트 − 66 (2048bit → 190B, 3072bit → 318B), PKCS#1 v1.5 = 키바이트 − 11. 초과 시 하이브리드 방식 사용.
- 암·복호화 양쪽의 `--padding`, `--hash`, `--mgf-hash`, `--label`, `-m`, `--aad` 가 정확히 같아야 한다.
- `aes-decrypt`/`rsa-decrypt` 의 기본 입력 형식은 base64 이다. 바이너리 파일이면 `--input-format raw`.
- `aes-encrypt -o` 는 기본으로 base64 **텍스트**를 저장한다. 바이너리로 저장하려면 `--output-format raw` (복호화 시 `--input-format raw`).
- seed 기반 AES 키의 강도는 seed 의 엔트로피를 넘지 못한다. 실제 운영 키는 seed 없이 생성한다.
- CBC 모드는 무결성 검증이 없다. 특별한 호환 요구가 없으면 GCM(기본)을 사용한다.
- RSA 2048bit 미만은 거부된다(`--allow-weak` 로 1024~2047 허용, 테스트 전용).
- 기존 키 파일은 덮어쓰지 않는다. 덮어쓰기는 사용자 확인 후 `--force`.

## Verification

- 설치 직후 또는 수정 후: `python3 ${HERMES_SKILL_DIR}/scripts/selftest.py` → 마지막 줄 `ALL PASSED`
- 개별 결과 검증: 암호화 직후 같은 옵션으로 복호화해 원문과 비교한다(`cmp` 또는 해시 비교).
