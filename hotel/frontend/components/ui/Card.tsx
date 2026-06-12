/** Genel kart/panel sarmalayıcısı — modül ekranlarında ortak kullanım (docs/03 §1). */
export function Card({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-xl border border-line bg-surface ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          {title && <h2 className="text-sm font-semibold">{title}</h2>}
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}
