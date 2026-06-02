export type CaseStatus =
  | "intake_pending"
  | "intake_complete"
  | "in_progress"
  | "needs_attention"
  | "signing_scheduled"
  | "signed"
  | "archived";

export type DealType = "purchase" | "sale" | "exchange";

export interface CaseListItem {
  id: string;
  case_number: string;
  status: CaseStatus;
  current_step: number;
  property_address: string;
  property_city: string;
  deal_type: DealType;
  red_flags_count: number;
  completion_percentage: number;
  primary_lawyer_id: string | null;
  opened_at: string;
}

export interface CaseList {
  items: CaseListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface Party {
  id: string;
  case_id: string;
  role: "buyer" | "seller" | "guarantor" | "spouse";
  full_name: string;
  israeli_id: string;
  phone: string | null;
  email: string | null;
  identity_check_status: "pending" | "clean" | "warning" | "red_flag";
  created_at: string;
}

export interface Activity {
  id: string;
  case_id: string;
  user_id: string | null;
  type: string;
  description: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface CaseDetail extends CaseListItem {
  block: string;
  parcel: string;
  sub_parcel: string | null;
  deal_value_ils: number | null;
  counterparty_lawyer_name: string | null;
  counterparty_lawyer_phone: string | null;
  signing_scheduled_at: string | null;
  handover_scheduled_at: string | null;
  parties: Party[];
  activities: Activity[];
}

export interface CreateCaseInput {
  deal_type: DealType;
  block: string;
  parcel: string;
  sub_parcel?: string | null;
  property_address: string;
  property_city: string;
  counterparty_lawyer_name?: string | null;
  primary_client?: {
    role: "buyer";
    full_name: string;
    israeli_id: string;
    phone?: string | null;
    email?: string | null;
  };
}
