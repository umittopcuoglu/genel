/**
 * Route geçiş animasyonu — her sayfa değişiminde içerik
 * zarif bir fade-up ile girer (template her navigasyonda yeniden mount olur).
 */
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="page-enter">{children}</div>;
}
