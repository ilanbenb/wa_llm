import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const file = join(dirname(fileURLToPath(import.meta.url)), "fixtures", "chat.html");
const html = readFileSync(file);

const server = createServer((request, response) => {
  const pathname = (request.url ?? "/").split("?")[0];
  if (pathname !== "/chat.html" && pathname !== "/") {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("not found");
    return;
  }
  response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  response.end(html);
});

server.listen(4179, "127.0.0.1");
