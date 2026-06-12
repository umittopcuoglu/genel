/** Modül ekranı başlığı + opsiyonel "mock veri" rozeti ve sağ aksiyon alanı. */
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
    <div className="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-text-2">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        {mock && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            Mock veri — backend entegrasyonu bekleniyor
          </span>
        )}
        {action}
      </div>
    </div>
  );
}
