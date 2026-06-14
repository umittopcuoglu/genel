"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowDownUp, Globe2, Loader2, Plus, RefreshCw, Share2 } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { api } from "@/lib/api";

/**
 * Channel Manager — kanal listesi + canlı senkron akışı.
 * Denklem: rezervasyon → stok düşer → tüm OTA'lara push → overbooking koruması.
 * Backend: /api/v1/channels + /api/v1/channels/sync-logs/recent
 */

type Channel = { id: string; name: string; channel_type: string; enabled: boolean };
type SyncLog = {
  id: string;
  channel_name: string;
  sync_type: string;
  status: string;
  rooms_updated: number;
  response_time_ms: number;
  created_at: string;
};

const KNOWN_CHANNELS = ["Booking.com", "Expedia", "Agoda", "Airbnb", "Hotelbeds", "Tatilsepeti", "ETS", "Jolly"];

export default function ChannelsPage() {
  const { t } = useTranslation();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [logs, setLogs] = useState<SyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ch, lg] = await Promise.all([
        api<Channel[]>("/api/v1/channels"),
        api<SyncLog[]>("/api/v1/channels/sync-logs/recent?limit=50"),
      ]);
      setChannels(ch);
      setLogs(lg);
    } catch (e: any) {
      setError(
        e?.status === 403
          ? t('channels.unauthorized')
          : t('channels.backendUnavailable')
      );
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  async function addChannel(name: string) {
    setAdding(true);
    try {
      await api("/api/v1/channels", {
        method: "POST",
        body: JSON.stringify({ name, channel_type: "ota", credentials: "pending-setup" }),
      });
      setNewName("");
      load();
    } catch (e: any) {
      setError(e?.message ?? "Kanal eklenemedi.");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('channels.title')}
        subtitle={t('channels.subtitle')}
        mock={false}
        action={
          <button onClick={load} className="btn-navy !px-3 !py-1.5 text-xs" aria-label="Refresh">
            <RefreshCw className="h-3.5 w-3.5" aria-hidden /> Refresh
          </button>
        }
      />

      {error && (
        <div className="rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning">{error}</div>
      )}

      {/* Denklem görseli */}
      <div className="card-lux p-5">
        <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-medium">
          <span className="rounded-full border border-line bg-bg px-3 py-1.5">Misafir / OTA satışı</span>
          <ArrowDownUp className="h-4 w-4 text-accent" aria-hidden />
          <span className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1.5 text-accent">
            Channel Manager
          </span>
          <ArrowDownUp className="h-4 w-4 text-accent" aria-hidden />
          <span className="rounded-full border border-line bg-bg px-3 py-1.5">PMS envanteri</span>
          <ArrowDownUp className="h-4 w-4 text-accent" aria-hidden />
          <span className="rounded-full border border-line bg-bg px-3 py-1.5">Tüm kanallara stok push</span>
        </div>
        <p className="mt-3 text-center text-[11px] text-text-2">
          Son oda hangi kanalda satılırsa satılsın, kalan envanter saniyeler içinde diğer tüm kanallara gönderilir.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Linked Channels */}
        <Card
          title={`${t('channels.linkedChannels')} (${channels.length})`}
          action={<Share2 className="h-4 w-4 text-accent" aria-hidden />}
        >
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-12" />
              ))}
            </div>
          ) : (
            <div className="space-y-2.5">
              {channels.map((ch) => (
                <div
                  key={ch.id}
                  className="flex items-center justify-between rounded-xl border border-line px-4 py-3 transition-colors hover:border-accent/30"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/12">
                      <Globe2 className="h-4 w-4 text-accent" aria-hidden />
                    </span>
                    <div>
                      <div className="text-sm font-medium">{ch.name}</div>
                      <div className="text-[11px] uppercase tracking-wide text-text-2">{ch.channel_type}</div>
                    </div>
                  </div>
                  <Badge tone={ch.enabled ? "success" : "neutral"}>{ch.enabled ? t('channels.activeChannel') : t('channels.inactive')}</Badge>
                </div>
              ))}
              {channels.length === 0 && (
                <p className="rounded-xl border border-dashed border-line p-5 text-center text-xs text-text-2">
                  Henüz kanal bağlı değil — aşağıdan ekleyin.
                </p>
              )}

              {/* Hızlı ekleme */}
              <div className="pt-2">
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {KNOWN_CHANNELS.filter((k) => !channels.some((c) => c.name === k)).map((k) => (
                    <button
                      key={k}
                      onClick={() => addChannel(k)}
                      disabled={adding}
                      className="rounded-full border border-line px-2.5 py-1 text-[11px] text-text-2 transition-colors hover:border-accent/50 hover:text-accent disabled:opacity-50"
                    >
                      + {k}
                    </button>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Özel kanal adı…"
                    className="flex-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm outline-none transition-all focus:border-accent/60"
                  />
                  <button
                    onClick={() => newName && addChannel(newName)}
                    disabled={adding || !newName}
                    className="btn-gold !px-4 !py-2 text-xs disabled:opacity-50"
                  >
                    {adding ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Plus className="h-3.5 w-3.5" aria-hidden />}
                    Ekle
                  </button>
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* Sync Flow */}
        <Card title={`${t('channels.syncFlow')} (${t('channels.recent')})`}>
          {loading ? (
            <div className="skeleton h-48" />
          ) : (
            <SimpleTable
              columns={[
                { key: "channel_name", header: "Channel" },
                { key: "sync_type", header: "Action", render: (r: SyncLog) => r.sync_type.replace("inventory_push:", "inventory push · ") },
                {
                  key: "status",
                  header: t('common.status'),
                  render: (r: SyncLog) => (
                    <Badge tone={r.status === "success" ? "success" : "danger"}>{r.status}</Badge>
                  ),
                },
                { key: "response_time_ms", header: "ms", align: "right" },
                {
                  key: "created_at",
                  header: "Time",
                  render: (r: SyncLog) => new Date(r.created_at).toLocaleString(),
                },
              ]}
              rows={logs}
              empty="Henüz senkron kaydı yok — ilk rezervasyonla birlikte akış başlar."
            />
          )}
        </Card>
      </div>
    </div>
  );
}
