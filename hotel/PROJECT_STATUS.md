# HotelOps — Proje Durum Panosu

> Bu dosya canlı durum kaydıdır. Her review/teslimat sonrası güncellenir.
> Nightly QA workflow'u test sonuçlarını buraya işler.

**Son güncelleme:** 2026-06-11 (TASK-001 tur 1 denetimi) · **Faz:** 1 (MVP) · **Sprint:** 1

## Modül Durumu

| # | Modül | Backend (DeepSeek) | Frontend (Claude) | Review | Faz |
|---|-------|--------------------|--------------------|--------|-----|
| 0 | Altyapı (Auth+RBAC+Audit) | ❌ Tur 1 teslim edildi → DÜZELTME (FB-001) | — | REVIEW-2026-06-11 | 1 |
| 1 | Ön Büro | ⬜ bekliyor | ⬜ bekliyor | — | 1 |
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
| TASK-001 | Altyapı: Auth + RBAC + Audit | düzeltme bekleniyor | 2 |

## Açık Geri Bildirimler (orchestrator/feedback/)
| FB | Görev | Şiddet | Özet |
|---|---|---|---|
| FB-001 | TASK-001 | critical | 4 critical (import hataları, yanlış JWT paketi), 3 high, 3 minor bulgu — testler import'ta çöküyor |

## Son Review Raporları (docs/reviews/)
- `REVIEW-2026-06-11-TASK-001.md` — **DÜZELTME GEREKLİ** ❌ (tur 1)

## Bilinen Engeller
- ⚠️ `api.deepseek.com` cloud ortam allowlist'inde kapalı → görevler manuel modla
  (`run_task.py --manual`) veya kullanıcının makinesinden API moduyla yürür.
  Tam otomasyon için: Claude Code web → ortam ayarları → network allowlist'e
  `api.deepseek.com` eklenmeli.
