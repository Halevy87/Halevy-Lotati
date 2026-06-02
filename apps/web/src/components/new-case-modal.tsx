"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";

import { api } from "@/lib/api";
import { newCaseSchema, type NewCaseForm } from "@/lib/schemas";

export function NewCaseModal({ onClose }: { onClose: () => void }) {
  const t = useTranslations("newCase");
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<NewCaseForm>({
    resolver: zodResolver(newCaseSchema),
    defaultValues: { deal_type: "purchase" },
  });

  const mutation = useMutation({
    mutationFn: (values: NewCaseForm) =>
      api.createCase({
        deal_type: values.deal_type,
        block: values.block,
        parcel: values.parcel,
        sub_parcel: values.sub_parcel || null,
        property_address: values.property_address,
        property_city: values.property_city,
        counterparty_lawyer_name: values.counterparty_lawyer_name || null,
        primary_client: {
          role: "buyer",
          full_name: values.client_name,
          israeli_id: values.client_id,
          phone: values.client_phone || null,
          email: values.client_email || null,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      onClose();
    },
  });

  const field = (name: keyof NewCaseForm, label: string, type = "text") => (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-ink/70">{label}</span>
      <input
        type={type}
        {...register(name)}
        className="rounded-lg border border-ink/15 px-3 py-2 outline-none focus:border-burgundy"
      />
      {errors[name] && <span className="text-xs text-red-600">{t("required")}</span>}
    </label>
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-2xl font-bold">{t("title")}</h2>
          <button onClick={onClose} aria-label={t("cancel")} className="text-ink/50 hover:text-ink">
            ✕
          </button>
        </div>

        <form
          onSubmit={handleSubmit((values) => mutation.mutate(values))}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2"
        >
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-ink/70">{t("dealType")}</span>
            <select
              {...register("deal_type")}
              className="rounded-lg border border-ink/15 px-3 py-2 outline-none focus:border-burgundy"
            >
              <option value="purchase">{t("dealTypes.purchase")}</option>
              <option value="sale">{t("dealTypes.sale")}</option>
              <option value="exchange">{t("dealTypes.exchange")}</option>
            </select>
          </label>
          <div className="hidden sm:block" />
          {field("block", t("block"))}
          {field("parcel", t("parcel"))}
          {field("sub_parcel", t("subParcel"))}
          {field("property_address", t("address"))}
          {field("property_city", t("city"))}
          {field("client_name", t("clientName"))}
          {field("client_id", t("clientId"))}
          {field("client_phone", t("clientPhone"))}
          {field("client_email", t("clientEmail"), "email")}
          {field("counterparty_lawyer_name", t("counterpartyLawyer"))}

          <div className="col-span-full mt-2 flex justify-start gap-3">
            <button
              type="submit"
              disabled={isSubmitting || mutation.isPending}
              className="rounded-lg bg-burgundy px-5 py-2 text-sm font-medium text-white hover:bg-burgundy/90 disabled:opacity-50"
            >
              {t("submit")}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-ink/15 px-5 py-2 text-sm"
            >
              {t("cancel")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
