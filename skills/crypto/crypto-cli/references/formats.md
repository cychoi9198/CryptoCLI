# crypto-cli 데이터 포맷 명세

다른 언어(C#, Java 등)·시스템과 연동할 때 맞춰야 하는 바이트 배치와 알고리즘 파라미터입니다.

## 1. RSA

| 항목 | 값 |
|---|---|
| 키 생성 | `rsa.generate_private_key(public_exponent, key_size)` (pyca/cryptography, OpenSSL 백엔드) |
| 개인키 파일 | PKCS#8 (`BEGIN PRIVATE KEY` / 암호화 시 `BEGIN ENCRYPTED PRIVATE KEY`) 또는 PKCS#1 (`BEGIN RSA PRIVATE KEY`) |
| 공개키 파일 | SPKI/X.509 (`BEGIN PUBLIC KEY`) 또는 PKCS#1 (`BEGIN RSA PUBLIC KEY`) |
| 개인키 암호화 | `BestAvailableEncryption` (cryptography 버전에 따라 알고리즘이 정해짐. 상호운용이 중요하면 OpenSSL 로 열리는지 확인) |
| 파일명 | `<name>_private.<pem\|der>`, `<name>_public.<pem\|der>` |

### rsa-encrypt (공개키 암호화)
- 기본: RSAES-OAEP, Hash = SHA-256, MGF1 = SHA-256, label 없음
- 선택: RSAES-PKCS1-v1_5 (type 2)
- 출력 길이 = 키 길이 바이트 (2048bit → 256B)

| 상대 플랫폼 | 대응 설정 |
|---|---|
| C# (.NET) | `rsa.Encrypt(data, RSAEncryptionPadding.OaepSHA256)` — .NET 의 OaepSHA256 은 MGF1 도 SHA-256 |
| Java | `Cipher.getInstance("RSA/ECB/OAEPPadding")` + `OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT)` — `RSA/ECB/OAEPWithSHA-256AndMGF1Padding` 만 쓰면 SunJCE 는 MGF1 을 SHA-1 로 사용하므로 주의 |
| OpenSSL | `openssl pkeyutl -encrypt -pubin -inkey pub.pem -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256` |

### rsa-decrypt
- 개인키: 위 encrypt 의 역연산 (기본 OAEP-SHA256)
- 공개키: EMSA-PKCS1-v1_5 type 1 블록(`00 01 FF..FF 00 || data`)을 복원하고 data 를 그대로 반환 (DigestInfo 해석 안 함)
  - 생성 측 예: OpenSSL `RSA_private_encrypt(..., RSA_PKCS1_PADDING)` / `openssl pkeyutl -sign -inkey priv.pem -pkeyopt rsa_padding_mode:pkcs1` (digest 미지정) / Java `Cipher("RSA/ECB/PKCS1Padding")` 를 PRIVATE_KEY 로 init

## 2. AES

### 키 생성 (aes-keygen)
- seed 없음: `secrets.token_bytes(bits/8)` (OS CSPRNG)
- seed 있음: `PBKDF2-HMAC-SHA256(password = UTF-8(seed), salt, iterations, dkLen = bits/8)`
  - salt 기본값 = UTF-8 `crypto_cli.aes-keygen.v1`
  - iterations 기본값 = 600000
- 출력: hex(기본) 또는 base64 텍스트 한 줄

### 암호문 바이트 배치
| 모드 | 배치 | 비고 |
|---|---|---|
| GCM (기본) | `nonce(12) ‖ ciphertext ‖ tag(16)` | nonce 는 매번 랜덤, AAD 선택 |
| CBC | `IV(16) ‖ ciphertext` | PKCS#7 패딩, 무결성 없음 |

- `--output-format base64`(기본) 이면 위 전체 바이트를 표준 Base64 로 인코딩한 한 줄.
- C# 연동: `AesGcm` 은 `Decrypt(nonce, ciphertext, tag, plaintext, aad)` 로 tag 를 분리해서 받으므로 마지막 16바이트를 잘라 전달.
- Java 연동: `Cipher("AES/GCM/NoPadding")` + `GCMParameterSpec(128, nonce)` 에 `ciphertext ‖ tag` 를 그대로 전달.

## 3. Base64
- 표준: RFC 4648 §4 (`+/`, `=` 패딩)
- `--url-safe`: RFC 4648 §5 (`-_`)
- `--no-padding`: 끝의 `=` 제거
- 디코딩 시 공백·줄바꿈 무시, 누락된 `=` 자동 보정, 그 외 문자는 오류
