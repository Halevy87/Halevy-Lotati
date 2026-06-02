// Israeli locale formatting (PRD §0): he-IL, DD/MM/YYYY, ₪ currency, comma thousands.

export function formatCurrencyILS(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("he-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("he-IL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

export const TOTAL_STEPS = 10;

export function progressLabel(currentStep: number): string {
  return `${currentStep}/${TOTAL_STEPS}`;
}
