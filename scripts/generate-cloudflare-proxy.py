#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = PROJECT_ROOT / "bank-statements-web" / "functions" / "api" / "[[path]].ts"

TEMPLATE = '''interface Env {
  API_HOST: string
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const apiHost = context.env.API_HOST || '%API_HOST%'
  const url = new URL(context.request.url)
  const apiUrl = `${apiHost}${url.pathname}${url.search}`

  const headers = new Headers(context.request.headers)
  headers.set('Host', new URL(apiHost).host)
  headers.delete('cf-connecting-ip')
  headers.delete('cf-ray')
  headers.delete('cf-visitor')
  headers.delete('cf-ipcountry')

  const init: RequestInit = {
    method: context.request.method,
    headers,
  }

  if (context.request.method !== 'GET' && context.request.method !== 'HEAD') {
    init.body = context.request.body
    init.duplex = 'half'
  }

  const response = await fetch(apiUrl, init)

  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete('content-encoding')
  responseHeaders.delete('content-length')

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}
'''


def main():
    api_host = os.environ.get("API_HOST")
    if not api_host:
        print("Error: API_HOST env var not set")
        sys.exit(1)

    content = TEMPLATE.replace("%API_HOST%", api_host)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)

    print(f"Generated {OUTPUT_FILE} with API_HOST={api_host}")


if __name__ == "__main__":
    main()
