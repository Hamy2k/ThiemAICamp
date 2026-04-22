import { z } from "zod";
import { isLikelyValidVNPhone } from "./phone";

/**
 * Zod schemas for every form. VN error messages.
 * Keep parity with backend contracts in types/api.ts.
 */

export const leadCreateSchema = z.object({
  full_name: z
    .string({ required_error: "Vui lòng nhập họ tên." })
    .trim()
    .min(2, "Họ tên quá ngắn.")
    .max(100, "Họ tên quá dài."),
  phone: z
    .string({ required_error: "Vui lòng nhập số điện thoại." })
    .trim()
    .refine(isLikelyValidVNPhone, "Số điện thoại chưa đúng, anh/chị kiểm tra lại giúp em."),
  area_raw: z
    .string()
    .trim()
    .max(200, "Địa chỉ quá dài.")
    .optional()
    .or(z.literal("")),
  consent_accepted: z
    .boolean()
    .refine((v) => v === true, {
      message: "Vui lòng tích ô đồng ý để tiếp tục.",
    }),
});

export type LeadCreateFormValues = z.infer<typeof leadCreateSchema>;

export const jobCreateSchema = z.object({
  company_name_override: z.string().trim().max(200).optional().or(z.literal("")),
  title: z.string().trim().min(3, "Tiêu đề quá ngắn.").max(200),
  salary_text: z.string().trim().max(100).optional().or(z.literal("")),
  location_raw: z.string().trim().min(1, "Vui lòng nhập địa điểm.").max(500),
  requirements_raw: z.string().trim().max(2000).optional().or(z.literal("")),
  shift: z.enum(["day", "night", "rotating", "flexible"]).optional(),
  start_date: z.string().optional().or(z.literal("")),
  target_hires: z
    .coerce.number({ invalid_type_error: "Số lượng phải là số." })
    .int("Nhập số nguyên.")
    .min(1, "Tối thiểu 1 người.")
    .max(500, "Tối đa 500 người.")
    .default(1),
});

export type JobCreateFormValues = z.infer<typeof jobCreateSchema>;

export const screeningMessageSchema = z.object({
  message: z.string().trim().min(1, "Hãy nhập câu trả lời.").max(1000),
});

export type ScreeningMessageFormValues = z.infer<typeof screeningMessageSchema>;
