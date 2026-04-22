"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { api, ApiError } from "@/lib/api";
import { leadCreateSchema, type LeadCreateFormValues } from "@/lib/validation";
import { normalizeVNPhone } from "@/lib/phone";
import { Button } from "@/components/ui/Button";
import { FieldError } from "@/components/ui/FieldError";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

interface Props {
  trackingId: string | null;
  /** Consent version shown, must match backend contract */
  consentVersion: string;
}

const CONSENT_TEXT =
  "Tôi đồng ý cho nền tảng sử dụng họ tên, số điện thoại và khu vực để kết nối với nhà tuyển dụng (Nghị định 13/2023).";

export function LandingForm({ trackingId, consentVersion }: Props) {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [resumeSessionId, setResumeSessionId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
  } = useForm<LeadCreateFormValues>({
    resolver: zodResolver(leadCreateSchema),
    defaultValues: { full_name: "", phone: "", area_raw: "", consent_accepted: false },
    mode: "onSubmit",
    reValidateMode: "onChange",
  });

  const onPhoneBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const norm = normalizeVNPhone(e.target.value);
    if (norm) setValue("phone", norm, { shouldValidate: true });
  };

  async function onSubmit(values: LeadCreateFormValues) {
    setServerError(null);
    setResumeSessionId(null);
    try {
      const res = await api.createLead({
        tracking_id: trackingId,
        full_name: values.full_name.trim(),
        phone: values.phone.trim(),
        area_raw: values.area_raw?.trim() || null,
        consent: { version: consentVersion, accepted: true },
      });
      router.push(
        `/screening/${encodeURIComponent(res.lead_id)}` +
          `?session_id=${encodeURIComponent(res.session_id)}` +
          `&first_msg=${encodeURIComponent(res.first_ai_message)}`
      );
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === "DUPLICATE_PHONE") {
          const resume = (err.details?.resume_session_id as string | undefined) ?? null;
          if (resume) setResumeSessionId(resume);
          setServerError(err.message);
          return;
        }
        setServerError(err.message);
        return;
      }
      setServerError("Đã có lỗi xảy ra, thử lại sau ít phút nhé anh/chị.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="space-y-4"
      aria-label="Đăng ký ứng tuyển"
    >
      <div>
        <Label htmlFor="full_name" required>
          Họ và tên
        </Label>
        <Input
          id="full_name"
          inputMode="text"
          autoComplete="name"
          autoCapitalize="words"
          placeholder="VD: Nguyễn Văn Tèo"
          aria-invalid={errors.full_name ? "true" : "false"}
          aria-describedby={errors.full_name ? "err-name" : undefined}
          hasError={!!errors.full_name}
          {...register("full_name")}
        />
        <FieldError id="err-name" message={errors.full_name?.message} />
      </div>

      <div>
        <Label htmlFor="phone" required>
          Số điện thoại
        </Label>
        <Input
          id="phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder="0909 123 456"
          aria-invalid={errors.phone ? "true" : "false"}
          aria-describedby={errors.phone ? "err-phone" : undefined}
          hasError={!!errors.phone}
          {...register("phone", { onBlur: onPhoneBlur })}
        />
        <FieldError id="err-phone" message={errors.phone?.message} />
      </div>

      <div>
        <Label htmlFor="area">Khu vực đang ở (không bắt buộc)</Label>
        <Input
          id="area"
          inputMode="text"
          autoCapitalize="sentences"
          placeholder="VD: gần chợ Bà Chiểu, Bình Thạnh"
          hasError={!!errors.area_raw}
          {...register("area_raw")}
        />
        <FieldError message={errors.area_raw?.message} />
      </div>

      <label className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 cursor-pointer">
        <input
          type="checkbox"
          className="mt-1 h-5 w-5 flex-shrink-0 rounded border-slate-300 accent-[var(--color-brand-dark)]"
          aria-describedby="err-consent"
          {...register("consent_accepted")}
        />
        <span className="text-sm leading-snug text-[var(--color-ink)]">
          {CONSENT_TEXT}
        </span>
      </label>
      <FieldError
        id="err-consent"
        message={errors.consent_accepted?.message}
      />

      {serverError && (
        <div
          role="alert"
          aria-live="assertive"
          className="rounded-lg border border-[var(--color-danger)]/30 bg-red-50 p-3 text-sm text-[var(--color-danger)]"
        >
          <p className="font-medium">{serverError}</p>
          {resumeSessionId && (
            <a
              href={`/screening/resume?session_id=${encodeURIComponent(resumeSessionId)}`}
              className="mt-1.5 inline-block font-semibold underline"
            >
              Tiếp tục trò chuyện đã mở →
            </a>
          )}
        </div>
      )}

      {/* Sticky bottom CTA on mobile */}
      <div className="fixed inset-x-0 bottom-0 border-t border-slate-200 bg-white/95 px-4 py-3 backdrop-blur md:static md:border-0 md:bg-transparent md:p-0 md:pt-2">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          disabled={isSubmitting}
          aria-busy={isSubmitting}
        >
          {isSubmitting ? "Đang gửi…" : "ĐĂNG KÝ 30 GIÂY"}
        </Button>
      </div>
    </form>
  );
}
