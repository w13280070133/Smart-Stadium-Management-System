// member-frontend/src/utils/auth.ts

export interface MemberInfo {
  id: number;
  name: string;
  phone: string;
  status?: string;
  level?: string;
}

export const MEMBER_TOKEN_KEY = "member_token";
export const MEMBER_INFO_KEY = "member_info";

export function getMemberToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(MEMBER_TOKEN_KEY);
}

export function setMemberToken(token: string) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(MEMBER_TOKEN_KEY, token);
}

export function clearMemberAuth() {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(MEMBER_TOKEN_KEY);
  localStorage.removeItem(MEMBER_INFO_KEY);
}

export function getMemberInfo(): MemberInfo | null {
  if (typeof localStorage === "undefined") return null;
  const raw = localStorage.getItem(MEMBER_INFO_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as MemberInfo;
  } catch {
    return null;
  }
}

export function setMemberInfo(info: MemberInfo) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(MEMBER_INFO_KEY, JSON.stringify(info));
}
