# HotelOps — Proje Durum Panosu

> Bu dosya canlı durum kaydıdır. Her review/teslimat sonrası güncellenir.
> Nightly QA workflow'u test sonuçlarını buraya işler.

**Son güncelleme:** 2026-06-11 (Faz 2 görev talimatları oluşturuldu) · **Faz:** 1 (MVP) — 4/5 modül tamamlandı · **Faz 2 kuyrukta**

## Modül Durumu

| # | Modül | Backend (DeepSeek) | Frontend (Claude) | Review | Faz |
|---|-------|--------------------|--------------------|--------|-----|
| 0 | Altyapı (Auth+RBAC+Audit) | ✅ KABUL (tur 2) | — | REVIEW-...-tur2 | 1 |
| 1 | Ön Büro | ✅ KABUL (tur 1) | ✅ ekranlar live (backend API entegre) | REVIEW-2026-06-11-TASK-002 | 1 |
| 2 | Rezervasyon | ✅ KABUL (tur 1) | 🟡 ekranlar yapılacak | REVIEW-2026-06-11-TASK-003 | 1 |
| 4 | Muhasebe & Cashiering | ✅ KABUL (tur 1) | 🟡 ekranlar yapılacak | REVIEW-2026-06-11-TASK-004 | 1 |
| 5 | Housekeeping | ⬜ | ⬜ | — | 1-2 |
| — | FrontDesk AI (temel) | ⬜ | ⬜ | — | 1 |
| 3 | Groups & Events | ⬜ | ⬜ | — | 3 |
| 6 | Bakım & Teknik | ⬜ | ⬜ | — | 3 |
| 7 | F&B (dış entegrasyon) | ⬜ | ⬜ | — | 3 |
| 8 | CRM & GuestAI | ⬜ | ⬜ | — | 2 |
| 9 | Güvenlik & KVKK | ⬜ | ⬜ | — | 3 |
| 10 | Raporlama & InsightAI | ⬜ | ⬜ | — | 2 |

Durum: ⬜ bekliyor · 🟡 devam · 🟠 review'da · ✅ kabul · ❌ düzeltmede

## Açık Görevler (orchestrator/tasks/)
| Görev | Modül | Durum | Faz | Tur |
|---|---|---|---|---|
| TASK-001 | Altyapı: Auth + RBAC + Audit | ✅ KABUL | 1 | 2 |
| TASK-002 | Modül 1: Ön Büro | ✅ KABUL | 1 | 1 |
| TASK-003 | Modül 2: Rezervasyon & Müsaitlik | ✅ KABUL | 1 | 1 |
| TASK-004 | Modül 4: Muhasebe & Cashiering | ✅ KABUL | 1 | 1 |
| TASK-005 | Modül 5: Housekeeping | 🟡 DeepSeek'e gönderilmesi bekleniyor | 1 | 1 |
| TASK-006 | Altyapı: WebSocket + E2E + Docker + CI/CD | ⬜ sıraya girecek | 1 | 1 |
| TASK-007 | Altyapı: Ortak AI Çekirdeği (BaseAgent + LLM + PII maskeleme) | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-008 | Modül 2 AI Genişleme: Channel Manager & OTA | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-009 | Modül 2 AI Genişleme: RevenueIQ Advisor | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-010 | Modül 4 Genişleme: Tam Muhasebe & GİB e-Fatura | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-011 | Modül 8: CRM & Misafir 360 & Loyalty | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-012 | Modül 8 AI: GuestAI Chatbot (WhatsApp) | ⬜ Faz 2 kuyruğu | 2 | — |
| TASK-013 | Modül 10: Raporlama & InsightAI | ⬜ Faz 2 kuyruğu | 2 | — |

## Açık Geri Bildirimler (orchestrator/feedback/)
_Yok. (FB-001 kapatıldı — düzeltmeler ağ engeli nedeniyle denetçi/Claude tarafından uygulandı.)_

## Son Review Raporları (docs/reviews/)
- `REVIEW-2026-06-11-TASK-001-tur2.md` — **KABUL** ✅ (6/6 backend testi + 6 kontrat testi yeşil, canlı API doğrulandı)
- `REVIEW-2026-06-11-TASK-001.md` — DÜZELTME GEREKLİ ❌ (tur 1, FB-001)

## Bilinen Engeller
- ⚠️ `api.deepseek.com` cloud ortam allowlist'inde kapalı → görevler manuel modla
  (`run_task.py --manual`) veya kullanıcının makinesinden API moduyla yürür.
  Tam otomasyon için: Claude Code web → ortam ayarları → network allowlist'e
  `api.deepseek.com` eklenmeli.
