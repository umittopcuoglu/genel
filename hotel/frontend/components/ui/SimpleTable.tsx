import React from "react";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  render?: (row: T) => React.ReactNode;
}

/** Genel okuma tablosu — modül listelerinde tekrarı önler. */
export function SimpleTable<T extends Record<string, any>>({
  columns,
  rows,
  empty = "Kayıt yok.",
  rowKey = "id",
}: {
  columns: Column<T>[];
  rows: T[];
  empty?: string;
  rowKey?: string;
}) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-text-2">
        {empty}
      </div>
    );
  }
  const alignCls = (a?: string) => (a === "right" ? "text-right" : a === "center" ? "text-center" : "text-left");
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line bg-bg text-xs uppercase tracking-wide text-text-2">
            {columns.map((c) => (
              <th key={c.key} className={`px-4 py-3 font-medium ${alignCls(c.align)}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]} className="border-b border-line last:border-0 hover:bg-bg/60">
              {columns.map((c) => (
                <td key={c.key} className={`px-4 py-3 ${alignCls(c.align)}`}>
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
