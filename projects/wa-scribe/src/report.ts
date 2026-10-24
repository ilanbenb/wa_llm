export function reportExchange(selector: string, message: unknown): void {
  const node = document.querySelector(selector);
  if (!(node instanceof HTMLElement)) {
    throw new Error(`Missing ${selector}`);
  }
  chrome.runtime.sendMessage(message, (reply: unknown) => {
    const failure = chrome.runtime.lastError?.message;
    node.textContent = JSON.stringify(failure === undefined ? reply : { lastError: failure });
  });
}
