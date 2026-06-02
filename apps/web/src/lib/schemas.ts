import { z } from "zod";

// Mirrors the backend Pydantic CaseCreate. israeli_id is synthetic/fake only (Foundation).
export const newCaseSchema = z.object({
  deal_type: z.enum(["purchase", "sale", "exchange"]),
  block: z.string().min(1),
  parcel: z.string().min(1),
  sub_parcel: z.string().optional(),
  property_address: z.string().min(1),
  property_city: z.string().min(1),
  client_name: z.string().min(1),
  client_id: z.string().min(1),
  client_phone: z.string().optional(),
  client_email: z.string().email().optional().or(z.literal("")),
  counterparty_lawyer_name: z.string().optional(),
});

export type NewCaseForm = z.infer<typeof newCaseSchema>;
