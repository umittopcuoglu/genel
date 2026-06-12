/** Lüks kart/panel sarmalayıcısı — yumuşak gölge, hover'da zarif yükselme. */
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
    <section className={`card-lux ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          {title && (
            <h2 className="font-display text-[15px] font-semibold tracking-wide text-text-1">{title}</h2>
          )}
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
