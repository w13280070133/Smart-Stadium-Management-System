export function getAllowedActions(): string[] {
  const raw = localStorage.getItem("allowed_actions");
  try {
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) && arr.length ? arr : ["*"];
  } catch {
    return ["*"];
  }
}

export function hasAction(actionCode: string): boolean {
  const actions = getAllowedActions();
  if (actions.includes("*")) return true;
  return actions.includes(actionCode);
}
