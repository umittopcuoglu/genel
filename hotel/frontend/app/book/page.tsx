"use client";

import { useState } from "react";
import {
  BedDouble,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Hotel,
  Loader2,
  Sparkles,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";

/**
 * Booking Engine — misafire açık, komisyonsuz doğrudan rezervasyon sayfası.
 * Backend: /api/v1/public/availability + /api/v1/public/bookings (auth gerekmez).
 * 3 adım: Tarih → Oda seçimi → Misafir bilgisi → Onay.
 */

type AvailableRoom = {
  room_type_id: string;
  code: string;
  name: string;
  description: string | null;
  max_guests: number;
  nightly_rate: string;
  total_price: string;
  nights: number;
  rooms_left: number;
};

type Confirmation = {
  reservation_number: string;
  room_type_name: string;
  check_in: string;
  check_out: string;
  nights: number;
  total_amount: string;
  guest_name: string;
  channels_notified: number;
};

const fmt = (v: string | number) =>
  Number(v).toLocaleString("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 0 });

export default function BookPage() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [adults, setAdults] = useState(2);
  const [rooms, setRooms] = useState<AvailableRoom[]>([]);
  const [selected, setSelected] = useState<AvailableRoom | null>(null);
  const [guest, setGuest] = useState({ first_name: "", last_name: "", email: "", phone: "" });
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    if (!checkIn || !checkOut) {
      setError("Giriş ve çıkış tarihlerini seçin.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api<AvailableRoom[]>(
        `/api/v1/public/availability?check_in=${checkIn}&check_out=${checkOut}&adults=${adults}`
      );
      setRooms(data);
      setStep(2);
      if (data.length === 0) setError("Seçilen tarihlerde müsait oda bulunamadı.");
    } catch (e: any) {
      setError(e?.message ?? "Arama başarısız — tarihleri kontrol edin.");
    } finally {
      setLoading(false);
    }
  }

  async function book() {
    if (!selected) return;
    if (!guest.first_name || !guest.last_name || !guest.email) {
      setError("Ad, soyad ve e-posta zorunludur.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api<Confirmation>("/api/v1/public/bookings", {
        method: "POST",
        body: JSON.stringify({
          room_type_id: selected.room_type_id,
          check_in: checkIn,
          check_out: checkOut,
          adults,
          children: 0,
          ...guest,
        }),
      });
      setConfirmation(res);
      setStep(4);
    } catch (e: any) {
      setError(e?.message ?? "Rezervasyon oluşturulamadı.");
    } finally {
      setLoading(false);
    }
  }

  const inputCls =
    "w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm outline-none transition-all duration-200 focus:border-accent/60 focus:shadow-[0_0_0_3px_rgb(var(--color-accent)/0.15)]";

  return (
    <main className="min-h-screen bg-bg">
      {/* Üst marka şeridi */}
      <header
        className="px-6 py-5"
        style={{ background: "linear-gradient(160deg, #101c32 0%, #17335c 100%)" }}
      >
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#c8a35a] to-[#a37e35]">
              <Hotel className="h-5 w-5 text-white" aria-hidden />
            </span>
            <span>
              <span className="block font-display text-lg font-semibold text-white">HotelOps Grand</span>
              <span className="block text-[10px] uppercase tracking-[0.22em] text-[#c0984a]">
                Online Rezervasyon
              </span>
            </span>
          </div>
          <span className="hidden items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs text-white/80 sm:flex">
            <Sparkles className="h-3 w-3 text-[#d6b26a]" aria-hidden />
            En iyi fiyat garantisi — komisyonsuz
          </span>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-8">
        {/* Adım göstergesi */}
        <ol className="mb-8 flex items-center gap-2 text-xs" aria-label="Rezervasyon adımları">
          {["Tarihler", "Oda Seçimi", "Misafir Bilgisi", "Onay"].map((label, i) => {
            const n = (i + 1) as 1 | 2 | 3 | 4;
            const active = step === n;
            const done = step > n;
            return (
              <li key={label} className="flex items-center gap-2">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold transition-all duration-300 ${
                    done
                      ? "bg-success text-white"
                      : active
                        ? "bg-gradient-to-br from-[#c8a35a] to-[#a37e35] text-white shadow-lg shadow-accent/30"
                        : "border border-line bg-surface text-text-2"
                  }`}
                >
                  {done ? <CheckCircle2 className="h-4 w-4" aria-hidden /> : n}
                </span>
                <span className={active ? "font-semibold text-text-1" : "text-text-2"}>{label}</span>
                {n < 4 && <ChevronRight className="h-3.5 w-3.5 text-text-2/50" aria-hidden />}
              </li>
            );
          })}
        </ol>

        {error && (
          <div className="page-enter mb-5 rounded-xl border border-danger/25 bg-danger/[0.07] px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* 1 — Tarih seçimi */}
        {step === 1 && (
          <section className="card-lux page-enter p-6">
            <h1 className="font-display text-2xl font-semibold">Konaklama tarihlerinizi seçin</h1>
            <div className="mt-3 h-[2px] w-14 rounded-full bg-gradient-to-r from-accent to-transparent" />
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <label className="block text-xs font-medium text-text-2">
                <span className="mb-1.5 flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" aria-hidden /> Giriş
                </span>
                <input type="date" value={checkIn} onChange={(e) => setCheckIn(e.target.value)} className={inputCls} />
              </label>
              <label className="block text-xs font-medium text-text-2">
                <span className="mb-1.5 flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" aria-hidden /> Çıkış
                </span>
                <input type="date" value={checkOut} onChange={(e) => setCheckOut(e.target.value)} className={inputCls} />
              </label>
              <label className="block text-xs font-medium text-text-2">
                <span className="mb-1.5 flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5" aria-hidden /> Yetişkin
                </span>
                <select value={adults} onChange={(e) => setAdults(Number(e.target.value))} className={inputCls}>
                  {[1, 2, 3, 4, 5, 6].map((n) => (
                    <option key={n} value={n}>
                      {n} yetişkin
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button onClick={search} disabled={loading} className="btn-gold mt-6 w-full disabled:opacity-60 sm:w-auto sm:px-10">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : "Müsaitlik Ara"}
            </button>
          </section>
        )}

        {/* 2 — Oda seçimi */}
        {step === 2 && (
          <section className="space-y-4">
            <button onClick={() => setStep(1)} className="text-xs text-text-2 underline-offset-2 hover:underline">
              ← Tarihleri değiştir
            </button>
            <div className="stagger space-y-4">
              {rooms.map((room) => (
                <article key={room.room_type_id} className="card-lux flex flex-wrap items-center gap-4 p-5">
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent/12">
                    <BedDouble className="h-7 w-7 text-accent" aria-hidden />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h2 className="font-display text-lg font-semibold">{room.name}</h2>
                    <p className="mt-0.5 text-xs text-text-2">
                      {room.description ?? "Konforlu konaklama"} · en fazla {room.max_guests} kişi
                    </p>
                    <p className={`mt-1 text-xs font-medium ${room.rooms_left <= 2 ? "text-danger" : "text-success"}`}>
                      {room.rooms_left <= 2 ? `Son ${room.rooms_left} oda!` : `${room.rooms_left} oda müsait`}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="tabular font-display text-xl font-semibold">{fmt(room.total_price)}</div>
                    <div className="text-[11px] text-text-2">
                      {room.nights} gece · {fmt(room.nightly_rate)}/gece
                    </div>
                    <button
                      onClick={() => {
                        setSelected(room);
                        setStep(3);
                        setError(null);
                      }}
                      className="btn-gold mt-2 !px-5 !py-1.5 text-xs"
                    >
                      Seç
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* 3 — Misafir bilgisi */}
        {step === 3 && selected && (
          <section className="card-lux page-enter p-6">
            <button onClick={() => setStep(2)} className="text-xs text-text-2 underline-offset-2 hover:underline">
              ← Oda seçimine dön
            </button>
            <h1 className="mt-3 font-display text-2xl font-semibold">Misafir bilgileri</h1>
            <p className="mt-1 text-sm text-text-2">
              {selected.name} · {checkIn} → {checkOut} · <strong className="text-text-1">{fmt(selected.total_price)}</strong>
            </p>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <input placeholder="Ad *" value={guest.first_name} onChange={(e) => setGuest({ ...guest, first_name: e.target.value })} className={inputCls} />
              <input placeholder="Soyad *" value={guest.last_name} onChange={(e) => setGuest({ ...guest, last_name: e.target.value })} className={inputCls} />
              <input type="email" placeholder="E-posta *" value={guest.email} onChange={(e) => setGuest({ ...guest, email: e.target.value })} className={inputCls} />
              <input placeholder="Telefon" value={guest.phone} onChange={(e) => setGuest({ ...guest, phone: e.target.value })} className={inputCls} />
            </div>
            <button onClick={book} disabled={loading} className="btn-gold mt-6 w-full disabled:opacity-60">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : `Rezervasyonu Tamamla — ${fmt(selected.total_price)}`}
            </button>
            <p className="mt-3 text-center text-[11px] text-text-2">
              Ödeme girişe kadar alınmaz · ücretsiz iptal · doğrudan otel fiyatı
            </p>
          </section>
        )}

        {/* 4 — Onay */}
        {step === 4 && confirmation && (
          <section className="card-lux page-enter overflow-hidden p-8 text-center">
            <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/12">
              <CheckCircle2 className="h-9 w-9 text-success" aria-hidden />
            </span>
            <h1 className="mt-4 font-display text-2xl font-semibold">Rezervasyonunuz onaylandı</h1>
            <p className="mt-1 text-sm text-text-2">Onay e-postanız kısa süre içinde gönderilecek.</p>
            <div className="mx-auto mt-6 max-w-sm space-y-2 rounded-2xl border border-line bg-bg/60 p-5 text-left text-sm">
              <Row label="Onay Kodu" value={confirmation.reservation_number} mono />
              <Row label="Misafir" value={confirmation.guest_name} />
              <Row label="Oda" value={confirmation.room_type_name} />
              <Row label="Tarih" value={`${confirmation.check_in} → ${confirmation.check_out} (${confirmation.nights} gece)`} />
              <Row label="Toplam" value={fmt(confirmation.total_amount)} strong />
            </div>
            <p className="mt-4 text-[11px] text-text-2">
              Envanter {confirmation.channels_notified} satış kanalına anında senkronlandı — çifte satış koruması aktif.
            </p>
            <button onClick={() => { setStep(1); setConfirmation(null); setSelected(null); }} className="btn-navy mt-6">
              Yeni rezervasyon
            </button>
          </section>
        )}
      </div>
    </main>
  );
}

function Row({ label, value, mono = false, strong = false }: { label: string; value: string; mono?: boolean; strong?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className="text-xs text-text-2">{label}</span>
      <span className={`${mono ? "font-mono" : ""} ${strong ? "font-display text-base font-semibold" : "text-sm"}`}>{value}</span>
    </div>
  );
}
