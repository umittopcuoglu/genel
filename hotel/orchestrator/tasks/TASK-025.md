---
id: TASK-025
modül: Faz 4 - Blockchain Guest Identity
kapsam: blockchain credential + self-sovereign identity + credential verification + zero-knowledge proof
durum: kuyrukta (Faz 3 tamamlanınca)
tur: —
bağımlılık: TASK-001 (guest identity), TASK-024 (mobile check-in), TASK-017 (KVKK/data protection)
---

# TASK-025 — Faz 4: Blockchain Misafir Kimliği — Self-Sovereign Identity (SSI)

> Misafir blockchain'de kendi "kimlik portföyü" yaratır → otel chain'inde tekrar check-in'de QR scan → identity otomatik doğrulama (manual data entry yok).

## 1. Veri Modeli

### `blockchain_identities`
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id nullable, ilk check-in'de null)
- did (VARCHAR 255, unique) — Decentralized Identifier (W3C standard, e.g., did:key:z6MkhaXg...)
- did_public_key (VARCHAR 1000) — EdDSA/secp256k1 public key
- did_private_key_encrypted (VARCHAR 2000) — AES-256 encrypted, guest'in mobile device'ında TBD
- credential_wallet (JSON) — {verifiable_credentials: [{type, issuer, claims, issued_at, expires_at}]}
- kyc_verified (BOOLEAN, default=false) — KYC (Know Your Customer) completed
- kyc_verified_at (DATETIME nullable)
- kyc_verified_by (UUID FK → users.id nullable, verifier)
- reputation_score (DECIMAL 5,2, default=0) — 0-100 (loyalty + compliance history)
- last_login_at (DATETIME nullable)
- device_fingerprint (VARCHAR 255 nullable) — mobile cihaz tanımlama
- status (VARCHAR 15, default="pending") — pending / active / revoked / expired
- created_at (auto)
- Index: did, guest_id, status

### `verifiable_credentials` (blockchain credentials)
- id (UUID, PK) [BaseModel]
- identity_id (UUID FK → blockchain_identities.id)
- credential_type (VARCHAR 50) — guest_profile / hotel_tier / loyalty_status / professional_license
- issuer_did (VARCHAR 255) — kimin verdiyse (otel, loyalty program, government)
- issuer_name (VARCHAR 100)
- subject_claims (JSON) — {name, email, passport_no, nationality, kyc_level: "tier1"/"tier2"/"tier3"}
- credential_signature (VARCHAR 500) — JWT signed credential
- issued_at (DATETIME)
- expires_at (DATETIME nullable)
- revocation_status (VARCHAR 15, default="active") — active / revoked / expired
- revoked_at (DATETIME nullable)
- revocation_reason (VARCHAR 200 nullable)
- linked_transaction (VARCHAR 255 nullable) — blockchain tx hash
- Index: identity_id, credential_type, revocation_status

### `identity_verification_proofs` (zero-knowledge proof'lar)
- id (UUID, PK) [BaseModel]
- identity_id (UUID FK → blockchain_identities.id)
- challenge_string (VARCHAR 255, unique) — random nonce (server ↔ client proof)
- proof_data (JSON) — {proof_type: "zk-snark", circuit: "age_verification", public_inputs: [...], proof: [...]}
- verification_type (VARCHAR 30) — age_over_18 / passport_validity / kyc_tier / no_sanctions
- verified (BOOLEAN, default=false)
- verified_at (DATETIME nullable)
- verification_timestamp (DATETIME)
- expiry_at (DATETIME) — proof validity (24h)
- Index: identity_id, verification_type

### `blockchain_sync_events` (blockchain log)
- id (UUID, PK) [BaseModel]
- identity_id (UUID FK → blockchain_identities.id)
- event_type (VARCHAR 30) — did_created / credential_issued / credential_revoked / verification_passed
- blockchain_network (VARCHAR 20, default="mock") — polygon_mumbai / ethereum_sepolia / mock_testnet
- transaction_hash (VARCHAR 255 nullable) — blockchain TX hash (public ledger)
- event_data (JSON) — {credential_type, issuer, claims_count, timestamp}
- status (VARCHAR 15, default="pending") — pending / confirmed / failed
- error_message (VARCHAR 500 nullable)
- confirmation_count (INT, default=0) — blockchain confirmations (10 için finality)
- created_at (auto)
- Index: identity_id, event_type, status

### `guest_consent_log` (misafir rıza kayıtları — KVKK TASK-017 ile entegre)
- id (UUID, PK) [BaseModel]
- identity_id (UUID FK → blockchain_identities.id)
- consent_type (VARCHAR 50) — blockchain_identity_creation / credential_sharing / kyc_verification / data_retention
- given_by (VARCHAR 50) — guest / manager / legal_representative
- given_at (DATETIME)
- consent_value (BOOLEAN) — true / false
- blockchain_recorded (BOOLEAN, default=false) — rıza blockchain'e kaydedildi mi
- blockchain_tx_hash (VARCHAR 255 nullable)
- expiry_at (DATETIME nullable) — rıza ne kadar süreyle geçerli
- Index: identity_id, consent_type

## 2. Endpoint'ler (Blockchain Identity API — /api/v1/blockchain/)

### `POST /api/v1/blockchain/identity/create`
- Auth: Guest (mobile app)
- Body: { guest_email, phone_number, accept_terms: true }
- İşlem: 
  - DID generate (did:key: method)
  - Public/private key pair create
  - blockchain_identities kaydı (status=pending)
  - Challenge string generate
- 201 döner { did, challenge, next_step: "email_verification" }

### `POST /api/v1/blockchain/identity/{did}/verify-email`
- Auth: Guest (challenge)
- Body: { email_code, challenge_response }
- İşlem: Email code doğrula → challenge geri (signed) → status=active
- 200 döner { did, status: "active", reputation_score, next_step: "kyc_verification" }

### `POST /api/v1/blockchain/identity/{did}/request-kyc`
- Auth: Guest, Manager
- Body: { kyc_data: {name, passport_no, address, nationality}, proof_of_identity: "document_scan_id" }
- İşlem: KYC kaydı create → manager approval kuyruğuna
- 201 döner { kyc_request_id, status: "pending_review", estimated_review_time: "2 hours" }

### `POST /api/v1/blockchain/identity/{did}/issue-credential`
- Auth: Manager, Superadmin (KYC verifier)
- Body: { credential_type: "guest_profile", claims: {name, kyc_level: "tier2"} }
- İşlem:
  - Credential JSON oluştur
  - JWT sign (otel private key ile)
  - blockchain_sync_events'e enqueue (async blockchain submission)
  - verifiable_credentials kaydı
- 201 döner { credential_id, credential_jwt, blockchain_status: "pending" }

### `POST /api/v1/blockchain/identity/{did}/checkin-proof`
- Auth: Guest (mobile check-in sırasında)
- Body: { challenge_string, proof: "signed_proof_data" }
- İşlem: Proof verify (did'nin public key ile) → zero-knowledge check
- 200 döner { proof_valid: true, reputation_score, guest_tier, access_granted: true }

### `GET /api/v1/blockchain/identity/{did}/wallet`
- Auth: Guest (kendi DID'i), Manager
- 200 döner { did, credentials: [{type, issuer, claims, issued_at, expires_at}], reputation_score, kyc_level, last_login }

### `POST /api/v1/blockchain/identity/{did}/share-credential`
- Auth: Guest
- Body: { credential_id, share_with_entity: "partner_hotel_chain", expiry_days: 7 }
- İşiem: Selective disclosure (claims'in subseti share et)
- 200 döner { share_token, shared_at, expires_at }

### `POST /api/v1/blockchain/identity/{did}/revoke-credential`
- Auth: Guest, Manager
- Body: { credential_id, reason: "lost_device" }
- İşlem:
  - verifiable_credentials.revocation_status = "revoked"
  - Blockchain'e revocation event push
  - reputation_score düşür (çok revoke ise)
- 200 döner { credential_id, revoked_at }

### `GET /api/v1/blockchain/identity/{did}/verification-history`
- Auth: Guest, Manager
- Query: ?days=30
- 200 döner { verifications: [{type, verified_at, proof_type, result}] }

## 3. İş Mantığı

1. **DID oluşturma:**
   - Guest mobil app'te DID creation başlatır
   - Backend: EdDSA key pair generate (crypto/nacl)
   - DID = did:key:{base58(public_key)} (W3C standard)
   - Public key Merkle tree'ye ekle (offchain index)

2. **KYC verification:**
   - Guest KYC data submit → Manager onay
   - Onay alınca "guest_profile" credential issue
   - Credential = JWT(claims={name, passport, kyc_level}, signed_by=otel_key, aud=did)
   - blockchain_sync_events'e: credential_issued event enqueue

3. **Blockchain sync (mock-first adapter):**
   - Async job: `integrations/blockchain/polygon_adapter.py`
   - Mock: transaction_hash = SHA256(event_data), status = confirmed (instant)
   - Real (ileride): Polygon Mumbai / Ethereum Sepolia testnet'e submit

4. **Check-in proof:**
   - Guest mobile app'ten check-in sırasında challenge string request
   - Client: DID'nin private key ile proof sign (Ed25519)
   - Server: Guest DID'nin public key ile proof verify
   - Verification passed → identity_verification_proofs kaydı + guest_consent_log

5. **Zero-knowledge proof (ZK-SNARK mock):**
   - Şimdilik mock: verification_type=age_over_18 için
   - Real (ilereira): age bilgisini açıklamadan "age > 18" prove et
   - Mock: proof_data = {circuit: "age_verification", public_inputs: ["21"], proof: "mock_proof"} (just JSON)

6. **Credential sharing:**
   - Selective disclosure: "kyc_level" share et ama passport_no share etme
   - Share token = JWT(credential_subset, expiry, audience=partner_chain_did)
   - Partner chain: share token'ı verify → guest Tier 2 olarak recognize

7. **Consent blockchain recording:**
   - KVKK compliance: her consent'i blockchain'e record et
   - Guest: "I consent to blockchain identity creation" → otel sign → blockchain TX
   - Immutable audit trail (GDPR deletion requests handle'lenebilir — selective revocation)

8. **Reputation scoring:**
   - Check-in: +1
   - Credential issued: +2
   - Credential revoked (fraud): -5
   - Score 0-100, < 50 ise "unverified", > 80 ise "trusted"

9. **Test ortamında:**
   - DID generation: real (crypto/nacl)
   - Blockchain: mock (tx_hash = SHA256, instant confirmation)
   - ZK-SNARK: mock JSON data
   - Async jobs: sync (no queue)

## 4. Minimum Test Sayısı

- [ ] 6 unit test (`test_blockchain_identity.py`):
  - DID generation + key pair
  - Credential issuing + JWT signing
  - Proof verification (Ed25519)
  - Credential sharing (selective disclosure)
  - Reputation score calculation
  - Consent logging

- [ ] 5 integration test (`test_blockchain_identity_e2e.py`):
  - Full identity creation → KYC → credential issuance
  - Check-in proof verification (identity intact)
  - Multi-hotel sharing (credential reuse)
  - Credential revocation
  - Blockchain sync (mock tx confirmation)

- [ ] 2 performance test:
  - 50 concurrent check-in proof verifications < 500ms each
  - Credential sharing validation < 100ms

## 5. Acceptance Criteria

- [ ] DID generation + public/private key management
- [ ] JWT credential format (W3C VC standard)
- [ ] Ed25519 proof verification
- [ ] Selective disclosure (credential sharing)
- [ ] Zero-knowledge proof mock (JSON format)
- [ ] Blockchain sync adapter (mock Polygon)
- [ ] KYC verification flow (manager approval)
- [ ] Reputation score tracking
- [ ] Consent blockchain recording (KVKK audit)
- [ ] Challenge-response mechanism (replay attack prevention)
- [ ] Credential expiry + revocation
- [ ] Tüm endpoint'ler RBAC + hata zarfı
- [ ] OpenAPI Türkçe
- [ ] pytest backend/tests yeşil

---

## 6. Teslim Dosyaları

### FILE: hotel/backend/app/models/blockchain_identity.py
```python
# Blockchain identity + credential + consent models
```

### FILE: hotel/backend/app/routers/blockchain.py
```python
# Blockchain identity endpoints
```

### FILE: hotel/backend/app/services/blockchain_service.py
```python
# DID management + credential orchestration
```

### FILE: hotel/backend/integrations/blockchain/base.py
```python
# Abstract blockchain adapter
```

### FILE: hotel/backend/integrations/blockchain/polygon_adapter.py
```python
# Polygon Mumbai mock implementation
```

### FILE: hotel/backend/integrations/blockchain/did_service.py
```python
# DID generation + key management
```

### FILE: hotel/backend/integrations/blockchain/credential_builder.py
```python
# W3C VC format builder
```

### FILE: hotel/backend/migrations/versions/0NN_add_blockchain_identity.py
```python
# Migration: blockchain_identities, verifiable_credentials, identity_verification_proofs, blockchain_sync_events, guest_consent_log
```

### FILE: hotel/backend/tests/test_modules/test_blockchain_identity.py
```python
# Unit + integration + performance tests
```
