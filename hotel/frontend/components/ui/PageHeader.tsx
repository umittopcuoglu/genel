/** Modül ekranı başlığı — serif display başlık + altın alt çizgi + sağ aksiyon alanı. */
export function PageHeader({
  title,
  subtitle,
  mock = true,
  action,
}: {
  title: string;
  subtitle?: string;
  mock?: boolean;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-2">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-[26px] font-semibold tracking-wide text-text-1">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-text-2">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          {mock && (
            <span className="rounded-full border border-warning/30 bg-warning/10 px-3 py-1 text-xs font-medium text-warning">
              Demo veri
            </span>
          )}
          {action}
        </div>
      </div>
      <div className="mt-3 h-[2px] w-16 rounded-full bg-gradient-to-r from-accent to-transparent" />
    </div>
  );
}
