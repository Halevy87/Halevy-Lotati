import { AppShell } from "@/components/app-shell";
import { CaseDetail } from "@/components/case-detail";

export default function CasePage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <CaseDetail caseId={params.id} />
    </AppShell>
  );
}
