# crypto-cli — Data Format Specification

**[한국어](#한국어) · [English](#english) · [日本語](#日本語)**

---

## 한국어

다른 언어(C#, Java 등)·시스템과 연동할 때 맞춰야 하는 바이트 배치와 알고리즘 파라미터입니다.

### 1. RSA

| 항목 | 값 |
|---|---|
| 키 생성 | `rsa.generate_private_key(public_exponent, key_size)` (pyca/cryptography, OpenSSL 백엔드) |
| 개인키 파일 | PKCS#8 (`BEGIN PRIVATE KEY` / 암호화 시 `BEGIN ENCRYPTED PRIVATE KEY`) 또는 PKCS#1 (`BEGIN RSA PRIVATE KEY`) |
| 공개키 파일 | SPKI/X.509 (`BEGIN PUBLIC KEY`) 또는 PKCS#1 (`BEGIN RSA PUBLIC KEY`) |
| 개인키 암호화 | `BestAvailableEncryption` (cryptography 버전에 따라 알고리즘이 정해짐. 상호운용이 중요하면 OpenSSL 로 열리는지 확인) |
| 파일명 | `<name>_private.<pem\|der>`, `<name>_public.<pem\|der>` |

**rsa-encrypt (공개키 암호화)**
- 기본: RSAES-OAEP, Hash = SHA-256, MGF1 = SHA-256, label 없음
- 선택: RSAES-PKCS1-v1_5 (type 2)
- 출력 길이 = 키 길이 바이트 (2048bit → 256B)

| 상대 플랫폼 | 대응 설정 |
|---|---|
| C# (.NET) | `rsa.Encrypt(data, RSAEncryptionPadding.OaepSHA256)` — .NET 의 OaepSHA256 은 MGF1 도 SHA-256 |
| Java | `Cipher.getInstance("RSA/ECB/OAEPPadding")` + `OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT)` — `RSA/ECB/OAEPWithSHA-256AndMGF1Padding` 만 쓰면 SunJCE 는 MGF1 을 SHA-1 로 사용하므로 주의 |
| OpenSSL | `openssl pkeyutl -encrypt -pubin -inkey pub.pem -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256` |

**rsa-decrypt**
- 개인키: 위 encrypt 의 역연산 (기본 OAEP-SHA256)
- 공개키: EMSA-PKCS1-v1_5 type 1 블록(`00 01 FF..FF 00 || data`)을 복원하고 data 를 그대로 반환 (DigestInfo 해석 안 함)
  - 생성 측 예: OpenSSL `RSA_private_encrypt(..., RSA_PKCS1_PADDING)` / `openssl pkeyutl -sign -inkey priv.pem -pkeyopt rsa_padding_mode:pkcs1` (digest 미지정) / Java `Cipher("RSA/ECB/PKCS1Padding")` 를 PRIVATE_KEY 로 init

### 2. AES

**키 생성 (aes-keygen)**
- seed 없음: `secrets.token_bytes(bits/8)` (OS CSPRNG)
- seed 있음: `PBKDF2-HMAC-SHA256(password = UTF-8(seed), salt, iterations, dkLen = bits/8)`
  - salt 기본값 = UTF-8 `crypto_cli.aes-keygen.v1`
  - iterations 기본값 = 600000
- 출력: hex(기본) 또는 base64 텍스트 한 줄

**암호문 바이트 배치**

| 모드 | 배치 | 비고 |
|---|---|---|
| GCM (기본) | `nonce(12) ‖ ciphertext ‖ tag(16)` | nonce 는 매번 랜덤, AAD 선택 |
| CBC | `IV(16) ‖ ciphertext` | PKCS#7 패딩, 무결성 없음 |

- `--output-format base64`(기본) 이면 위 전체 바이트를 표준 Base64 로 인코딩한 한 줄.
- C# 연동: `AesGcm` 은 `Decrypt(nonce, ciphertext, tag, plaintext, aad)` 로 tag 를 분리해서 받으므로 마지막 16바이트를 잘라 전달.
- Java 연동: `Cipher("AES/GCM/NoPadding")` + `GCMParameterSpec(128, nonce)` 에 `ciphertext ‖ tag` 를 그대로 전달.

### 3. Base64
- 표준: RFC 4648 §4 (`+/`, `=` 패딩)
- `--url-safe`: RFC 4648 §5 (`-_`)
- `--no-padding`: 끝의 `=` 제거
- 디코딩 시 공백·줄바꿈 무시, 누락된 `=` 자동 보정, 그 외 문자는 오류

---

## English

Byte layouts and algorithm parameters you need to match when interoperating with other languages (C#, Java, etc.) or systems.

### 1. RSA

| Item | Value |
|---|---|
| Key generation | `rsa.generate_private_key(public_exponent, key_size)` (pyca/cryptography, OpenSSL backend) |
| Private key file | PKCS#8 (`BEGIN PRIVATE KEY` / `BEGIN ENCRYPTED PRIVATE KEY` when encrypted) or PKCS#1 (`BEGIN RSA PRIVATE KEY`) |
| Public key file | SPKI/X.509 (`BEGIN PUBLIC KEY`) or PKCS#1 (`BEGIN RSA PUBLIC KEY`) |
| Private key encryption | `BestAvailableEncryption` (the algorithm depends on the cryptography version; if interoperability matters, confirm that OpenSSL can open the key) |
| File names | `<name>_private.<pem\|der>`, `<name>_public.<pem\|der>` |

**rsa-encrypt (public-key encryption)**
- Default: RSAES-OAEP, Hash = SHA-256, MGF1 = SHA-256, no label
- Optional: RSAES-PKCS1-v1_5 (type 2)
- Output length = key length in bytes (2048 bits → 256 B)

| Counterpart | Matching setting |
|---|---|
| C# (.NET) | `rsa.Encrypt(data, RSAEncryptionPadding.OaepSHA256)` — .NET's OaepSHA256 also uses SHA-256 for MGF1 |
| Java | `Cipher.getInstance("RSA/ECB/OAEPPadding")` + `OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT)` — note that with `RSA/ECB/OAEPWithSHA-256AndMGF1Padding` alone, SunJCE uses SHA-1 for MGF1 |
| OpenSSL | `openssl pkeyutl -encrypt -pubin -inkey pub.pem -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256` |

**rsa-decrypt**
- Private key: the inverse of encrypt above (default OAEP-SHA256)
- Public key: recovers the EMSA-PKCS1-v1_5 type 1 block (`00 01 FF..FF 00 || data`) and returns data as-is (DigestInfo is not parsed)
  - Producer examples: OpenSSL `RSA_private_encrypt(..., RSA_PKCS1_PADDING)` / `openssl pkeyutl -sign -inkey priv.pem -pkeyopt rsa_padding_mode:pkcs1` (no digest) / Java `Cipher("RSA/ECB/PKCS1Padding")` initialised with PRIVATE_KEY

### 2. AES

**Key generation (aes-keygen)**
- Without a seed: `secrets.token_bytes(bits/8)` (OS CSPRNG)
- With a seed: `PBKDF2-HMAC-SHA256(password = UTF-8(seed), salt, iterations, dkLen = bits/8)`
  - Default salt = UTF-8 `crypto_cli.aes-keygen.v1`
  - Default iterations = 600000
- Output: one line of hex (default) or base64 text

**Ciphertext byte layout**

| Mode | Layout | Notes |
|---|---|---|
| GCM (default) | `nonce(12) ‖ ciphertext ‖ tag(16)` | random nonce every time, optional AAD |
| CBC | `IV(16) ‖ ciphertext` | PKCS#7 padding, no integrity |

- With `--output-format base64` (default), the whole byte string above is encoded as one line of standard Base64.
- C# interop: `AesGcm` takes the tag separately via `Decrypt(nonce, ciphertext, tag, plaintext, aad)`, so split off the last 16 bytes.
- Java interop: pass `ciphertext ‖ tag` as-is to `Cipher("AES/GCM/NoPadding")` with `GCMParameterSpec(128, nonce)`.

### 3. Base64
- Standard: RFC 4648 §4 (`+/`, `=` padding)
- `--url-safe`: RFC 4648 §5 (`-_`)
- `--no-padding`: strips trailing `=`
- When decoding, whitespace and line breaks are ignored and missing `=` is restored automatically; any other character is an error

---

## 日本語

他の言語（C#、Java など）やシステムと連携する際に合わせる必要があるバイト配置とアルゴリズムパラメータです。

### 1. RSA

| 項目 | 値 |
|---|---|
| 鍵生成 | `rsa.generate_private_key(public_exponent, key_size)`（pyca/cryptography、OpenSSL バックエンド） |
| 秘密鍵ファイル | PKCS#8（`BEGIN PRIVATE KEY` / 暗号化時は `BEGIN ENCRYPTED PRIVATE KEY`）または PKCS#1（`BEGIN RSA PRIVATE KEY`） |
| 公開鍵ファイル | SPKI/X.509（`BEGIN PUBLIC KEY`）または PKCS#1（`BEGIN RSA PUBLIC KEY`） |
| 秘密鍵の暗号化 | `BestAvailableEncryption`（アルゴリズムは cryptography のバージョンによって決まります。相互運用性が重要な場合は OpenSSL で開けるか確認してください） |
| ファイル名 | `<name>_private.<pem\|der>`、`<name>_public.<pem\|der>` |

**rsa-encrypt（公開鍵による暗号化）**
- 既定: RSAES-OAEP、Hash = SHA-256、MGF1 = SHA-256、label なし
- 選択: RSAES-PKCS1-v1_5（type 2）
- 出力長 = 鍵長のバイト数（2048bit → 256B）

| 連携先 | 対応する設定 |
|---|---|
| C# (.NET) | `rsa.Encrypt(data, RSAEncryptionPadding.OaepSHA256)` — .NET の OaepSHA256 は MGF1 にも SHA-256 を使用 |
| Java | `Cipher.getInstance("RSA/ECB/OAEPPadding")` + `OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT)` — `RSA/ECB/OAEPWithSHA-256AndMGF1Padding` だけを指定すると SunJCE は MGF1 に SHA-1 を使うため注意 |
| OpenSSL | `openssl pkeyutl -encrypt -pubin -inkey pub.pem -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256` |

**rsa-decrypt**
- 秘密鍵: 上記 encrypt の逆演算（既定 OAEP-SHA256）
- 公開鍵: EMSA-PKCS1-v1_5 type 1 ブロック（`00 01 FF..FF 00 || data`）を復元し、data をそのまま返す（DigestInfo は解釈しない）
  - 生成側の例: OpenSSL `RSA_private_encrypt(..., RSA_PKCS1_PADDING)` / `openssl pkeyutl -sign -inkey priv.pem -pkeyopt rsa_padding_mode:pkcs1`（digest 指定なし）/ Java `Cipher("RSA/ECB/PKCS1Padding")` を PRIVATE_KEY で init

### 2. AES

**鍵生成（aes-keygen）**
- seed なし: `secrets.token_bytes(bits/8)`（OS の CSPRNG）
- seed あり: `PBKDF2-HMAC-SHA256(password = UTF-8(seed), salt, iterations, dkLen = bits/8)`
  - salt の既定値 = UTF-8 `crypto_cli.aes-keygen.v1`
  - iterations の既定値 = 600000
- 出力: hex（既定）または base64 テキスト 1 行

**暗号文のバイト配置**

| モード | 配置 | 備考 |
|---|---|---|
| GCM（既定） | `nonce(12) ‖ ciphertext ‖ tag(16)` | nonce は毎回ランダム、AAD は任意 |
| CBC | `IV(16) ‖ ciphertext` | PKCS#7 パディング、完全性なし |

- `--output-format base64`（既定）の場合、上記のバイト列全体を標準 Base64 で 1 行にエンコードします。
- C# 連携: `AesGcm` は `Decrypt(nonce, ciphertext, tag, plaintext, aad)` で tag を分けて受け取るため、末尾 16 バイトを切り出して渡します。
- Java 連携: `Cipher("AES/GCM/NoPadding")` + `GCMParameterSpec(128, nonce)` に `ciphertext ‖ tag` をそのまま渡します。

### 3. Base64
- 標準: RFC 4648 §4（`+/`、`=` パディング）
- `--url-safe`: RFC 4648 §5（`-_`）
- `--no-padding`: 末尾の `=` を除去
- デコード時は空白・改行を無視し、欠けた `=` を自動補完します。それ以外の文字はエラーになります
