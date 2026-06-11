// ═══════════════════════════════════════════════════════════
// LANDING ROUTING — code.gs içine eklenecek / mevcut doGet ile DEĞİŞTİRİLECEK
//
// Kurulum:
//  1) Apps Script projesinde "landing" adında YENİ bir HTML dosyası oluştur,
//     lovable/henkel-ekol/landing.html içeriğini içine yapıştır.
//  2) Mevcut code.gs'teki doGet() fonksiyonunu aşağıdaki doGet(e) ile DEĞİŞTİR.
//  3) getPanelUrl() fonksiyonunu code.gs'e EKLE.
//  4) Yeni bir dağıtım (deployment) al → açılışta "landing" gelir,
//     CTA / "Operasyon Paneli" butonu ?page=panel ile mevcut dashboard'a (index) gider.
//
// Not: authLogin ve diğer tüm fonksiyonlar AYNEN kalır; landing aynı authLogin'i kullanır.
// ═══════════════════════════════════════════════════════════

function doGet(e) {
  var page = (e && e.parameter && e.parameter.page) ? String(e.parameter.page) : '';
  var file = (page === 'panel') ? 'index' : 'landing';
  var title = (file === 'index')
    ? 'Henkel × Ekol — Operations Dashboard'
    : 'Henkel × Ekol — Lavanta Terminal';
  return HtmlService.createHtmlOutputFromFile(file)
    .setTitle(title)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// Landing'deki "Operasyon Paneli" CTA'sı için web app URL'ini döner (?page=panel).
function getPanelUrl() {
  return ScriptApp.getService().getUrl() + '?page=panel';
}
