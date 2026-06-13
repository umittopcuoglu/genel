'use client';

import { useEffect, useState } from 'react';
import { ArrowRightLeft, TrendingUp } from 'lucide-react';

interface ExchangeRates {
  [key: string]: number;
}

interface CurrencyRateData {
  base: string;
  rates: ExchangeRates;
  timestamp: string;
  source: string;
}

export function CurrencyRates({ baseCurrency = 'TRY' }: { baseCurrency?: string }) {
  const [rates, setRates] = useState<CurrencyRateData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');

  useEffect(() => {
    const fetchRates = async () => {
      try {
        const response = await fetch(`/api/v1/currency/rates?base=${baseCurrency}`);
        if (!response.ok) throw new Error('Failed to fetch rates');
        const data = await response.json();
        setRates(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error fetching rates');
      } finally {
        setLoading(false);
      }
    };

    fetchRates();
    // Refresh every 30 minutes
    const interval = setInterval(fetchRates, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [baseCurrency]);

  if (loading) {
    return (
      <div className="rounded-lg border border-line bg-surface p-4">
        <div className="flex items-center gap-2 text-text-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          Kur yükleniyor...
        </div>
      </div>
    );
  }

  if (error || !rates) {
    return (
      <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-4">
        <p className="text-sm text-red-700 dark:text-red-300">Kurlar yüklenemedi: {error}</p>
      </div>
    );
  }

  const topCurrencies = ['USD', 'EUR', 'GBP', 'JPY'];
  const rate = rates.rates[selectedCurrency] || rates.rates['USD'];

  return (
    <div className="space-y-4">
      {/* Current Rate Card */}
      <div className="rounded-lg border border-accent/20 bg-gradient-to-br from-accent/5 to-accent/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text-2">Güncel Kur</p>
            <p className="text-2xl font-semibold text-accent">
              1 {selectedCurrency} = {rate.toFixed(2)} {baseCurrency}
            </p>
          </div>
          <TrendingUp className="h-8 w-8 text-accent" />
        </div>
      </div>

      {/* Currency Selector */}
      <div>
        <label className="block text-sm font-medium text-text-1 mb-2">Para Birimini Seç</label>
        <select
          value={selectedCurrency}
          onChange={(e) => setSelectedCurrency(e.target.value)}
          className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
        >
          {Object.entries(rates.rates).map(([code]) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </div>

      {/* Top Currencies Quick View */}
      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        {topCurrencies.map((currency) => {
          const rate = rates.rates[currency] || 0;
          return (
            <div
              key={currency}
              className="rounded-lg border border-line bg-surface p-3 transition-all hover:border-accent/50 hover:shadow-sm cursor-pointer"
              onClick={() => setSelectedCurrency(currency)}
            >
              <p className="text-xs font-medium text-text-2 uppercase tracking-wider">{currency}</p>
              <p className="mt-1 text-sm font-semibold text-accent">{rate.toFixed(2)}</p>
              <p className="text-xs text-text-3">per {baseCurrency}</p>
            </div>
          );
        })}
      </div>

      {/* Last Updated */}
      <p className="text-xs text-text-3">
        Son güncelleme: {new Date(rates.timestamp).toLocaleTimeString('tr-TR')}
      </p>
    </div>
  );
}

// Currency Converter Component
export function CurrencyConverter() {
  const [amount, setAmount] = useState('1');
  const [fromCurrency, setFromCurrency] = useState('TRY');
  const [toCurrency, setToCurrency] = useState('USD');
  const [result, setResult] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleConvert = async () => {
    if (!amount || isNaN(Number(amount))) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/currency/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: parseFloat(amount),
          from_currency: fromCurrency,
          to_currency: toCurrency,
        }),
      });
      if (!response.ok) throw new Error('Conversion failed');
      const data = await response.json();
      setResult(data.converted_amount);
    } catch (err) {
      console.error('Conversion error:', err);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <h3 className="mb-4 font-semibold text-text-1">Para Birimi Dönüştürücü</h3>

      <div className="space-y-3">
        {/* Amount Input */}
        <div>
          <label className="block text-sm text-text-2 mb-1">Miktar</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20"
            placeholder="Miktar"
          />
        </div>

        {/* From Currency */}
        <div>
          <label className="block text-sm text-text-2 mb-1">Kaynağı</label>
          <select
            value={fromCurrency}
            onChange={(e) => setFromCurrency(e.target.value)}
            className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent/60"
          >
            <option value="TRY">Turkish Lira (TRY)</option>
            <option value="USD">US Dollar (USD)</option>
            <option value="EUR">Euro (EUR)</option>
            <option value="GBP">British Pound (GBP)</option>
            <option value="JPY">Japanese Yen (JPY)</option>
          </select>
        </div>

        {/* Arrow */}
        <div className="flex justify-center">
          <ArrowRightLeft className="h-5 w-5 text-accent" />
        </div>

        {/* To Currency */}
        <div>
          <label className="block text-sm text-text-2 mb-1">Hedef</label>
          <select
            value={toCurrency}
            onChange={(e) => setToCurrency(e.target.value)}
            className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent/60"
          >
            <option value="TRY">Turkish Lira (TRY)</option>
            <option value="USD">US Dollar (USD)</option>
            <option value="EUR">Euro (EUR)</option>
            <option value="GBP">British Pound (GBP)</option>
            <option value="JPY">Japanese Yen (JPY)</option>
          </select>
        </div>

        {/* Convert Button */}
        <button
          onClick={handleConvert}
          disabled={loading}
          className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-white transition-all hover:bg-accent/90 disabled:opacity-50"
        >
          {loading ? 'Dönüştürülüyor...' : 'Dönüştür'}
        </button>

        {/* Result */}
        {result !== null && (
          <div className="rounded-lg bg-accent/10 p-3">
            <p className="text-sm text-text-2">Sonuç</p>
            <p className="text-2xl font-bold text-accent">
              {result.toFixed(2)} {toCurrency}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
