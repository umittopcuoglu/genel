# HotelOps — Proje Durum Panosu

> Bu dosya canlı durum kaydıdır. Her review/teslimat sonrası güncellenir.
> Nightly QA workflow'u test sonuçlarını buraya işler.

**Son güncelleme:** 2026-06-11 (TASK-002 KABUL ✅) · **Faz:** 1 (MVP) · **Sprint:** 1

## Modül Durumu

| # | Modül | Backend (DeepSeek) | Frontend (Claude) | Review | Faz |
|---|-------|--------------------|--------------------|--------|-----|
| 0 | Altyapı (Auth+RBAC+Audit) | ✅ KABUL (tur 2) | — | REVIEW-...-tur2 | 1 |
| 1 | Ön Büro | ✅ KABUL (tur 1) | 🟡 ekranlar live (backend API için hazır) | REVIEW-2026-06-11-TASK-002 | 1 |
| 2 | Rezervasyon | ⬜ | ⬜ | — | 1-2 |
| 4 | Muhasebe & Cashiering | ⬜ | ⬜ | — | 1-2 |
| 5 | Housekeeping | ⬜ | ⬜ | — | 1-2 |
| — | FrontDesk AI (temel) | ⬜ | ⬜ | — | 1 |
| 3 | Groups & Events | ⬜ | ⬜ | — | 3 |
| 6 | Bakım & Teknik | ⬜ | ⬜ | — | 3 |
| 7 | F&B (dış entegrasyon) | ⬜ | ⬜ | — | 3 |
| 8 | CRM & GuestAI | ⬜ | ⬜ | — | 2-3 |
| 9 | Güvenlik & KVKK | ⬜ | ⬜ | — | 3 |
| 10 | Raporlama & InsightAI | ⬜ | ⬜ | — | 2-3 |

Durum: ⬜ bekliyor · 🟡 devam · 🟠 review'da · ✅ kabul · ❌ düzeltmede

## Açık Görevler (orchestrator/tasks/)
| Görev | Modül | Durum | Tur |
|---|---|---|---|
| TASK-001 | Altyapı: Auth + RBAC + Audit | ✅ done (KABUL) | 2 |
| TASK-002 | Modül 1: Ön Büro | ✅ done (KABUL) | 1 |
| TASK-003 | Modül 2: Rezervasyon & Müsaitlik | 🟡 kullanıcı DeepSeek'e iletiyor | 1 |
| TASK-004 | Modül 4: Muhasebe & Cashiering | ⬜ kuyrukta (TASK-003 KABUL sonrası) | — |
| TASK-005 | Modül 5: Housekeeping | ⬜ kuyrukta (TASK-004 KABUL sonrası) | — |
| TASK-006 | Altyapı: WebSocket + E2E + Docker + CI/CD | 🟡 TASK-003 ile paralel | 1 |

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
