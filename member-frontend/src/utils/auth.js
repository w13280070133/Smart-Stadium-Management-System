// member-frontend/src/utils/auth.ts
export const MEMBER_TOKEN_KEY = "member_token";
export const MEMBER_INFO_KEY = "member_info";
export function getMemberToken() {
    if (typeof localStorage === "undefined")
        return null;
    return localStorage.getItem(MEMBER_TOKEN_KEY);
}
export function setMemberToken(token) {
    if (typeof localStorage === "undefined")
        return;
    localStorage.setItem(MEMBER_TOKEN_KEY, token);
}
export function clearMemberAuth() {
    if (typeof localStorage === "undefined")
        return;
    localStorage.removeItem(MEMBER_TOKEN_KEY);
    localStorage.removeItem(MEMBER_INFO_KEY);
}
export function getMemberInfo() {
    if (typeof localStorage === "undefined")
        return null;
    const raw = localStorage.getItem(MEMBER_INFO_KEY);
    if (!raw)
        return null;
    try {
        return JSON.parse(raw);
    }
    catch {
        return null;
    }
}
export function setMemberInfo(info) {
    if (typeof localStorage === "undefined")
        return;
    localStorage.setItem(MEMBER_INFO_KEY, JSON.stringify(info));
}
