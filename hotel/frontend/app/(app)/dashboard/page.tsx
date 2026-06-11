import { StatCard } from "@/components/kpi/StatCard";
import { AIPanel } from "@/components/ai/AIPanel";

/**
 * Manager Dashboard — docs/03 §3. Şimdilik mock veri;
 * backend Modül 10 (GET /api/v1/dashboard/manager) teslim edilince canlanır.
 */
const MOCK = {
  occupancy: "78%",
  adr: "₺2.450",
  revpar: "₺1.911",
  arrivals: "12 / 18",
  departures: "9 / 14",
  ooo: "3",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Doluluk" value={MOCK.occupancy} hint="son 7 gün ↑" tone="success" />
        <StatCard label="ADR" value={MOCK.adr} />
        <StatCard label="RevPAR" value={MOCK.revpar} />
        <StatCard label="Arrivals" value={MOCK.arrivals} hint="gelen / beklenen" />
        <StatCard label="Departures" value={MOCK.departures} hint="çıkan / beklenen" />
        <StatCard label="OOO Oda" value={MOCK.ooo} tone="danger" />
      </div>

      <div className="max-w-xl">
        <AIPanel
          agent="InsightAI"
          suggestion="Önümüzdeki hafta sonu doluluk %91 öngörülüyor. Cuma-Cumartesi için BAR fiyatını %8 artırmayı değerlendirin."
          rationale="90 günlük tahmin modeli · şehirde konser etkinliği · rakip fiyatları yükseldi"
        />
      </div>
    </div>
  );
}
