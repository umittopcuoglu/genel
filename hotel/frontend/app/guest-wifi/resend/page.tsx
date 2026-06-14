"use client";

import { useState } from "react";

export default function GuestWiFiResendPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [credentialData, setCredentialData] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/guest-wifi/resend-credentials/${email}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || "Bir hata oluştu");
      }

      const data = await response.json();
      setCredentialData(data);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Kimlik bilgileri gönderilemedi. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🔑 Kimlik Bilgilerini Tekrar Gönder</h1>
          <p className="text-gray-600">Kaydınız sırasında kullandığınız e-posta adresi girin</p>
        </div>

        {!success ? (
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
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ornek@email.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-500 text-white py-2 rounded-lg font-medium hover:bg-blue-600 transition disabled:bg-gray-400 mt-6"
            >
              {loading ? "Gönderiliyor..." : "Kimlik Bilgilerini Gönder"}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Bulundu!</h2>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded p-4">
                <p className="text-sm text-gray-600 mb-1">Ağ Adı (SSID)</p>
                <p className="text-lg font-mono font-bold text-gray-900">{credentialData.ssid}</p>
              </div>

              <div className="bg-gray-50 rounded p-4">
                <p className="text-sm text-gray-600 mb-1">Şifre</p>
                <div className="flex items-center justify-between">
                  <p className="text-lg font-mono font-bold text-gray-900">{credentialData.wifi_password}</p>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(credentialData.wifi_password);
                      alert("Şifre kopyalandı!");
                    }}
                    className="ml-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                  >
                    Kopyala
                  </button>
                </div>
              </div>

              <div className="bg-blue-50 rounded p-4 text-sm text-blue-800">
                ⏱️ <strong>Kayıt Tarihi:</strong> {new Date(credentialData.valid_from).toLocaleString("tr-TR")}
                <br />
                <strong>Bitiş Zamanı:</strong> {new Date(credentialData.valid_until).toLocaleString("tr-TR")}
              </div>
            </div>

            <button
              onClick={() => {
                setSuccess(false);
                setEmail("");
              }}
              className="w-full border border-gray-300 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-50 transition"
            >
              Başka E-posta İçin Ara
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
