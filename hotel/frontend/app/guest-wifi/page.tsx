"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function GuestWiFiPage() {
  const router = useRouter();
  const [step, setStep] = useState<"form" | "success">("form");
  const [formData, setFormData] = useState({
    email: "",
    guest_name: "",
    phone: "",
    terms_accepted: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState<any>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, type, value, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (!formData.terms_accepted) {
      setError("Koşul ve Gizlilik Politikası'nı kabul etmelisiniz.");
      setLoading(false);
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/guest-wifi/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          guest_name: formData.guest_name,
          phone: formData.phone || undefined,
          terms_accepted: formData.terms_accepted,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || "Bir hata oluştu");
      }

      const data = await response.json();
      setSuccessData(data);
      setStep("success");
    } catch (err: any) {
      setError(err.message || "Kayıt başarısız oldu. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  };

  if (step === "success" && successData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Wi-Fi Kaydı Başarılı!</h1>
            <p className="text-gray-600">Aşağıdaki bilgilerle bağlanabilirsiniz</p>
          </div>

          <div className="space-y-4 mb-6">
            <div className="bg-gray-50 rounded p-4">
              <p className="text-sm text-gray-600 mb-1">Ağ Adı (SSID)</p>
              <p className="text-lg font-mono font-bold text-gray-900">{successData.ssid}</p>
            </div>

            <div className="bg-gray-50 rounded p-4">
              <p className="text-sm text-gray-600 mb-1">Şifre</p>
              <div className="flex items-center justify-between">
                <p className="text-lg font-mono font-bold text-gray-900">{successData.password}</p>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(successData.password);
                    alert("Şifre kopyalandı!");
                  }}
                  className="ml-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                >
                  Kopyala
                </button>
              </div>
            </div>

            <div className="bg-blue-50 rounded p-4 text-sm text-blue-800">
              ⏱️ <strong>Geçerli Süresi:</strong> {successData.valid_hours} saat
              <br />
              <strong>Bitiş Zamanı:</strong> {new Date(successData.valid_until).toLocaleString("tr-TR")}
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => router.push("/")}
              className="w-full bg-blue-500 text-white py-2 rounded font-medium hover:bg-blue-600 transition"
            >
              Ana Sayfaya Dön
            </button>
            <button
              onClick={() => setStep("form")}
              className="w-full border border-gray-300 text-gray-700 py-2 rounded font-medium hover:bg-gray-50 transition"
            >
              Başka E-posta İçin Kayıt Ol
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🌐 Otel Wi-Fi</h1>
          <p className="text-gray-600">Hızlı ve Güvenli İnternet Erişimi</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              E-Posta Adresi <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ornek@email.com"
            />
          </div>

          <div>
            <label htmlFor="guest_name" className="block text-sm font-medium text-gray-700 mb-1">
              Ad Soyad <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="guest_name"
              name="guest_name"
              value={formData.guest_name}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
              Telefon (İsteğe Bağlı)
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="+90 500 123 45 67"
            />
          </div>

          <div className="flex items-start gap-3 pt-2">
            <input
              type="checkbox"
              id="terms_accepted"
              name="terms_accepted"
              checked={formData.terms_accepted}
              onChange={handleInputChange}
              className="mt-1 w-4 h-4 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label htmlFor="terms_accepted" className="text-sm text-gray-700">
              <a href="#" className="text-blue-500 hover:underline">
                Koşul ve Gizlilik Politikası
              </a>
              'nı okudum ve kabul ediyorum. <span className="text-red-500">*</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 rounded-lg font-medium hover:bg-blue-600 transition disabled:bg-gray-400 mt-6"
          >
            {loading ? "Kaydediliyor..." : "Wi-Fi'ye Erişim Sağla"}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-600">
          <p>❓ Kimlik bilgilerini unuttun mu?</p>
          <p className="mt-2">
            <button className="text-blue-500 hover:underline">
              Kimlik bilgilerini tekrar gönder
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
