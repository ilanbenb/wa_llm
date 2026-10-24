const FIXTURE_ORIGIN = "http://127.0.0.1:4179";

export function isAllowedTestRequest(url: string): boolean {
  if (url.startsWith("chrome-extension://")) return true;
  return url === FIXTURE_ORIGIN || url.startsWith(`${FIXTURE_ORIGIN}/`);
}
