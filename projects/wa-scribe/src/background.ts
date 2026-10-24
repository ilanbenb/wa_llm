import { decide } from "./protocol";

chrome.runtime.onMessage.addListener((message: unknown, sender, sendResponse) => {
  sendResponse(
    decide(
      message,
      {
        extensionId: sender.id ?? "",
        url: sender.url ?? "",
      },
      chrome.runtime.id,
    ),
  );
});
